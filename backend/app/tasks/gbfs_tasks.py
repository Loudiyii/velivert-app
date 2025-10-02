"""Celery tasks for GBFS data polling."""

import structlog
from datetime import datetime
from celery import shared_task
from app.tasks.celery_app import celery_app
from app.services import GBFSPollerService
from app.services.bike_movement_tracker import BikeMovementTracker
from app.repositories import StationRepository, BikeRepository
from app.schemas.station import StationCreate
from app.database import SessionLocal, AsyncSessionLocal
from app.models.bike import Bike

logger = structlog.get_logger()


@celery_app.task(name="poll_station_status", bind=True, max_retries=3)
def poll_station_status(self):
    """
    Poll station_status.json every 30 seconds.

    Fetches current station status and stores snapshots in TimescaleDB.
    """
    logger.info("task_started", task="poll_station_status")

    db = SessionLocal()

    try:
        # Fetch station status from GBFS API
        import asyncio
        poller = GBFSPollerService()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            status_feed = loop.run_until_complete(poller.fetch_station_status())
        finally:
            loop.run_until_complete(poller.close())
            loop.close()

        # Store snapshots in database
        repo = StationRepository(db)
        snapshot_time = datetime.fromtimestamp(status_feed.last_updated)

        stored_count = 0
        for station_status in status_feed.data.stations:
            try:
                # Store status snapshot (idempotent)
                asyncio.run(repo.store_status_snapshot(
                    station_id=station_status.station_id,
                    timestamp=snapshot_time,
                    status_data={
                        "num_bikes_available": station_status.num_bikes_available,
                        "num_bikes_disabled": station_status.num_bikes_disabled or 0,
                        "num_docks_available": station_status.num_docks_available,
                        "num_docks_disabled": station_status.num_docks_disabled or 0,
                        "is_installed": station_status.is_installed,
                        "is_renting": station_status.is_renting,
                        "is_returning": station_status.is_returning,
                        "last_reported": datetime.fromtimestamp(station_status.last_reported)
                    }
                ))
                stored_count += 1
            except Exception as e:
                logger.error("snapshot_store_failed", station_id=station_status.station_id, error=str(e))

        db.commit()

        logger.info(
            "task_completed",
            task="poll_station_status",
            stations_processed=len(status_feed.data.stations),
            snapshots_stored=stored_count
        )

        return {
            "status": "success",
            "stations_processed": len(status_feed.data.stations),
            "snapshots_stored": stored_count,
            "timestamp": snapshot_time.isoformat()
        }

    except Exception as exc:
        logger.error("task_failed", task="poll_station_status", error=str(exc), exc_info=True)
        db.rollback()
        raise self.retry(exc=exc, countdown=60)

    finally:
        db.close()


@celery_app.task(name="poll_free_bike_status", bind=True, max_retries=3)
def poll_free_bike_status(self):
    """
    Poll free_bike_status.json every 30 seconds.

    Fetches current bike positions, updates bike table, and tracks movements.
    """
    logger.info("task_started", task="poll_free_bike_status")

    db = SessionLocal()

    try:
        # Fetch bike status from GBFS API
        import asyncio
        poller = GBFSPollerService()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            bike_feed = loop.run_until_complete(poller.fetch_free_bike_status())
        finally:
            loop.run_until_complete(poller.close())
            loop.close()

        # Update bikes in database
        repo = BikeRepository(db)
        updated_count = 0

        for bike in bike_feed.data.bikes:
            try:
                bike_data = {
                    "bike_id": bike.bike_id,
                    "lat": bike.lat,
                    "lon": bike.lon,
                    "is_reserved": bike.is_reserved,
                    "is_disabled": bike.is_disabled,
                    "vehicle_type_id": bike.vehicle_type_id,
                    "current_range_meters": bike.current_range_meters,
                    "current_station_id": bike.station_id
                }

                # Upsert bike (idempotent)
                asyncio.run(repo.upsert(bike_data))
                updated_count += 1
            except Exception as e:
                logger.error("bike_update_failed", bike_id=bike.bike_id, error=str(e))

        db.commit()

        # Track movements and create snapshots
        try:
            async def track_movements():
                """Helper function to run movement tracking in async context."""
                async with AsyncSessionLocal() as async_db:
                    try:
                        # Get all bikes from database (with updated positions)
                        async_repo = BikeRepository(async_db)
                        bikes = await async_repo.get_all(limit=1000)

                        # Initialize movement tracker
                        tracker = BikeMovementTracker(async_db)

                        # Detect movements and create snapshots
                        result = await tracker.track_movements_and_snapshot(bikes)

                        await async_db.commit()
                        return result
                    except Exception:
                        await async_db.rollback()
                        raise

            tracking_result = asyncio.run(track_movements())

            logger.info(
                "movement_tracking_completed",
                movements_detected=tracking_result['movements_detected'],
                snapshots_created=tracking_result['snapshots_created']
            )
        except Exception as e:
            logger.error("movement_tracking_failed", error=str(e), exc_info=True)
            # Don't fail the whole task if movement tracking fails

        logger.info(
            "task_completed",
            task="poll_free_bike_status",
            bikes_processed=len(bike_feed.data.bikes),
            bikes_updated=updated_count
        )

        return {
            "status": "success",
            "bikes_processed": len(bike_feed.data.bikes),
            "bikes_updated": updated_count
        }

    except Exception as exc:
        logger.error("task_failed", task="poll_free_bike_status", error=str(exc), exc_info=True)
        db.rollback()
        raise self.retry(exc=exc, countdown=60)

    finally:
        db.close()


@celery_app.task(name="poll_station_information", bind=True, max_retries=3)
def poll_station_information(self):
    """
    Poll station_information.json every 12 hours.

    Fetches static station information and updates station table.
    """
    logger.info("task_started", task="poll_station_information")

    db = SessionLocal()

    try:
        # Fetch station information from GBFS API
        import asyncio
        poller = GBFSPollerService()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            info_feed = loop.run_until_complete(poller.fetch_station_information())
        finally:
            loop.run_until_complete(poller.close())
            loop.close()

        # Update stations in database
        repo = StationRepository(db)
        updated_count = 0

        for station_info in info_feed.data.stations:
            try:
                station_data = StationCreate(
                    id=station_info.station_id,
                    name=station_info.name,
                    lat=station_info.lat,
                    lon=station_info.lon,
                    address=station_info.address,
                    capacity=station_info.capacity,
                    region_id=station_info.region_id,
                    rental_methods=station_info.rental_methods,
                    is_virtual_station=station_info.is_virtual_station or False
                )

                # Upsert station (idempotent)
                asyncio.run(repo.upsert(station_data))
                updated_count += 1
            except Exception as e:
                logger.error("station_update_failed", station_id=station_info.station_id, error=str(e))

        db.commit()

        logger.info(
            "task_completed",
            task="poll_station_information",
            stations_processed=len(info_feed.data.stations),
            stations_updated=updated_count
        )

        return {
            "status": "success",
            "stations_processed": len(info_feed.data.stations),
            "stations_updated": updated_count
        }

    except Exception as exc:
        logger.error("task_failed", task="poll_station_information", error=str(exc), exc_info=True)
        db.rollback()
        raise self.retry(exc=exc, countdown=300)

    finally:
        db.close()