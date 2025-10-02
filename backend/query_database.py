"""
Utility script for querying and searching Vélivert database.

This script provides examples of common queries to search and analyze
bike and station data in the database.

Usage:
    python query_database.py [command] [args]

Examples:
    python query_database.py disabled_bikes
    python query_database.py low_battery
    python query_database.py bike_by_id BIKE123
    python query_database.py bikes_at_station STATION456
    python query_database.py station_status
"""

import asyncio
import sys
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Bike, Station, StationStatusSnapshot, MaintenanceIntervention
from app.repositories import BikeRepository, StationRepository


async def find_disabled_bikes():
    """Find all disabled bikes that need inspection."""
    async with AsyncSessionLocal() as db:
        repo = BikeRepository(db)
        bikes = await repo.get_disabled_bikes()

        print(f"\n=== Vélos Désactivés ({len(bikes)}) ===\n")
        for bike in bikes:
            print(f"ID: {bike.bike_id}")
            print(f"  Type: {bike.vehicle_type_id}")
            print(f"  Station: {bike.current_station_id or 'En circulation'}")
            print(f"  Position: {bike.lat}, {bike.lon}")
            print(f"  Autonomie: {bike.current_range_meters}m")
            print(f"  Réservé: {bike.is_reserved}")
            print()


async def find_low_battery_bikes(threshold_km: float = 5.0):
    """Find bikes with low battery (< threshold km)."""
    async with AsyncSessionLocal() as db:
        threshold_meters = threshold_km * 1000

        result = await db.execute(
            select(Bike)
            .where(
                and_(
                    Bike.is_disabled == False,
                    Bike.current_range_meters < threshold_meters,
                    Bike.current_range_meters > 0
                )
            )
            .order_by(Bike.current_range_meters)
        )
        bikes = result.scalars().all()

        print(f"\n=== Vélos avec Autonomie Faible (< {threshold_km}km) ({len(bikes)}) ===\n")
        for bike in bikes:
            range_km = bike.current_range_meters / 1000 if bike.current_range_meters else 0
            print(f"ID: {bike.bike_id}")
            print(f"  Autonomie: {range_km:.1f}km")
            print(f"  Station: {bike.current_station_id or 'En circulation'}")
            print(f"  Position: {bike.lat}, {bike.lon}")
            print()


async def find_empty_battery_bikes():
    """Find bikes with empty battery (0km)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Bike)
            .where(
                or_(
                    Bike.current_range_meters == 0,
                    Bike.current_range_meters == None
                )
            )
        )
        bikes = result.scalars().all()

        print(f"\n=== Vélos avec Batterie Vide ({len(bikes)}) ===\n")
        for bike in bikes:
            print(f"ID: {bike.bike_id}")
            print(f"  Désactivé: {bike.is_disabled}")
            print(f"  Station: {bike.current_station_id or 'En circulation'}")
            print(f"  Position: {bike.lat}, {bike.lon}")
            print()


async def find_bike_by_id(bike_id: str):
    """Find a specific bike by ID (supports partial match)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Bike)
            .where(Bike.bike_id.ilike(f"%{bike_id}%"))
        )
        bikes = result.scalars().all()

        if not bikes:
            print(f"\nAucun vélo trouvé avec l'ID contenant: {bike_id}")
            return

        print(f"\n=== Vélos trouvés ({len(bikes)}) ===\n")
        for bike in bikes:
            print(f"ID: {bike.bike_id}")
            print(f"  Type: {bike.vehicle_type_id}")
            print(f"  Station: {bike.current_station_id or 'En circulation'}")
            print(f"  Position: {bike.lat}, {bike.lon}")
            print(f"  Autonomie: {bike.current_range_meters}m")
            print(f"  Désactivé: {bike.is_disabled}")
            print(f"  Réservé: {bike.is_reserved}")
            print(f"  Dernière mise à jour: {bike.last_reported}")
            print()


async def find_bikes_at_station(station_id: str):
    """Find all bikes at a specific station (supports partial match)."""
    async with AsyncSessionLocal() as db:
        repo = BikeRepository(db)

        # Try exact match first
        bikes = await repo.get_bikes_by_station(station_id)

        # If no results, try partial match
        if not bikes:
            result = await db.execute(
                select(Bike)
                .where(Bike.current_station_id.ilike(f"%{station_id}%"))
            )
            bikes = result.scalars().all()

        if not bikes:
            print(f"\nAucun vélo trouvé à la station: {station_id}")
            return

        print(f"\n=== Vélos à la station {station_id} ({len(bikes)}) ===\n")
        available = sum(1 for b in bikes if not b.is_disabled and not b.is_reserved)
        disabled = sum(1 for b in bikes if b.is_disabled)
        reserved = sum(1 for b in bikes if b.is_reserved)

        print(f"Disponibles: {available}")
        print(f"Désactivés: {disabled}")
        print(f"Réservés: {reserved}")
        print()

        for bike in bikes:
            status = "DÉSACTIVÉ" if bike.is_disabled else ("RÉSERVÉ" if bike.is_reserved else "DISPONIBLE")
            range_km = bike.current_range_meters / 1000 if bike.current_range_meters else 0
            print(f"  {bike.bike_id[:8]}... - {status} - {range_km:.1f}km")


