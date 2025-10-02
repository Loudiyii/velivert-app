"""Repository for MaintenanceIntervention data access."""

from typing import List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models import MaintenanceIntervention
from app.schemas.intervention import InterventionCreate, InterventionUpdate

logger = structlog.get_logger()


class InterventionRepository:
    """
    Repository handling all database operations for maintenance interventions.

    Encapsulates:
    - CRUD operations
    - Status updates
    - Filtering and queries
    """

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db

    async def get_by_id(self, intervention_id: UUID) -> Optional[MaintenanceIntervention]:
        """
        Get intervention by ID.

        Args:
            intervention_id: Intervention UUID

        Returns:
            MaintenanceIntervention object or None if not found
        """
        result = await self.db.execute(
            select(MaintenanceIntervention).where(
                MaintenanceIntervention.id == intervention_id
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        technician_id: Optional[UUID] = None
    ) -> List[MaintenanceIntervention]:
        """
        Get interventions with filtering and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by status
            priority: Filter by priority
            technician_id: Filter by technician

        Returns:
            List of MaintenanceIntervention objects
        """
        query = select(MaintenanceIntervention)

        if status:
            query = query.where(MaintenanceIntervention.status == status)
        if priority:
            query = query.where(MaintenanceIntervention.priority == priority)
        if technician_id:
            query = query.where(MaintenanceIntervention.technician_id == technician_id)

        query = query.offset(skip).limit(limit).order_by(
            MaintenanceIntervention.created_at.desc()
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        intervention_data: InterventionCreate
    ) -> MaintenanceIntervention:
        """
        Create a new intervention.

        Args:
            intervention_data: Intervention creation data

        Returns:
            Created MaintenanceIntervention object
        """
        intervention = MaintenanceIntervention(
            **intervention_data.model_dump(exclude_unset=True),
            status="pending"
        )

        self.db.add(intervention)
        await self.db.flush()
        await self.db.refresh(intervention)

        logger.info(
            "intervention_created",
            intervention_id=str(intervention.id),
            type=intervention.intervention_type,
            priority=intervention.priority
        )

        return intervention

    async def update(
        self,
        intervention_id: UUID,
        intervention_data: InterventionUpdate
    ) -> Optional[MaintenanceIntervention]:
        """
        Update an intervention.

        Args:
            intervention_id: Intervention UUID
            intervention_data: Update data

        Returns:
            Updated MaintenanceIntervention object or None if not found
        """
        intervention = await self.get_by_id(intervention_id)
        if not intervention:
            return None

        for key, value in intervention_data.model_dump(exclude_unset=True).items():
            setattr(intervention, key, value)

        intervention.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(intervention)

        logger.info(
            "intervention_updated",
            intervention_id=str(intervention_id),
            status=intervention.status
        )

        return intervention

    async def get_pending_interventions(
        self,
        priority: Optional[str] = None
    ) -> List[MaintenanceIntervention]:
        """
        Get all pending interventions.

        Args:
            priority: Optional priority filter

        Returns:
            List of pending interventions
        """
        query = select(MaintenanceIntervention).where(
            MaintenanceIntervention.status == "pending"
        )

        if priority:
            query = query.where(MaintenanceIntervention.priority == priority)

        query = query.order_by(
            MaintenanceIntervention.priority.desc(),
            MaintenanceIntervention.created_at.asc()
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())