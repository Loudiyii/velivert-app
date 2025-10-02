"""API endpoints for route optimization."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.models import Bike, MaintenanceIntervention
from app.services.route_optimizer import RouteOptimizerService
from app.schemas.route import OptimizedRouteResponse, OptimizedRouteWaypoint

router = APIRouter()


@router.get("/optimize/disabled-bikes", response_model=OptimizedRouteResponse)
async def optimize_disabled_bikes_route(
    start_lat: float = Query(45.439695, description="Latitude du point de départ"),
    start_lon: float = Query(4.387178, description="Longitude du point de départ"),
    db: AsyncSession = Depends(get_db)
):
    """
    Calcule le trajet optimal pour collecter tous les vélos désactivés.

    Point de départ par défaut : Centre de Saint-Étienne.
    """
    # Récupérer tous les vélos désactivés
    result = await db.execute(
        select(Bike).where(Bike.is_disabled == True)
    )
    disabled_bikes = result.scalars().all()

    if not disabled_bikes:
        return {
            "waypoints": [],
            "total_distance_meters": 0,
            "estimated_duration_minutes": 0,
            "total_bikes": 0,
            "optimization_algorithm": "Nearest Neighbor",
            "route_type": "disabled_bikes_collection"
        }

    # Préparer les interventions
    interventions = [
        {
            "id": bike.bike_id,
            "lat": float(bike.lat),
            "lon": float(bike.lon),
            "priority": "urgent",
            "station_id": bike.current_station_id,
            "bike_id": bike.bike_id
        }
        for bike in disabled_bikes
    ]

    # Optimiser le trajet
    optimizer = RouteOptimizerService()
    route = optimizer.optimize_route(
        interventions=interventions,
        start_location=(start_lat, start_lon),
        prioritize_urgent=True
    )

    # Ajouter les informations supplémentaires
    route["total_bikes"] = len(disabled_bikes)
    route["route_type"] = "disabled_bikes_collection"

    return route


@router.get("/optimize/pending-interventions", response_model=OptimizedRouteResponse)
async def optimize_pending_interventions_route(
    start_lat: float = Query(45.439695, description="Latitude du point de départ"),
    start_lon: float = Query(4.387178, description="Longitude du point de départ"),
    max_interventions: int = Query(10, ge=1, le=50, description="Nombre max d'interventions"),
    db: AsyncSession = Depends(get_db)
):
    """
    Calcule le trajet optimal pour effectuer les interventions en attente.

    Priorise les interventions urgentes et limite le nombre d'interventions.
    """
    # Récupérer les interventions en attente
    result = await db.execute(
        select(MaintenanceIntervention)
        .where(MaintenanceIntervention.status == "pending")
        .limit(max_interventions)
    )
    pending_interventions = result.scalars().all()

    if not pending_interventions:
        return {
            "waypoints": [],
            "total_distance_meters": 0,
            "estimated_duration_minutes": 0,
            "total_bikes": 0,
            "optimization_algorithm": "Nearest Neighbor",
            "route_type": "pending_interventions"
        }

    # Préparer les données d'interventions
    interventions = []
    for intervention in pending_interventions:
        # Récupérer la localisation du vélo ou de la station
        if intervention.bike_id:
            bike_result = await db.execute(
                select(Bike).where(Bike.bike_id == intervention.bike_id)
            )
            bike = bike_result.scalar_one_or_none()
            if bike:
                interventions.append({
                    "id": intervention.id,
                    "lat": float(bike.lat),
                    "lon": float(bike.lon),
                    "priority": intervention.priority,
                    "bike_id": bike.bike_id,
                    "intervention_type": intervention.intervention_type
                })

    if not interventions:
        return {
            "waypoints": [],
            "total_distance_meters": 0,
            "estimated_duration_minutes": 0,
            "total_bikes": 0,
            "optimization_algorithm": "Nearest Neighbor",
            "route_type": "pending_interventions"
        }

    # Optimiser le trajet
    optimizer = RouteOptimizerService()
    route = optimizer.optimize_route(
        interventions=interventions,
        start_location=(start_lat, start_lon),
        prioritize_urgent=True
    )

    route["total_bikes"] = len(interventions)
    route["route_type"] = "pending_interventions"

    return route


@router.get("/optimize/low-battery-bikes", response_model=OptimizedRouteResponse)
async def optimize_low_battery_route(
    start_lat: float = Query(45.439695, description="Latitude du point de départ"),
    start_lon: float = Query(4.387178, description="Longitude du point de départ"),
    threshold_km: float = Query(5.0, description="Seuil d'autonomie (km)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Calcule le trajet optimal pour collecter les vélos avec batterie faible.
    """
    threshold_meters = threshold_km * 1000

    # Récupérer les vélos avec batterie faible
    result = await db.execute(
        select(Bike).where(
            and_(
                Bike.is_disabled == False,
                Bike.current_range_meters < threshold_meters,
                Bike.current_range_meters > 0
            )
        )
    )
    low_battery_bikes = result.scalars().all()

    if not low_battery_bikes:
        return {
            "waypoints": [],
            "total_distance_meters": 0,
            "estimated_duration_minutes": 0,
            "total_bikes": 0,
            "optimization_algorithm": "Nearest Neighbor",
            "route_type": "low_battery_collection"
        }

    # Préparer les interventions
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
        for bike in low_battery_bikes
    ]

    # Optimiser le trajet
    optimizer = RouteOptimizerService()
    route = optimizer.optimize_route(
        interventions=interventions,
        start_location=(start_lat, start_lon),
        prioritize_urgent=True
    )

    route["total_bikes"] = len(low_battery_bikes)
    route["route_type"] = "low_battery_collection"

    return route


