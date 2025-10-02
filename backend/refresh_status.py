"""Refresh station and bike status from GBFS API."""

import asyncio
from app.services.gbfs_poller import GBFSPollerService
from app.database import AsyncSessionLocal
from app.repositories import StationRepository
from datetime import datetime
import structlog

logger = structlog.get_logger()


async def refresh_station_status():
    """Fetch and update station status from GBFS API."""
    poller = GBFSPollerService()

    async with AsyncSessionLocal() as db:
        try:
            logger.info("Fetching station status from GBFS API...")
            status_feed = await poller.fetch_station_status()
            snapshot_time = datetime.fromtimestamp(status_feed.last_updated)

            repo = StationRepository(db)
            stored_count = 0
            total_bikes = 0

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
                    total_bikes += station_status.num_bikes_available
                    logger.info(f"Updated status for station: {station_status.station_id} - {station_status.num_bikes_available} bikes")
                except Exception as e:
                    logger.error(f"Failed to store status for station {station_status.station_id}: {e}")

            await db.commit()
            logger.info(f"Successfully stored {stored_count} station status snapshots")
            logger.info(f"Total bikes available across all stations: {total_bikes}")

        finally:
            await poller.close()


async def main():
    """Main function to refresh status."""
    logger.info("=" * 50)
    logger.info("Refreshing station status from GBFS API")
    logger.info("=" * 50)

    await refresh_station_status()

    logger.info("=" * 50)
    logger.info("Status refresh completed!")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
