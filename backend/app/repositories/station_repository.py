"""Repository for Station data access."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, update, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models import Station, StationStatusSnapshot
from app.schemas.station import StationCreate, StationUpdate

logger = structlog.get_logger()


class StationRepository:
    """
    Repository handling all database operations for stations.

    Encapsulates:
    - CRUD operations for stations
    - Status snapshot storage
    - Historical queries
    """

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db

    async def get_by_id(self, station_id: str) -> Optional[Station]:
        """
        Get station by ID.

        Args:
            station_id: Station identifier

        Returns:
            Station object or None if not found
        """
        result = await self.db.execute(
            select(Station).where(Station.id == station_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Station]:
        """
        Get all stations with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Station objects
        """
        result = await self.db.execute(
            select(Station).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, station_data: StationCreate) -> Station:
        """
        Create a new station.

        Args:
            station_data: Station creation data

        Returns:
            Created Station object
        """
        station = Station(**station_data.model_dump())

        self.db.add(station)
        await self.db.flush()
        await self.db.refresh(station)

        logger.info("station_created", station_id=station.id, name=station.name)

        return station

    async def upsert(self, station_data: StationCreate) -> Station:
        """
        Create or update a station (idempotent).

        Args:
            station_data: Station data

        Returns:
            Station object
        """
        existing = await self.get_by_id(station_data.id)

        if existing:
            # Update existing
            for key, value in station_data.model_dump(exclude_unset=True).items():
                setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        else:
            # Create new
            return await self.create(station_data)

    async def update(
        self,
        station_id: str,
        station_data: StationUpdate
    ) -> Optional[Station]:
        """
        Update station information.

        Args:
            station_id: Station identifier
            station_data: Updated data

        Returns:
            Updated Station object or None if not found
        """
        station = await self.get_by_id(station_id)
        if not station:
            return None

        for key, value in station_data.model_dump(exclude_unset=True).items():
            setattr(station, key, value)

        station.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(station)

        logger.info("station_updated", station_id=station_id)

        return station

    async def store_status_snapshot(
        self,
        station_id: str,
        timestamp: datetime,
        status_data: dict
    ) -> None:
        """
        Store a status snapshot (idempotent via ON CONFLICT).

        Args:
            station_id: Station identifier
            timestamp: Snapshot timestamp
            status_data: Status information
        """
        # Use INSERT ... ON CONFLICT DO NOTHING for idempotence
        stmt = insert(StationStatusSnapshot).values(
            time=timestamp,
            station_id=station_id,
            num_bikes_available=status_data.get("num_bikes_available", 0),
            num_bikes_disabled=status_data.get("num_bikes_disabled", 0),
            num_docks_available=status_data.get("num_docks_available", 0),
            num_docks_disabled=status_data.get("num_docks_disabled", 0),
            is_installed=status_data.get("is_installed", True),
            is_renting=status_data.get("is_renting", True),
            is_returning=status_data.get("is_returning", True),
            last_reported=status_data.get("last_reported")
        )

        # PostgreSQL specific ON CONFLICT
        stmt = stmt.on_conflict_do_nothing(index_elements=["time", "station_id"])

        await self.db.execute(stmt)

    async def get_latest_status(self, station_id: str) -> Optional[dict]:
        """
        Get the latest status snapshot for a station.

        Args:
            station_id: Station identifier

        Returns:
            Dictionary with latest status data or None if not found
        """
        result = await self.db.execute(
            select(StationStatusSnapshot)
            .where(StationStatusSnapshot.station_id == station_id)
            .order_by(StationStatusSnapshot.time.desc())
            .limit(1)
        )
        snapshot = result.scalar_one_or_none()

        if not snapshot:
            return None

        return {
            'num_bikes_available': snapshot.num_bikes_available,
            'num_bikes_disabled': snapshot.num_bikes_disabled,
            'num_docks_available': snapshot.num_docks_available,
            'num_docks_disabled': snapshot.num_docks_disabled,
            'is_installed': snapshot.is_installed,
            'is_renting': snapshot.is_renting,
            'is_returning': snapshot.is_returning,
            'last_reported': snapshot.last_reported
        }

    async def get_status_history(
        self,
        station_id: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "1 hour"
    ) -> List[dict]:
        """
        Get aggregated status history for a station.

        Args:
            station_id: Station identifier
            start_time: Start of time range
            end_time: End of time range
            interval: Time bucket interval (TimescaleDB format)

        Returns:
            List of aggregated snapshots
        """
        query = text("""
            SELECT
                time_bucket(:interval, time) AS bucket,
                AVG(num_bikes_available) AS avg_bikes_available,
                MIN(num_bikes_available) AS min_bikes_available,
                MAX(num_bikes_available) AS max_bikes_available
            FROM station_status_snapshots
            WHERE station_id = :station_id
              AND time >= :start_time
              AND time <= :end_time
            GROUP BY bucket
            ORDER BY bucket
        """)

        result = await self.db.execute(
            query,
            {
                "interval": interval,
                "station_id": station_id,
                "start_time": start_time,
                "end_time": end_time
            }
        )

        return [dict(row._mapping) for row in result]