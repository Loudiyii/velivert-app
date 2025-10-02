"""API endpoint for manual data refresh."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import structlog

from app.database import get_db
from app.services.gbfs_poller import GBFSPollerService
from app.repositories import StationRepository, BikeRepository

router = APIRouter()
logger = structlog.get_logger()


@router.post("/manual-refresh")
async def manual_data_refresh(db: AsyncSession = Depends(get_db)):
    """
    Déclenche un rafraîchissement manuel des données GBFS.

    Utile pour obtenir immédiatement les dernières données sans attendre
    le prochain cycle du daemon (5 minutes).
    """
    logger.info("manual_refresh_triggered")

    poller = GBFSPollerService()

    try:
        # Récupérer les données GBFS
        logger.info("Fetching GBFS data...")
        station_info = await poller.fetch_station_information()
        station_status = await poller.fetch_station_status()
        bike_status = await poller.fetch_free_bike_status()

        # Mettre à jour la base de données
        station_repo = StationRepository(db)
        bike_repo = BikeRepository(db)

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

        # Créer snapshots de statut
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

        # Mettre à jour les vélos
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

        # Tracker les mouvements
        movements_detected = 0
        try:
            from app.services.bike_movement_tracker import BikeMovementTracker

            bikes = await bike_repo.get_all(limit=1000)
            tracker = BikeMovementTracker(db)
            result = await tracker.track_movements_and_snapshot(bikes)
            movements_detected = result['movements_detected']

            logger.info(
                "Movement tracking completed",
                movements=result['movements_detected'],
                snapshots=result['snapshots_created']
            )
        except Exception as e:
            logger.error(f"Movement tracking failed: {e}")

        await db.commit()

        refresh_summary = {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "stats": {
                "stations_updated": stations_updated,
                "station_snapshots": snapshots_created,
                "bikes_updated": bikes_updated,
                "movements_detected": movements_detected
            },
            "message": f"✅ Données actualisées: {stations_updated} stations, {bikes_updated} vélos, {movements_detected} mouvements détectés"
        }

        logger.info("manual_refresh_completed", **refresh_summary['stats'])

        return refresh_summary

    except Exception as e:
        await db.rollback()
        logger.error(f"Manual refresh failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Échec de l'actualisation: {str(e)}"
        }
    finally:
        await poller.close()
