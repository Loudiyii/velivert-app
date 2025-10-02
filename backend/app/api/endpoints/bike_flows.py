"""API endpoints for bike flow analysis between stations."""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text

from app.database import get_db
from app.models import Bike, StationStatusSnapshot
from app.models.bike_movement import BikeMovement

router = APIRouter()


@router.get("/flows/station-movements")
async def get_station_to_station_flows(
    hours: int = Query(24, ge=1, le=168, description="Nombre d'heures d'historique"),
    min_flow: int = Query(0, ge=0, description="Flux minimum à afficher"),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyse les mouvements de vélos entre stations.

    Retourne un graphe de flux montrant:
    - Les stations source et destination
    - Le nombre de vélos déplacés entre chaque paire de stations
    - Les stations les plus actives (hubs)

    Basé sur l'historique des snapshots de stations.
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)

    # Query pour calculer les flux nets entre stations
    query = text("""
        WITH station_changes AS (
            SELECT
                station_id,
                time,
                num_bikes_available,
                LAG(num_bikes_available) OVER (PARTITION BY station_id ORDER BY time) as prev_bikes,
                num_bikes_available - LAG(num_bikes_available) OVER (PARTITION BY station_id ORDER BY time) as bike_change
            FROM station_status_snapshots
            WHERE time >= :start_time AND time <= :end_time
        )
        SELECT
            station_id,
            COALESCE(SUM(CASE WHEN bike_change > 0 THEN bike_change ELSE 0 END), 0) as bikes_arrived,
            COALESCE(SUM(CASE WHEN bike_change < 0 THEN ABS(bike_change) ELSE 0 END), 0) as bikes_departed,
            AVG(num_bikes_available) as avg_bikes
        FROM station_changes
        WHERE bike_change IS NOT NULL
        GROUP BY station_id
        ORDER BY (COALESCE(SUM(CASE WHEN bike_change > 0 THEN bike_change ELSE 0 END), 0) +
                  COALESCE(SUM(CASE WHEN bike_change < 0 THEN ABS(bike_change) ELSE 0 END), 0)) DESC
    """)

    result = await db.execute(
        query,
        {
            "start_time": start_time,
            "end_time": end_time,
            "min_flow": min_flow
        }
    )

    stations = result.fetchall()

    # Récupérer les informations des stations
    from app.repositories import StationRepository
    repo = StationRepository(db)
    station_details = {}

    for row in stations:
        station = await repo.get_by_id(row[0])
        if station:
            station_details[row[0]] = {
                "station_id": station.id,
                "name": station.name,
                "lat": float(station.lat),
                "lon": float(station.lon),
                "capacity": station.capacity,
                "bikes_arrived": int(row[1]),
                "bikes_departed": int(row[2]),
                "avg_bikes": float(row[3]),
                "net_flow": int(row[1]) - int(row[2]),  # Positif = plus d'arrivées, négatif = plus de départs
                "total_activity": int(row[1]) + int(row[2])
            }

    # Identifier les hubs (stations très actives)
    stations_list = list(station_details.values())
    if stations_list:
        avg_activity = sum(s["total_activity"] for s in stations_list) / len(stations_list)

        for station in stations_list:
            if station["total_activity"] > avg_activity * 1.5:
                station["is_hub"] = True
            else:
                station["is_hub"] = False

    return {
        "period_hours": hours,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "stations": stations_list,
        "summary": {
            "total_stations": len(stations_list),
            "total_arrivals": sum(s["bikes_arrived"] for s in stations_list),
            "total_departures": sum(s["bikes_departed"] for s in stations_list),
            "most_active_station": max(stations_list, key=lambda s: s["total_activity"]) if stations_list else None
        }
    }


