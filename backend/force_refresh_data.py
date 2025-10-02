"""Script pour forcer l'actualisation des données GBFS."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.gbfs_poller import GBFSPollerService
from app.repositories import StationRepository, BikeRepository
from app.database import AsyncSessionLocal
from datetime import datetime
import structlog

logger = structlog.get_logger()


async def refresh_all_data():
    """Actualise toutes les données depuis l'API GBFS."""
    logger.info("Starting data refresh...")

    poller = GBFSPollerService()

    try:
        # Récupérer les données GBFS
        logger.info("Fetching station information...")
        station_info = await poller.fetch_station_information()

        logger.info("Fetching station status...")
        station_status = await poller.fetch_station_status()

        logger.info("Fetching bike status...")
        bike_status = await poller.fetch_free_bike_status()

        # Mettre à jour la base de données
        async with AsyncSessionLocal() as db:
            try:
                # Mettre à jour les stations
                station_repo = StationRepository(db)
                stations_updated = 0

                for station in station_info.data.stations:
                    from app.schemas.station import StationCreate
                    station_data = StationCreate(
                        id=station.station_id,
                        name=station.name,
                        lat=station.lat,
                        lon=station.lon,
                        address=station.address,
                        capacity=station.capacity,
                        region_id=station.region_id,
                        rental_methods=station.rental_methods,
                        is_virtual_station=station.is_virtual_station or False
                    )
                    await station_repo.upsert(station_data)
                    stations_updated += 1

                logger.info(f"Updated {stations_updated} stations")

                # Créer des snapshots de statut
                snapshot_time = datetime.fromtimestamp(station_status.last_updated)
                snapshots_created = 0

                for status in station_status.data.stations:
                    await station_repo.store_status_snapshot(
                        station_id=status.station_id,
                        timestamp=snapshot_time,
                        status_data={
                            "num_bikes_available": status.num_bikes_available,
                            "num_bikes_disabled": status.num_bikes_disabled or 0,
                            "num_docks_available": status.num_docks_available,
                            "num_docks_disabled": status.num_docks_disabled or 0,
                            "is_installed": status.is_installed,
                            "is_renting": status.is_renting,
                            "is_returning": status.is_returning,
                            "last_reported": datetime.fromtimestamp(status.last_reported)
                        }
                    )
                    snapshots_created += 1

                logger.info(f"Created {snapshots_created} station snapshots")

                # Mettre à jour les vélos
                bike_repo = BikeRepository(db)
                bikes_updated = 0

                for bike in bike_status.data.bikes:
                    # Convertir chaîne vide en None pour la clé étrangère
                    station_id = bike.station_id if bike.station_id and bike.station_id.strip() else None

                    bike_data = {
                        "bike_id": bike.bike_id,
                        "lat": bike.lat,
                        "lon": bike.lon,
                        "is_reserved": bike.is_reserved,
                        "is_disabled": bike.is_disabled,
                        "vehicle_type_id": bike.vehicle_type_id,
                        "current_range_meters": bike.current_range_meters,
                        "current_station_id": station_id
                    }
                    await bike_repo.upsert(bike_data)
                    bikes_updated += 1

                logger.info(f"Updated {bikes_updated} bikes")

                # Tracker les mouvements
                try:
                    from app.services.bike_movement_tracker import BikeMovementTracker

                    bikes = await bike_repo.get_all(limit=1000)
                    tracker = BikeMovementTracker(db)
                    result = await tracker.track_movements_and_snapshot(bikes)

                    logger.info(
                        f"Movement tracking completed",
                        movements=result['movements_detected'],
                        snapshots=result['snapshots_created']
                    )
                except Exception as e:
                    logger.error(f"Movement tracking failed: {e}")

                await db.commit()

                print("\n" + "="*60)
                print("✅ DATA REFRESH COMPLETED SUCCESSFULLY!")
                print("="*60)
                print(f"📊 Stations updated: {stations_updated}")
                print(f"📊 Station snapshots: {snapshots_created}")
                print(f"🚲 Bikes updated: {bikes_updated}")
                print(f"🕒 Timestamp: {datetime.now().isoformat()}")
                print("="*60 + "\n")

            except Exception as e:
                await db.rollback()
                logger.error(f"Database error: {e}", exc_info=True)
                raise

    except Exception as e:
        logger.error(f"Failed to refresh data: {e}", exc_info=True)
        raise
    finally:
        await poller.close()


if __name__ == "__main__":
    print("\n🔄 Starting GBFS data refresh...\n")
    asyncio.run(refresh_all_data())
