"""Analytics service for computing metrics and insights."""

import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Station, StationStatusSnapshot, Bike

logger = structlog.get_logger()


class AnalyticsService:
    """
    Service for analytics computations.

    Responsibilities:
    - Calculate occupancy metrics
    - Identify idle bikes
    - Generate heatmaps
    - Compute demand forecasts
    """

    def __init__(self, db: AsyncSession):
        """Initialize analytics service."""
        self.db = db

    async def calculate_occupancy_rate(
        self,
        station_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> float:
        """
        Calculate average occupancy rate for a station.

        Args:
            station_id: Station identifier
            start_time: Start of time range (default: 24h ago)
            end_time: End of time range (default: now)

        Returns:
            float: Average occupancy rate (0.0 to 1.0)
        """
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)

        # Get station capacity
        station_result = await self.db.execute(
            select(Station.capacity).where(Station.id == station_id)
        )
        station = station_result.scalar_one_or_none()

        if not station:
            logger.warning("station_not_found", station_id=station_id)
            return 0.0

        capacity = station

        # Calculate average bikes available
        query = select(func.avg(StationStatusSnapshot.num_bikes_available)).where(
            StationStatusSnapshot.station_id == station_id,
            StationStatusSnapshot.time >= start_time,
            StationStatusSnapshot.time <= end_time
        )

        result = await self.db.execute(query)
        avg_bikes = result.scalar_one_or_none()

        if avg_bikes is None or capacity == 0:
            return 0.0

        occupancy_rate = float(avg_bikes) / float(capacity)
        return min(max(occupancy_rate, 0.0), 1.0)

    async def identify_idle_bikes(
        self,
        threshold_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Identify bikes that haven't moved in a specified time period.

        Args:
            threshold_hours: Hours without movement to consider idle

        Returns:
            List of idle bike records with details
        """
        threshold_time = datetime.utcnow() - timedelta(hours=threshold_hours)

        query = select(Bike).where(
            Bike.last_reported < threshold_time,
            Bike.is_disabled == False
        )

        result = await self.db.execute(query)
        idle_bikes = result.scalars().all()

        idle_list = []
        for bike in idle_bikes:
            idle_list.append({
                "bike_id": bike.bike_id,
                "lat": float(bike.lat) if bike.lat else None,
                "lon": float(bike.lon) if bike.lon else None,
                "last_reported": bike.last_reported,
                "hours_idle": (datetime.utcnow() - bike.last_reported).total_seconds() / 3600
                    if bike.last_reported else None,
                "current_station_id": bike.current_station_id
            })

        logger.info(
            "idle_bikes_identified",
            count=len(idle_list),
            threshold_hours=threshold_hours
        )

        return idle_list

    async def get_station_occupancy_heatmap(
        self,
        time_of_day: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate occupancy heatmap data for all stations.

        Args:
            time_of_day: Hour of day (0-23) to filter by, None for current

        Returns:
            List of stations with occupancy data
        """
        # This would typically involve time-bucketed queries
        # Simplified version for structure

        query = select(Station)
        result = await self.db.execute(query)
        stations = result.scalars().all()

        heatmap_data = []
        for station in stations:
            occupancy = await self.calculate_occupancy_rate(station.id)
            heatmap_data.append({
                "station_id": station.id,
                "name": station.name,
                "lat": float(station.lat),
                "lon": float(station.lon),
                "occupancy_rate": occupancy,
                "capacity": station.capacity
            })

        return heatmap_data

    async def get_average_occupancy_rate(
        self,
        hours: int = 24
    ) -> float:
        """
        Calculate average occupancy rate across all stations (optimized).

        Args:
            hours: Time window in hours

        Returns:
            float: Average occupancy rate (0.0 to 1.0)
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # Optimized: Calculate global average in one query
        # Get average bikes across all snapshots and divide by total capacity
        avg_bikes_query = select(
            func.avg(StationStatusSnapshot.num_bikes_available)
        ).where(
            StationStatusSnapshot.time >= start_time,
            StationStatusSnapshot.time <= end_time
        )

        avg_bikes_result = await self.db.execute(avg_bikes_query)
        avg_bikes = avg_bikes_result.scalar() or 0.0

        # Get total capacity
        capacity_query = select(func.sum(Station.capacity))
        capacity_result = await self.db.execute(capacity_query)
        total_capacity = capacity_result.scalar() or 1

        avg_occupancy = (avg_bikes / total_capacity) if total_capacity > 0 else 0.0

        logger.info(
            "average_occupancy_calculated",
            avg_occupancy=avg_occupancy,
            avg_bikes=avg_bikes,
            total_capacity=total_capacity,
            hours=hours
        )
        return round(avg_occupancy, 3)

    async def calculate_daily_rotations(
        self,
        hours: int = 24
    ) -> float:
        """
        Calculate average daily bike rotations (trips per bike per day).

        Args:
            hours: Time window in hours

        Returns:
            float: Average rotations per bike per day
        """
        from app.models import BikeMovement

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # Count total movements (pickups + dropoffs)
        movements_query = select(func.count(BikeMovement.id)).where(
            BikeMovement.detected_at >= start_time,
            BikeMovement.detected_at <= end_time,
            BikeMovement.movement_type.in_(['pickup', 'dropoff'])
        )
        movements_result = await self.db.execute(movements_query)
        total_movements = movements_result.scalar() or 0

        # Count unique bikes
        bikes_query = select(func.count(Bike.bike_id)).where(
            Bike.is_disabled == False
        )
        bikes_result = await self.db.execute(bikes_query)
        total_bikes = bikes_result.scalar() or 1

        # Calculate rotations per bike per day
        days = hours / 24.0
        if days == 0 or total_bikes == 0:
            return 0.0

        # Each rotation = 1 pickup + 1 dropoff = 2 movements
        rotations_per_day = (total_movements / 2.0) / total_bikes / days

        logger.info(
            "daily_rotations_calculated",
            rotations_per_day=rotations_per_day,
            total_movements=total_movements,
            total_bikes=total_bikes,
            hours=hours
        )

        return round(rotations_per_day, 2)

    async def get_occupancy_timeseries(
        self,
        hours: int = 24,
        interval_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Get occupancy time series data for charting.

        Args:
            hours: Time window in hours
            interval_minutes: Data point interval in minutes

        Returns:
            List of time series data points
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # Generate time buckets
        time_series = []
        current_time = start_time
        interval_delta = timedelta(minutes=interval_minutes)

        while current_time <= end_time:
            bucket_start = current_time
            bucket_end = current_time + interval_delta

            # Calculate average bikes available across all stations for this bucket
            query = select(
                func.avg(StationStatusSnapshot.num_bikes_available)
            ).where(
                StationStatusSnapshot.time >= bucket_start,
                StationStatusSnapshot.time < bucket_end
            )

            result = await self.db.execute(query)
            avg_bikes = result.scalar() or 0

            # Get total capacity (approximate - using current capacity)
            capacity_query = select(func.sum(Station.capacity))
            capacity_result = await self.db.execute(capacity_query)
            total_capacity = capacity_result.scalar() or 1

            occupancy_rate = (avg_bikes / total_capacity) if total_capacity > 0 else 0.0

            time_series.append({
                "timestamp": current_time.isoformat(),
                "occupancy_rate": round(occupancy_rate, 3),
                "average_bikes_available": round(avg_bikes, 1)
            })

            current_time += interval_delta

        logger.info(
            "occupancy_timeseries_generated",
            data_points=len(time_series),
            hours=hours,
            interval_minutes=interval_minutes
        )

        return time_series