async def show_station_status():
    """Show status summary of all stations."""
    async with AsyncSessionLocal() as db:
        repo = StationRepository(db)
        stations = await repo.get_all(skip=0, limit=500)

        print(f"\n=== Statut des Stations ({len(stations)}) ===\n")

        # Collect statistics
        empty_stations = []
        full_stations = []
        low_bikes_stations = []

        for station in stations:
            latest = await repo.get_latest_status(station.id)
            if latest:
                bikes = latest.get('num_bikes_available', 0)

                if bikes == 0:
                    empty_stations.append((station.name, station.id))
                elif bikes >= station.capacity * 0.9:
                    full_stations.append((station.name, bikes, station.capacity))
                elif bikes < 3:
                    low_bikes_stations.append((station.name, bikes))

        print(f"Stations vides (0 vélos): {len(empty_stations)}")
        if empty_stations[:5]:
            for name, sid in empty_stations[:5]:
                print(f"  - {name} ({sid[:12]}...)")

        print(f"\nStations pleines (>90%): {len(full_stations)}")
        if full_stations[:5]:
            for name, bikes, capacity in full_stations[:5]:
                print(f"  - {name}: {bikes}/{capacity} vélos")

        print(f"\nStations avec peu de vélos (<3): {len(low_bikes_stations)}")
        if low_bikes_stations[:5]:
            for name, bikes in low_bikes_stations[:5]:
                print(f"  - {name}: {bikes} vélos")


async def find_suspect_bikes():
    """Find all bikes that need attention (suspect bikes)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Bike)
            .where(
                or_(
                    Bike.is_disabled == True,
                    Bike.current_range_meters < 5000,
                    Bike.current_range_meters == 0,
                    Bike.current_range_meters == None
                )
            )
            .order_by(
                Bike.is_disabled.desc(),
                Bike.current_range_meters
            )
        )
        bikes = result.scalars().all()

        print(f"\n=== Vélos Suspects Nécessitant Intervention ({len(bikes)}) ===\n")

        for bike in bikes:
            reasons = []
            priority = "medium"

            if bike.is_disabled:
                reasons.append("DÉSACTIVÉ")
                priority = "high"

            if bike.current_range_meters is None or bike.current_range_meters == 0:
                reasons.append("BATTERIE VIDE")
                priority = "urgent"
            elif bike.current_range_meters < 5000:
                range_km = bike.current_range_meters / 1000
                reasons.append(f"AUTONOMIE FAIBLE ({range_km:.1f}km)")
                priority = "high"

            print(f"[{priority.upper()}] {bike.bike_id[:8]}...")
            print(f"  Raisons: {', '.join(reasons)}")
            print(f"  Station: {bike.current_station_id[:12] if bike.current_station_id else 'En circulation'}...")
            print(f"  Position: {bike.lat}, {bike.lon}")
            print()


async def show_recent_interventions():
    """Show recent interventions."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MaintenanceIntervention)
            .order_by(desc(MaintenanceIntervention.created_at))
            .limit(10)
        )
        interventions = result.scalars().all()

        print(f"\n=== Interventions Récentes ({len(interventions)}) ===\n")

        for intervention in interventions:
            print(f"ID: {intervention.id}")
            print(f"  Vélo: {intervention.bike_id[:12]}...")
            print(f"  Type: {intervention.intervention_type}")
            print(f"  Priorité: {intervention.priority}")
            print(f"  Statut: {intervention.status}")
            print(f"  Créée: {intervention.created_at}")
            if intervention.description:
                print(f"  Description: {intervention.description}")
            print()


async def show_station_history(station_id: str, hours: int = 24):
    """Show station occupancy history."""
    async with AsyncSessionLocal() as db:
        repo = StationRepository(db)

        station = await repo.get_by_id(station_id)
        if not station:
            print(f"\nStation non trouvée: {station_id}")
            return

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        history = await repo.get_status_history(
            station_id=station_id,
            start_time=start_time,
            end_time=end_time,
            interval="1 hour"
        )

        print(f"\n=== Historique Station: {station.name} (dernières {hours}h) ===\n")

        for point in history:
            print(f"{point['bucket'].strftime('%Y-%m-%d %H:%M')}")
            print(f"  Moyenne: {point['avg_bikes_available']:.1f} vélos")
            print(f"  Min: {point['min_bikes_available']} vélos")
            print(f"  Max: {point['max_bikes_available']} vélos")
            print()


# Command line interface
async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    try:
        if command == "disabled_bikes":
            await find_disabled_bikes()

        elif command == "low_battery":
            threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
            await find_low_battery_bikes(threshold)

        elif command == "empty_battery":
            await find_empty_battery_bikes()

        elif command == "bike_by_id":
            if len(sys.argv) < 3:
                print("Usage: python query_database.py bike_by_id <bike_id>")
                return
            await find_bike_by_id(sys.argv[2])

        elif command == "bikes_at_station":
            if len(sys.argv) < 3:
                print("Usage: python query_database.py bikes_at_station <station_id>")
                return
            await find_bikes_at_station(sys.argv[2])

        elif command == "station_status":
            await show_station_status()

        elif command == "suspect_bikes":
            await find_suspect_bikes()

        elif command == "recent_interventions":
            await show_recent_interventions()

        elif command == "station_history":
            if len(sys.argv) < 3:
                print("Usage: python query_database.py station_history <station_id> [hours]")
                return
            hours = int(sys.argv[3]) if len(sys.argv) > 3 else 24
            await show_station_history(sys.argv[2], hours)

        else:
            print(f"Commande inconnue: {command}")
            print(__doc__)

    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
