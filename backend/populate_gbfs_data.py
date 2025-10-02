"""Manually populate database with real GBFS data."""

import asyncio
from app.services.gbfs_poller import GBFSPollerService
from app.database import AsyncSessionLocal
from app.repositories import StationRepository, BikeRepository
from app.schemas.station import StationCreate
from datetime import datetime
import structlog

logger = structlog.get_logger()


async def populate_stations():
    """Fetch and populate all stations from GBFS API."""
    poller = GBFSPollerService()

    async with AsyncSessionLocal() as db:
        try:
            # Fetch station information
            logger.info("Fetching station information from GBFS API...")
            info_feed = await poller.fetch_station_information()

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

                    await repo.upsert(station_data)
                    updated_count += 1
                    logger.info(f"Upserted station: {station_info.station_id} - {station_info.name}")
                except Exception as e:
                    logger.error(f"Failed to upsert station {station_info.station_id}: {e}")

            await db.commit()
            logger.info(f"Successfully populated {updated_count} stations from GBFS API")

            # Now fetch and store station status snapshots
            logger.info("Fetching station status from GBFS API...")
            status_feed = await poller.fetch_station_status()
            snapshot_time = datetime.fromtimestamp(status_feed.last_updated)

            stored_count = 0
            for station_status in status_feed.data.stations:
                try:
                    await repo.store_status_snapshot(
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
                    )
                    stored_count += 1
                    logger.info(f"Stored status for station: {station_status.station_id}")
                except Exception as e:
                    logger.error(f"Failed to store status for station {station_status.station_id}: {e}")

            await db.commit()
            logger.info(f"Successfully stored {stored_count} station status snapshots")

        finally:
            await poller.close()


async def populate_bikes():
    """Fetch and populate all bikes from GBFS API."""
    poller = GBFSPollerService()

    async with AsyncSessionLocal() as db:
        try:
            # Fetch bike status
            logger.info("Fetching bike status from GBFS API...")
            bike_feed = await poller.fetch_free_bike_status()

            # Update bikes in database
            repo = BikeRepository(db)
            updated_count = 0

            for bike in bike_feed.data.bikes:
                try:
                    # Handle empty string station_id - should be None
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

                    await repo.upsert(bike_data)
                    updated_count += 1
                    logger.info(f"Upserted bike: {bike.bike_id}")
                except Exception as e:
                    logger.error(f"Failed to upsert bike {bike.bike_id}: {e}")
                    # Don't let one bike failure stop the whole import
                    await db.rollback()

            await db.commit()
            logger.info(f"Successfully populated {updated_count} bikes from GBFS API")

        finally:
            await poller.close()


async def main():
    """Main function to populate both stations and bikes."""
    logger.info("=" * 50)
    logger.info("Starting GBFS data population")
    logger.info("=" * 50)

    await populate_stations()
    await populate_bikes()

    logger.info("=" * 50)
    logger.info("GBFS data population completed!")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
