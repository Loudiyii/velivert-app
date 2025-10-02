"""Test script to manually trigger bike movement tracking."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import AsyncSessionLocal
from app.repositories import BikeRepository
from app.services.bike_movement_tracker import BikeMovementTracker
import structlog

logger = structlog.get_logger()


async def test_movement_tracking():
    """Test the bike movement tracking system."""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting bike movement tracking test...")

            # Get all bikes
            repo = BikeRepository(db)
            bikes = await repo.get_all(limit=1000)
            logger.info(f"Found {len(bikes)} bikes in database")

            # Initialize tracker
            tracker = BikeMovementTracker(db)

            # Run tracking
            result = await tracker.track_movements_and_snapshot(bikes)

            await db.commit()

            logger.info(
                "Tracking completed",
                movements=result['movements_detected'],
                snapshots=result['snapshots_created']
            )

            print(f"\n✅ Tracking test completed successfully!")
            print(f"   - Movements detected: {result['movements_detected']}")
            print(f"   - Snapshots created: {result['snapshots_created']}")

            return result

        except Exception as e:
            await db.rollback()
            logger.error("Tracking test failed", error=str(e), exc_info=True)
            print(f"\n❌ Tracking test failed: {e}")
            raise


if __name__ == "__main__":
    result = asyncio.run(test_movement_tracking())
