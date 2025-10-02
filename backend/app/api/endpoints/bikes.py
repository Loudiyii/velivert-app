"""Bike API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories import BikeRepository
from app.schemas.bike import BikeResponse

router = APIRouter()


@router.get("/current", response_model=List[BikeResponse])
async def get_bikes_current_status(
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=1000),  # Increased to show all bikes
    include_disabled: bool = Query(True, description="Include disabled bikes"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current status of all bikes.

    Retrieves real-time bike data including location, availability,
    and operational status.
    """
    repo = BikeRepository(db)
    bikes = await repo.get_all(
        skip=skip,
        limit=limit,
        include_disabled=include_disabled
    )

    return bikes


@router.get("/{bike_id}", response_model=BikeResponse)
async def get_bike_by_id(
    bike_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get bike by ID.

    Returns detailed information about a specific bike.
    """
    repo = BikeRepository(db)
    bike = await repo.get_by_id(bike_id)

    if not bike:
        raise HTTPException(status_code=404, detail="Bike not found")

    return bike


@router.get("/disabled/list", response_model=List[BikeResponse])
async def get_disabled_bikes(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all disabled bikes.

    Returns list of bikes that are currently disabled and may need
    maintenance or repair.
    """
    repo = BikeRepository(db)
    disabled_bikes = await repo.get_disabled_bikes()

    return disabled_bikes


@router.get("/station/{station_id}/bikes", response_model=List[BikeResponse])
async def get_bikes_at_station(
    station_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all bikes at a specific station.

    Returns list of bikes currently docked at the specified station.
    """
    repo = BikeRepository(db)
    bikes = await repo.get_bikes_by_station(station_id)

    return bikes