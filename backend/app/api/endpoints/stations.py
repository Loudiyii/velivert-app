"""Station API endpoints."""

from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories import StationRepository
from app.schemas.station import (
    StationResponse,
    StationStatusResponse,
    StationHistoryPoint,
)
from app.services import GBFSPollerService

router = APIRouter()


@router.get("/current", response_model=List[StationStatusResponse])
async def get_stations_current_status(
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=500),  # Increased to show all stations
    db: AsyncSession = Depends(get_db)
):
    """
    Get current status of all stations.

    Retrieves real-time station data including bike availability,
    dock status, and operational status.
    """
    repo = StationRepository(db)
    stations = await repo.get_all(skip=skip, limit=limit)

    # Get latest status for all stations
    response = []
    for station in stations:
        # Get latest status snapshot
        latest_status = await repo.get_latest_status(station.id)

        if latest_status:
            # Calculate occupancy rate (capped at 1.0)
            occupancy_rate = 0.0
            if station.capacity > 0:
                bikes_available = latest_status.get('num_bikes_available', 0)
                occupancy_rate = min(1.0, bikes_available / station.capacity)

            response.append(
                StationStatusResponse(
                    station_id=station.id,
                    name=station.name,
                    lat=float(station.lat),
                    lon=float(station.lon),
                    capacity=station.capacity,
                    num_bikes_available=latest_status.get('num_bikes_available', 0),
                    num_bikes_disabled=latest_status.get('num_bikes_disabled', 0),
                    num_docks_available=latest_status.get('num_docks_available', 0),
                    num_docks_disabled=latest_status.get('num_docks_disabled', 0),
                    is_installed=latest_status.get('is_installed', True),
                    is_renting=latest_status.get('is_renting', True),
                    is_returning=latest_status.get('is_returning', True),
                    last_reported=latest_status.get('last_reported', datetime.utcnow()),
                    occupancy_rate=occupancy_rate
                )
            )
        else:
            # No status available, return defaults
            response.append(
                StationStatusResponse(
                    station_id=station.id,
                    name=station.name,
                    lat=float(station.lat),
                    lon=float(station.lon),
                    capacity=station.capacity,
                    num_bikes_available=0,
                    num_bikes_disabled=0,
                    num_docks_available=station.capacity,
                    num_docks_disabled=0,
                    is_installed=True,
                    is_renting=True,
                    is_returning=True,
                    last_reported=datetime.utcnow(),
                    occupancy_rate=0.0
                )
            )

    return response


@router.get("/{station_id}", response_model=StationResponse)
async def get_station_by_id(
    station_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get station by ID.

    Returns detailed information about a specific station.
    """
    repo = StationRepository(db)
    station = await repo.get_by_id(station_id)

    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    return station


@router.get("/{station_id}/history", response_model=List[StationHistoryPoint])
async def get_station_history(
    station_id: str,
    start_time: datetime = Query(
        default=None,
        description="Start time (default: 24h ago)"
    ),
    end_time: datetime = Query(
        default=None,
        description="End time (default: now)"
    ),
    interval: str = Query(
        default="1 hour",
        description="Time bucket interval (e.g., '15 minutes', '1 hour')"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical occupancy data for a station.

    Returns time-bucketed aggregated statistics including average,
    minimum, and maximum bike availability.
    """
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=24)

    repo = StationRepository(db)

    # Check if station exists
    station = await repo.get_by_id(station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    # Get history
    history = await repo.get_status_history(
        station_id=station_id,
        start_time=start_time,
        end_time=end_time,
        interval=interval
    )

    return [
        StationHistoryPoint(
            time=row["bucket"],
            avg_bikes_available=float(row["avg_bikes_available"]),
            min_bikes_available=int(row["min_bikes_available"]),
            max_bikes_available=int(row["max_bikes_available"])
        )
        for row in history
    ]