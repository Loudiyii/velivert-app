"""Route optimization API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories import InterventionRepository
from app.services import RouteOptimizerService
from app.schemas.route import RouteOptimizationRequest, RouteResponse

router = APIRouter()


@router.post("/optimize", response_model=dict)
async def optimize_route(
    request: RouteOptimizationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Optimize a route for a technician.

    Takes a list of intervention IDs and generates an optimal route
    considering priorities, distances, and time constraints.
    """
    repo = InterventionRepository(db)

    # Fetch all interventions
    interventions_data = []
    for intervention_id in request.intervention_ids:
        intervention = await repo.get_by_id(intervention_id)
        if not intervention:
            raise HTTPException(
                status_code=404,
                detail=f"Intervention {intervention_id} not found"
            )

        # Extract location data
        # In production, this would get actual lat/lon from bike/station
        interventions_data.append({
            "id": intervention.id,
            "bike_id": intervention.bike_id,
            "station_id": intervention.station_id,
            "priority": intervention.priority,
            "lat": 45.44,  # Placeholder - would fetch from bike/station
            "lon": 4.39,   # Placeholder - would fetch from bike/station
        })

    # Default start location if not provided
    start_location = (
        request.start_location["lat"],
        request.start_location["lon"]
    ) if request.start_location else (45.44, 4.39)

    # Optimize route
    optimizer = RouteOptimizerService()
    optimized_route = optimizer.optimize_route(
        interventions=interventions_data,
        start_location=start_location,
        max_working_hours=request.max_working_hours,
        prioritize_urgent=request.prioritize_urgent
    )

    return {
        "technician_id": str(request.technician_id),
        "date": request.date.isoformat(),
        **optimized_route
    }