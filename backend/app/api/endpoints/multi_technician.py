"""API endpoints for multi-technician route optimization."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.models import Bike
from app.services.multi_technician_optimizer import MultiTechnicianOptimizer
from pydantic import BaseModel

router = APIRouter()


class TechnicianAssignmentRequest(BaseModel):
    num_technicians: int
    technician_names: Optional[List[str]] = None
    route_type: str = "disabled_bikes"  # disabled_bikes, low_battery, pending_interventions


@router.post("/assign-technicians")
async def assign_technicians_to_routes(
    request: TechnicianAssignmentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Répartit intelligemment les interventions entre plusieurs techniciens.

    Utilise K-means clustering pour grouper les vélos par proximité géographique,
    puis calcule le trajet optimal pour chaque technicien.

    Args:
        num_technicians: Nombre de techniciens disponibles
        technician_names: Liste des noms (optionnel)
        route_type: Type de mission (disabled_bikes, low_battery, etc.)
    """

    # Récupérer les interventions selon le type
    interventions = []

    if request.route_type == "disabled_bikes":
        result = await db.execute(select(Bike).where(Bike.is_disabled == True))
        bikes = result.scalars().all()

        # Prioriser selon la batterie : batterie critique = urgent, sinon medium
        interventions = [
            {
                "id": bike.bike_id,
                "lat": float(bike.lat),
                "lon": float(bike.lon),
                "priority": "urgent" if (bike.current_range_meters and bike.current_range_meters < 1000) else "medium",
                "station_id": bike.current_station_id,
                "bike_id": bike.bike_id
            }
            for bike in bikes
        ]

    elif request.route_type == "low_battery":
        result = await db.execute(
            select(Bike).where(
                and_(
                    Bike.is_disabled == False,
                    Bike.current_range_meters < 5000,
                    Bike.current_range_meters > 0
                )
            )
        )
        bikes = result.scalars().all()
        interventions = [
            {
                "id": bike.bike_id,
                "lat": float(bike.lat),
                "lon": float(bike.lon),
                "priority": "high" if bike.current_range_meters < 1000 else "medium",
                "station_id": bike.current_station_id,
                "bike_id": bike.bike_id,
                "range_meters": bike.current_range_meters
            }
            for bike in bikes
        ]

    if not interventions:
        return {
            "technician_assignments": [],
            "total_technicians": request.num_technicians,
            "total_interventions": 0,
            "message": "Aucune intervention à assigner"
        }

    # Optimiser avec multi-techniciens
    optimizer = MultiTechnicianOptimizer()
    result = optimizer.assign_technicians(
        interventions=interventions,
        num_technicians=request.num_technicians,
        technician_names=request.technician_names
    )

    return result


@router.get("/preview-technician-zones")
async def preview_technician_zones(
    num_technicians: int = Query(3, ge=1, le=10),
    route_type: str = Query("disabled_bikes"),
    db: AsyncSession = Depends(get_db)
):
    """
    Prévisualise les zones d'assignation des techniciens sans calculer les trajets complets.

    Rapide pour afficher sur la carte les clusters avant validation.
    """
    from sklearn.cluster import KMeans
    import numpy as np

    # Récupérer les vélos
    interventions = []

    if route_type == "disabled_bikes":
        result = await db.execute(select(Bike).where(Bike.is_disabled == True))
        bikes = result.scalars().all()
        interventions = [
            {
                "id": bike.bike_id,
                "lat": float(bike.lat),
                "lon": float(bike.lon),
                "priority": "urgent"
            }
            for bike in bikes
        ]

    if not interventions:
        return {"zones": [], "message": "Aucune intervention"}

    # K-means simple
    coordinates = np.array([[i['lat'], i['lon']] for i in interventions])
    actual_num = min(num_technicians, len(interventions))

    kmeans = KMeans(n_clusters=actual_num, random_state=42, n_init=10)
    labels = kmeans.fit_predict(coordinates)
    centers = kmeans.cluster_centers_

    # Grouper par zone
    zones = []
    for i in range(actual_num):
        zone_interventions = [
            interventions[idx] for idx, label in enumerate(labels) if label == i
        ]

        zones.append({
            "zone_id": i,
            "technician_name": f"Technicien {i+1}",
            "center": {"lat": float(centers[i][0]), "lon": float(centers[i][1])},
            "num_interventions": len(zone_interventions),
            "interventions": zone_interventions[:5]  # Preview 5 premiers
        })

    return {
        "zones": zones,
        "total_interventions": len(interventions),
        "num_technicians": actual_num
    }
