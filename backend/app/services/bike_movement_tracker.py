"""Service for tracking bike movements and creating snapshots."""

from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from math import radians, cos, sin, asin, sqrt

from app.models.bike import Bike
from app.models.bike_movement import BikeMovement, BikeSnapshot


class BikeMovementTracker:
    """Tracks bike movements by comparing current positions with previous snapshots."""

    # Threshold for considering a bike has moved (in meters)
    MOVEMENT_THRESHOLD = 10.0

    def __init__(self, db: AsyncSession):
        self.db = db
        self._previous_positions: Dict[str, Dict] = {}

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth (in meters).
        Uses the Haversine formula.
        """
        # Convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        # Radius of Earth in meters
        r = 6371000

        return c * r

    @staticmethod
    def determine_movement_type(
        bike: Bike,
        prev_station_id: Optional[str],
        curr_station_id: Optional[str]
    ) -> str:
        """
        Determine the type of movement based on station changes.

        Returns:
            - "pickup": Bike left a station
            - "dropoff": Bike arrived at a station
            - "relocation": Bike moved between stations (maintenance)
            - "in_transit": Bike moved but not at a station
        """
        if prev_station_id and not curr_station_id:
            return "pickup"
        elif not prev_station_id and curr_station_id:
            return "dropoff"
        elif prev_station_id and curr_station_id and prev_station_id != curr_station_id:
            return "relocation"
        else:
            return "in_transit"

    async def load_previous_positions(self):
        """Load the last known positions of all bikes into memory."""
        result = await self.db.execute(select(Bike))
        bikes = result.scalars().all()

        for bike in bikes:
            if bike.lat and bike.lon:
                self._previous_positions[bike.bike_id] = {
                    'lat': float(bike.lat),
                    'lon': float(bike.lon),
                    'station_id': bike.current_station_id,
                    'is_reserved': bike.is_reserved,
                    'is_disabled': bike.is_disabled,
                    'range_meters': bike.current_range_meters,
                }

    async def detect_and_record_movements(self, current_bikes: List[Bike]) -> int:
        """
        Compare current bike positions with previous positions and record movements.
        Uses database snapshots to detect movements even after restarts.

        Args:
            current_bikes: List of bikes with current positions

        Returns:
            Number of movements detected and recorded
        """
        from app.models import BikeSnapshot
        from sqlalchemy import select, desc, func

        movements_recorded = 0

        # Load all latest snapshots in one query (optimized)
        if not self._previous_positions:
            # Get the latest snapshot for each bike in a single query
            subquery = select(
                BikeSnapshot.bike_id,
                func.max(BikeSnapshot.time).label('max_time')
            ).group_by(BikeSnapshot.bike_id).subquery()

            query = select(BikeSnapshot).join(
                subquery,
                (BikeSnapshot.bike_id == subquery.c.bike_id) &
                (BikeSnapshot.time == subquery.c.max_time)
            )

            result = await self.db.execute(query)
            latest_snapshots = result.scalars().all()

            for snapshot in latest_snapshots:
                self._previous_positions[snapshot.bike_id] = {
                    'lat': float(snapshot.lat),
                    'lon': float(snapshot.lon),
                    'station_id': snapshot.station_id,
                    'is_reserved': snapshot.is_reserved,
                    'is_disabled': snapshot.is_disabled,
                    'range_meters': snapshot.current_range_meters,
                }

            logger.info("previous_positions_loaded", count=len(self._previous_positions))

        for bike in current_bikes:
            if not bike.lat or not bike.lon:
                continue

            curr_lat = float(bike.lat)
            curr_lon = float(bike.lon)
            bike_id = bike.bike_id

            # Check if we have previous position
            if bike_id not in self._previous_positions:
                # No previous data, store current position and skip
                self._previous_positions[bike_id] = {
                    'lat': curr_lat,
                    'lon': curr_lon,
                    'station_id': bike.current_station_id,
                    'is_reserved': bike.is_reserved,
                    'is_disabled': bike.is_disabled,
                    'range_meters': bike.current_range_meters,
                }
                continue

            prev = self._previous_positions[bike_id]

            prev_lat = prev['lat']
            prev_lon = prev['lon']
            prev_station_id = prev['station_id']

            # Calculate distance moved
            distance = self.calculate_distance(prev_lat, prev_lon, curr_lat, curr_lon)

            # Only record if bike moved more than threshold OR station changed
            if distance > self.MOVEMENT_THRESHOLD or prev_station_id != bike.current_station_id:
                movement_type = self.determine_movement_type(
                    bike,
                    prev_station_id,
                    bike.current_station_id
                )

                logger.info(
                    "movement_detected",
                    bike_id=bike_id,
                    distance_meters=distance,
                    movement_type=movement_type,
                    from_station=prev_station_id,
                    to_station=bike.current_station_id
                )

                # Create movement record
                movement = BikeMovement(
                    bike_id=bike_id,
                    from_station_id=prev_station_id,
                    from_lat=prev_lat,
                    from_lon=prev_lon,
                    to_station_id=bike.current_station_id,
                    to_lat=curr_lat,
                    to_lon=curr_lon,
                    movement_type=movement_type,
                    distance_meters=distance,
                    is_reserved=bike.is_reserved,
                    is_disabled=bike.is_disabled,
                    battery_range_meters=bike.current_range_meters,
                    detected_at=datetime.utcnow()
                )

                self.db.add(movement)
                movements_recorded += 1

            # Update stored position
            self._previous_positions[bike_id] = {
                'lat': curr_lat,
                'lon': curr_lon,
                'station_id': bike.current_station_id,
                'is_reserved': bike.is_reserved,
                'is_disabled': bike.is_disabled,
                'range_meters': bike.current_range_meters,
            }

        if movements_recorded > 0:
            await self.db.commit()
            logger.info("movements_recorded", count=movements_recorded)

        return movements_recorded

    async def create_snapshots(self, bikes: List[Bike], snapshot_time: Optional[datetime] = None) -> int:
        """
        Create snapshots of all bikes at a specific point in time.

        Args:
            bikes: List of all bikes to snapshot
            snapshot_time: Time of snapshot (defaults to now)

        Returns:
            Number of snapshots created
        """
        if snapshot_time is None:
            snapshot_time = datetime.utcnow()

        snapshots_created = 0

        for bike in bikes:
            if not bike.lat or not bike.lon:
                continue

            snapshot = BikeSnapshot(
                time=snapshot_time,
                bike_id=bike.bike_id,
                station_id=bike.current_station_id,
                lat=float(bike.lat),
                lon=float(bike.lon),
                is_reserved=bike.is_reserved,
                is_disabled=bike.is_disabled,
                current_range_meters=bike.current_range_meters,
                vehicle_type_id=bike.vehicle_type_id
            )

            self.db.add(snapshot)
            snapshots_created += 1

        if snapshots_created > 0:
            await self.db.commit()

        return snapshots_created

    async def track_movements_and_snapshot(self, bikes: List[Bike]) -> Dict[str, int]:
        """
        Main entry point: detect movements and create snapshots.

        Args:
            bikes: List of current bikes from GBFS

        Returns:
            Dict with 'movements' and 'snapshots' counts
        """
        # First time initialization
        if not self._previous_positions:
            await self.load_previous_positions()

        # Detect and record movements
        movements = await self.detect_and_record_movements(bikes)

        # Create snapshots (every call, for time-series analysis)
        snapshots = await self.create_snapshots(bikes)

        return {
            'movements_detected': movements,
            'snapshots_created': snapshots
        }
