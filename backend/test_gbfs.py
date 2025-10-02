"""Test script for GBFS API integration."""

import asyncio
import sys
from app.services import GBFSPollerService


async def test_gbfs_connection():
    """Test GBFS API connectivity and data fetching."""

    print("🔄 Testing GBFS API Connection...\n")

    poller = GBFSPollerService()

    try:
        # Test system information
        print("1. Fetching system information...")
        system_info = await poller.fetch_system_information()
        print(f"   ✅ System: {system_info.data.name}")
        print(f"   ✅ System ID: {system_info.data.system_id}")
        print(f"   ✅ Timezone: {system_info.data.timezone}\n")

        # Test station information
        print("2. Fetching station information...")
        station_info = await poller.fetch_station_information()
        print(f"   ✅ Found {len(station_info.data.stations)} stations")
        if station_info.data.stations:
            sample = station_info.data.stations[0]
            print(f"   ✅ Sample station: {sample.name} (ID: {sample.station_id})\n")

        # Test station status
        print("3. Fetching station status...")
        station_status = await poller.fetch_station_status()
        print(f"   ✅ Found status for {len(station_status.data.stations)} stations")
        if station_status.data.stations:
            sample = station_status.data.stations[0]
            print(f"   ✅ Sample: Station {sample.station_id}")
            print(f"      - Bikes available: {sample.num_bikes_available}")
            print(f"      - Docks available: {sample.num_docks_available}\n")

        # Test free bike status
        print("4. Fetching free bike status...")
        try:
            bike_status = await poller.fetch_free_bike_status()
            print(f"   ✅ Found {len(bike_status.data.bikes)} bikes")
            if bike_status.data.bikes:
                sample = bike_status.data.bikes[0]
                print(f"   ✅ Sample bike: {sample.bike_id}")
                print(f"      - Location: ({sample.lat}, {sample.lon})")
                print(f"      - Reserved: {sample.is_reserved}\n")
        except Exception as e:
            print(f"   ⚠️  Free bike status not available or empty: {e}\n")

        print("✅ All GBFS API tests passed!\n")
        return True

    except Exception as e:
        print(f"❌ GBFS API test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await poller.close()


if __name__ == "__main__":
    result = asyncio.run(test_gbfs_connection())
    sys.exit(0 if result else 1)