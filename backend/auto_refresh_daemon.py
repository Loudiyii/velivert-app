"""Daemon pour actualiser automatiquement les données GBFS toutes les 5 minutes."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import structlog

sys.path.insert(0, str(Path(__file__).parent))

from force_refresh_data import refresh_all_data

logger = structlog.get_logger()

REFRESH_INTERVAL_SECONDS = 5 * 60  # 5 minutes


async def run_daemon():
    """Exécute le rafraîchissement des données en boucle."""
    logger.info("🔄 Auto-refresh daemon started", interval_minutes=5)

    while True:
        try:
            logger.info("Starting scheduled refresh...")
            await refresh_all_data()
            logger.info("✅ Refresh completed successfully")
        except Exception as e:
            logger.error(f"❌ Refresh failed: {e}", exc_info=True)

        # Attendre 5 minutes avant le prochain rafraîchissement
        logger.info(f"⏰ Next refresh in {REFRESH_INTERVAL_SECONDS // 60} minutes")
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)


if __name__ == "__main__":
    print("🚀 Starting GBFS Auto-Refresh Daemon (5-minute interval)")
    print("=" * 60)
    asyncio.run(run_daemon())