@router.get("/stations-with-disabled-bikes")
async def get_stations_with_disabled_bikes(
    db: AsyncSession = Depends(get_db)
):
    """
    Retourne la liste des stations contenant des vélos hors service.

    Utile pour permettre à l'utilisateur de choisir une station de départ.
    """
    from app.models import Station
    from sqlalchemy import func

    # Requête pour trouver les stations avec au moins un vélo désactivé
    query = select(
        Station.id,
        Station.name,
        Station.lat,
        Station.lon,
        Station.capacity,
        func.count(Bike.bike_id).label('disabled_bikes_count')
    ).join(
        Bike, Station.id == Bike.current_station_id
    ).where(
        Bike.is_disabled == True
    ).group_by(
        Station.id, Station.name, Station.lat, Station.lon, Station.capacity
    ).order_by(
        func.count(Bike.bike_id).desc()
    )

    result = await db.execute(query)
    stations = result.fetchall()

    stations_list = [
        {
            "station_id": row[0],
            "name": row[1],
            "lat": float(row[2]),
            "lon": float(row[3]),
            "capacity": row[4],
            "disabled_bikes_count": row[5]
        }
        for row in stations
    ]

    return {
        "stations": stations_list,
        "total_stations": len(stations_list),
        "total_disabled_bikes": sum(s['disabled_bikes_count'] for s in stations_list)
    }


