"""Repository for Bike data access."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models import Bike

logger = structlog.get_logger()


class BikeRepository:
    """
    Repository handling all database operations for bikes.

    Encapsulates:
    - CRUD operations for bikes
    - Location updates
    - Status queries
    """

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db

    async def get_by_id(self, bike_id: str) -> Optional[Bike]:
        """
        Get bike by ID.

        Args:
            bike_id: Bike identifier

        Returns:
            Bike object or None if not found
        """
        result = await self.db.execute(
            select(Bike).where(Bike.bike_id == bike_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_disabled: bool = True
    ) -> List[Bike]:
        """
        Get all bikes with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_disabled: Whether to include disabled bikes

        Returns:
            List of Bike objects
        """
        query = select(Bike)

        if not include_disabled:
            query = query.where(Bike.is_disabled == False)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def upsert(self, bike_data: dict) -> Bike:
        """
        Create or update a bike (idempotent).

        Args:
            bike_data: Bike data dictionary

        Returns:
            Bike object
        """
        bike_id = bike_data.get("bike_id")
        existing = await self.get_by_id(bike_id)

        if existing:
            # Update existing
            for key, value in bike_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            existing.last_reported = datetime.utcnow()
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        else:
            # Create new
            bike = Bike(
                **bike_data,
                last_reported=datetime.utcnow()
            )
            self.db.add(bike)
            await self.db.flush()
            await self.db.refresh(bike)

            logger.info("bike_created", bike_id=bike.bike_id)

            return bike

    async def update_location(
        self,
        bike_id: str,
        lat: float,
        lon: float,
        station_id: Optional[str] = None
    ) -> Optional[Bike]:
        """
        Update bike location.

        Args:
            bike_id: Bike identifier
            lat: Latitude
            lon: Longitude
            station_id: Optional station ID if docked

        Returns:
            Updated Bike object or None if not found
        """
        bike = await self.get_by_id(bike_id)
        if not bike:
            return None

        bike.lat = lat
        bike.lon = lon
        bike.current_station_id = station_id
        bike.last_reported = datetime.utcnow()
        bike.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(bike)

        return bike

    async def get_disabled_bikes(self) -> List[Bike]:
        """
        Get all disabled bikes.

        Returns:
            List of disabled Bike objects
        """
        result = await self.db.execute(
            select(Bike).where(Bike.is_disabled == True)
        )
        return list(result.scalars().all())

    async def get_bikes_by_station(self, station_id: str) -> List[Bike]:
        """
        Get all bikes at a specific station.

        Args:
            station_id: Station identifier

        Returns:
            List of Bike objects at the station
        """
        result = await self.db.execute(
            select(Bike).where(Bike.current_station_id == station_id)
        )
        return list(result.scalars().all())