@router.get("/flows/current-circulation")
async def get_current_bike_circulation(
    db: AsyncSession = Depends(get_db)
):
    """
    Retourne la circulation actuelle des vélos.

    Montre:
    - Les vélos en circulation (hors stations)
    - Leur dernière position connue
    - Leur mouvement estimé
    """
    # Récupérer tous les vélos en circulation (sans station, incluant désactivés)
    result = await db.execute(
        select(Bike).where(
            or_(
                Bike.current_station_id == None,
                Bike.current_station_id == ''
            )
        )
    )
    bikes_in_circulation = result.scalars().all()

    bikes_data = [
        {
            "bike_id": bike.bike_id,
            "lat": float(bike.lat),
            "lon": float(bike.lon),
            "range_meters": bike.current_range_meters,
            "range_km": round(bike.current_range_meters / 1000, 1) if bike.current_range_meters else 0,
            "is_reserved": bike.is_reserved,
            "is_disabled": bike.is_disabled,
            "vehicle_type_id": bike.vehicle_type_id,
            "last_reported": bike.last_reported.isoformat() if bike.last_reported else None
        }
        for bike in bikes_in_circulation
    ]

    return {
        "bikes_in_circulation": bikes_data,
        "total_count": len(bikes_data),
        "disabled_count": sum(1 for b in bikes_data if b["is_disabled"]),
        "reserved_count": sum(1 for b in bikes_data if b["is_reserved"]),
        "available_count": sum(1 for b in bikes_data if not b["is_disabled"] and not b["is_reserved"])
    }


