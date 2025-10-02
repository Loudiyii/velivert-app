"""Analytics API endpoints."""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import AnalyticsService

router = APIRouter()


@router.get("/stations/occupancy-heatmap")
async def get_occupancy_heatmap(
    time_of_day: int = Query(
        None,
        ge=0,
        le=23,
        description="Hour of day (0-23) to filter by"
    ),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get station occupancy heatmap data.

    Returns occupancy rates for all stations, optionally filtered
    by time of day for pattern analysis.
    """
    service = AnalyticsService(db)
    heatmap = await service.get_station_occupancy_heatmap(time_of_day=time_of_day)

    return heatmap


@router.get("/bikes/idle-detection")
async def detect_idle_bikes(
    threshold_hours: int = Query(
        24,
        ge=1,
        le=168,
        description="Hours without movement to consider idle"
    ),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Detect bikes that haven't moved recently.

    Returns bikes that may need relocation or maintenance
    based on inactivity period.
    """
    service = AnalyticsService(db)
    idle_bikes = await service.identify_idle_bikes(threshold_hours=threshold_hours)

    return idle_bikes


@router.get("/stations/{station_id}/occupancy-rate")
async def get_station_occupancy_rate(
    station_id: str,
    start_time: datetime = Query(
        None,
        description="Start time (default: 24h ago)"
    ),
    end_time: datetime = Query(
        None,
        description="End time (default: now)"
    ),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Calculate occupancy rate for a specific station.

    Returns average occupancy rate over the specified time period.
    """
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=24)

    service = AnalyticsService(db)
    occupancy_rate = await service.calculate_occupancy_rate(
        station_id=station_id,
        start_time=start_time,
        end_time=end_time
    )

    return {
        "station_id": station_id,
        "occupancy_rate": occupancy_rate,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }


@router.get("/overview")
async def get_analytics_overview(
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get overall analytics overview.

    Returns:
        - Average occupancy rate across all stations
        - Idle bikes count
        - Daily bike rotation rate
        - Time series data for occupancy chart
    """
    service = AnalyticsService(db)

    # Calculate average occupancy across all stations
    avg_occupancy = await service.get_average_occupancy_rate(hours=hours)

    # Get idle bikes
    idle_bikes = await service.identify_idle_bikes(threshold_hours=hours)

    # Calculate daily rotations (movements per bike)
    daily_rotations = await service.calculate_daily_rotations(hours=hours)

    # Get time series data for chart
    occupancy_timeseries = await service.get_occupancy_timeseries(hours=hours)

    return {
        "period_hours": hours,
        "average_occupancy_rate": avg_occupancy,
        "idle_bikes_count": len(idle_bikes),
        "daily_bike_rotations": daily_rotations,
        "occupancy_timeseries": occupancy_timeseries
    }