@router.get("/optimize/detailed-route", response_model=OptimizedRouteResponse)
async def get_detailed_optimized_route(
    route_type: str = Query(..., description="Type de trajet: disabled_bikes, low_battery, pending_interventions"),
    start_station_id: Optional[str] = Query(None, description="ID de la station de départ (optionnel)"),
    start_lat: Optional[float] = Query(None, description="Latitude personnalisée du départ"),
    start_lon: Optional[float] = Query(None, description="Longitude personnalisée du départ"),
    db: AsyncSession = Depends(get_db)
):
    """
    Calcule un trajet optimisé avec descriptif détaillé.

    Permet de choisir une station de départ ou des coordonnées personnalisées.
    Retourne un itinéraire détaillé station par station avec instructions.
    """
    from app.models import Station

    # Déterminer le point de départ
    if start_station_id:
        # Utiliser la station spécifiée
        station_result = await db.execute(
            select(Station).where(Station.id == start_station_id)
        )
        station = station_result.scalar_one_or_none()
        if not station:
            raise HTTPException(status_code=404, detail="Station de départ introuvable")
        start_coordinates = (float(station.lat), float(station.lon))
        start_location_name = station.name
    elif start_lat and start_lon:
        # Utiliser les coordonnées personnalisées
        start_coordinates = (start_lat, start_lon)
        start_location_name = f"Position personnalisée ({start_lat:.4f}, {start_lon:.4f})"
    else:
        # Utiliser le centre de Saint-Étienne par défaut
        start_coordinates = (45.439695, 4.387178)
        start_location_name = "Centre de Saint-Étienne"

    # Préparer les interventions selon le type
    interventions = []

    if route_type == "disabled_bikes":
        result = await db.execute(select(Bike).where(Bike.is_disabled == True))
        bikes = result.scalars().all()
        interventions = [
            {
                "id": bike.bike_id,
                "lat": float(bike.lat),
                "lon": float(bike.lon),
                "priority": "urgent",
                "station_id": bike.current_station_id,
                "bike_id": bike.bike_id
            }
            for bike in bikes
        ]

    elif route_type == "low_battery":
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

    elif route_type == "pending_interventions":
        result = await db.execute(
            select(MaintenanceIntervention)
            .where(MaintenanceIntervention.status == "pending")
            .limit(20)
        )
        pending = result.scalars().all()

        for intervention in pending:
            if intervention.bike_id:
                bike_result = await db.execute(
                    select(Bike).where(Bike.bike_id == intervention.bike_id)
                )
                bike = bike_result.scalar_one_or_none()
                if bike:
                    interventions.append({
                        "id": intervention.id,
                        "lat": float(bike.lat),
                        "lon": float(bike.lon),
                        "priority": intervention.priority,
                        "bike_id": bike.bike_id,
                        "intervention_type": intervention.intervention_type
                    })

    if not interventions:
        return {
            "waypoints": [],
            "total_distance_meters": 0,
            "estimated_duration_minutes": 0,
            "total_bikes": 0,
            "optimization_algorithm": "Nearest Neighbor",
            "route_type": route_type,
            "start_location": start_location_name,
            "detailed_instructions": []
        }

    # Optimiser le trajet
    optimizer = RouteOptimizerService()
    route = optimizer.optimize_route(
        interventions=interventions,
        start_location=start_coordinates,
        prioritize_urgent=True
    )

    # Ajouter les informations supplémentaires
    route["total_bikes"] = len(interventions)
    route["route_type"] = route_type
    route["start_location"] = start_location_name

    # Générer les instructions détaillées
    detailed_instructions = []
    detailed_instructions.append({
        "step": 0,
        "action": "start",
        "location": start_location_name,
        "description": f"🚀 Départ depuis {start_location_name}"
    })

    for idx, waypoint in enumerate(route["waypoints"], 1):
        # Récupérer le nom de la station si disponible
        station_name = "Position GPS"
        if waypoint.get("station_id"):
            station_result = await db.execute(
                select(Station).where(Station.id == waypoint["station_id"])
            )
            station = station_result.scalar_one_or_none()
            if station:
                station_name = station.name

        bike_id_short = waypoint.get("bike_id", "")[:8] if waypoint.get("bike_id") else "N/A"
        priority_emoji = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
            waypoint.get("priority", "medium"), "⚪"
        )

        detailed_instructions.append({
            "step": idx,
            "action": "collect",
            "location": station_name,
            "bike_id": waypoint.get("bike_id"),
            "priority": waypoint.get("priority"),
            "description": f"{priority_emoji} Arrêt #{idx}: {station_name} - Vélo {bike_id_short}"
        })

    detailed_instructions.append({
        "step": len(route["waypoints"]) + 1,
        "action": "finish",
        "location": "Point de retour",
        "description": f"🏁 Fin du trajet - {len(interventions)} vélo(s) collecté(s)"
    })

    route["detailed_instructions"] = detailed_instructions

    return route
