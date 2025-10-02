"""Maintenance intervention API endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories import InterventionRepository
from app.schemas.intervention import (
    InterventionCreate,
    InterventionUpdate,
    InterventionResponse,
)

router = APIRouter()


@router.get("/", response_model=List[InterventionResponse])
async def list_interventions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None, regex="^(pending|in_progress|completed|cancelled)$"),
    priority: Optional[str] = Query(None, regex="^(low|medium|high|urgent)$"),
    technician_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List maintenance interventions with filtering.

    Supports filtering by status, priority, and technician.
    """
    repo = InterventionRepository(db)
    interventions = await repo.get_all(
        skip=skip,
        limit=limit,
        status=status,
        priority=priority,
        technician_id=technician_id
    )

    return interventions


@router.get("/pending", response_model=List[InterventionResponse])
async def list_pending_interventions(
    priority: Optional[str] = Query(None, regex="^(low|medium|high|urgent)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all pending interventions.

    Returns interventions that have not yet been started,
    ordered by priority and creation time.
    """
    repo = InterventionRepository(db)
    interventions = await repo.get_pending_interventions(priority=priority)

    return interventions


@router.get("/{intervention_id}", response_model=InterventionResponse)
async def get_intervention(
    intervention_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get intervention by ID.

    Returns detailed information about a specific intervention.
    """
    repo = InterventionRepository(db)
    intervention = await repo.get_by_id(intervention_id)

    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    return intervention


@router.post("/", response_model=InterventionResponse, status_code=201)
async def create_intervention(
    intervention_data: InterventionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new maintenance intervention.

    Either bike_id or station_id must be provided.
    """
    repo = InterventionRepository(db)
    intervention = await repo.create(intervention_data)

    return intervention


@router.patch("/{intervention_id}", response_model=InterventionResponse)
async def update_intervention(
    intervention_id: UUID,
    intervention_data: InterventionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing intervention.

    Can update status, priority, scheduled time, and notes.
    """
    repo = InterventionRepository(db)
    intervention = await repo.update(intervention_id, intervention_data)

    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    return intervention