@router.get("/flows/station-demand")
async def get_station_demand_patterns(
    hours: int = Query(24, ge=1, le=168, description="Nombre d'heures d'historique"),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyse les patterns de demande pour chaque station.

    Identifie:
    - Stations sources (beaucoup de départs)
    - Stations puits (beaucoup d'arrivées)
    - Heures de pointe
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)

    query = text("""
        SELECT
            station_id,
            EXTRACT(HOUR FROM time) as hour_of_day,
            AVG(num_bikes_available) as avg_bikes,
            MIN(num_bikes_available) as min_bikes,
            MAX(num_bikes_available) as max_bikes,
            STDDEV(num_bikes_available) as volatility
        FROM station_status_snapshots
        WHERE time >= :start_time AND time <= :end_time
        GROUP BY station_id, EXTRACT(HOUR FROM time)
        ORDER BY station_id, hour_of_day
    """)

    result = await db.execute(
        query,
        {
            "start_time": start_time,
            "end_time": end_time
        }
    )

    patterns = {}
    for row in result.fetchall():
        station_id = row[0]
        if station_id not in patterns:
            patterns[station_id] = {
                "station_id": station_id,
                "hourly_patterns": []
            }

        patterns[station_id]["hourly_patterns"].append({
            "hour": int(row[1]),
            "avg_bikes": float(row[2]),
            "min_bikes": int(row[3]),
            "max_bikes": int(row[4]),
            "volatility": float(row[5]) if row[5] else 0
        })

    # Enrichir avec les infos de station
    from app.repositories import StationRepository
    repo = StationRepository(db)

    stations_data = []
    for station_id, data in patterns.items():
        station = await repo.get_by_id(station_id)
        if station:
            # Calculer les caractéristiques
            hourly = data["hourly_patterns"]
            peak_hour = max(hourly, key=lambda h: h["avg_bikes"])
            low_hour = min(hourly, key=lambda h: h["avg_bikes"])

            stations_data.append({
                **data,
                "name": station.name,
                "lat": float(station.lat),
                "lon": float(station.lon),
                "capacity": station.capacity,
                "peak_hour": peak_hour["hour"],
                "peak_bikes": peak_hour["avg_bikes"],
                "low_hour": low_hour["hour"],
                "low_bikes": low_hour["avg_bikes"],
                "demand_variance": peak_hour["avg_bikes"] - low_hour["avg_bikes"]
            })

    return {
        "period_hours": hours,
        "stations": stations_data,
        "summary": {
            "total_stations": len(stations_data)
        }
    }


@router.get("/movements/history")
async def get_bike_movement_history(
    bike_id: Optional[str] = Query(None, description="ID du vélo spécifique"),
    hours: int = Query(24, ge=1, le=168, description="Nombre d'heures d'historique"),
    movement_type: Optional[str] = Query(None, description="Type de mouvement: pickup, dropoff, relocation, in_transit"),
    limit: int = Query(100, ge=1, le=10000, description="Nombre maximum de mouvements"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retourne l'historique réel des mouvements de vélos.

    Utilise la table bike_movements pour afficher les vrais déplacements
    détectés par le système de tracking.
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)

    # Construire la requête avec filtres
    query = select(BikeMovement).where(
        BikeMovement.detected_at >= start_time
    )

    if bike_id:
        query = query.where(BikeMovement.bike_id == bike_id)

    if movement_type:
        query = query.where(BikeMovement.movement_type == movement_type)

    query = query.order_by(BikeMovement.detected_at.desc()).limit(limit)

    result = await db.execute(query)
    movements = result.scalars().all()

    movements_data = [
        {
            "id": movement.id,
            "bike_id": movement.bike_id,
            "from_station_id": movement.from_station_id,
            "from_lat": float(movement.from_lat) if movement.from_lat else None,
            "from_lon": float(movement.from_lon) if movement.from_lon else None,
            "to_station_id": movement.to_station_id,
            "to_lat": float(movement.to_lat),
            "to_lon": float(movement.to_lon),
            "movement_type": movement.movement_type,
            "distance_meters": float(movement.distance_meters) if movement.distance_meters else None,
            "is_reserved": movement.is_reserved,
            "is_disabled": movement.is_disabled,
            "battery_range_meters": movement.battery_range_meters,
            "detected_at": movement.detected_at.isoformat()
        }
        for movement in movements
    ]

    # Statistiques
    pickup_count = sum(1 for m in movements_data if m["movement_type"] == "pickup")
    dropoff_count = sum(1 for m in movements_data if m["movement_type"] == "dropoff")
    relocation_count = sum(1 for m in movements_data if m["movement_type"] == "relocation")
    in_transit_count = sum(1 for m in movements_data if m["movement_type"] == "in_transit")

    total_distance = sum(m["distance_meters"] for m in movements_data if m["distance_meters"])

    return {
        "period_hours": hours,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "movements": movements_data,
        "summary": {
            "total_movements": len(movements_data),
            "pickups": pickup_count,
            "dropoffs": dropoff_count,
            "relocations": relocation_count,
            "in_transit": in_transit_count,
            "total_distance_km": round(total_distance / 1000, 2) if total_distance else 0,
            "unique_bikes": len(set(m["bike_id"] for m in movements_data))
        }
    }


@router.get("/movements/real-time-flows")
async def get_real_time_bike_flows(
    hours: int = Query(1, ge=1, le=24, description="Nombre d'heures d'historique"),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyse les flux réels de vélos entre stations basés sur les mouvements détectés.

    Plus précis que la méthode basée sur les snapshots car il utilise
    les mouvements réellement détectés.
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)

    # Requête pour obtenir les flux entre stations
    query = text("""
        SELECT
            from_station_id,
            to_station_id,
            movement_type,
            COUNT(*) as movement_count,
            AVG(distance_meters) as avg_distance
        FROM bike_movements
        WHERE detected_at >= :start_time
          AND detected_at <= :end_time
          AND from_station_id IS NOT NULL
          AND to_station_id IS NOT NULL
        GROUP BY from_station_id, to_station_id, movement_type
        ORDER BY movement_count DESC
        LIMIT 100
    """)

    result = await db.execute(
        query,
        {
            "start_time": start_time,
            "end_time": end_time
        }
    )

    flows = []
    from app.repositories import StationRepository
    repo = StationRepository(db)

    for row in result.fetchall():
        from_station = await repo.get_by_id(row[0])
        to_station = await repo.get_by_id(row[1])

        if from_station and to_station:
            flows.append({
                "from_station_id": row[0],
                "from_station_name": from_station.name,
                "from_lat": float(from_station.lat),
                "from_lon": float(from_station.lon),
                "to_station_id": row[1],
                "to_station_name": to_station.name,
                "to_lat": float(to_station.lat),
                "to_lon": float(to_station.lon),
                "movement_type": row[2],
                "count": int(row[3]),
                "avg_distance_meters": float(row[4]) if row[4] else 0
            })

    return {
        "period_hours": hours,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "flows": flows,
        "summary": {
            "total_flows": len(flows),
            "total_movements": sum(f["count"] for f in flows)
        }
    }
