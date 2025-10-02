"""GBFS API polling service for fetching and validating bike share data."""

from typing import Optional
from datetime import datetime
import httpx
import structlog
from redis import asyncio as aioredis

from app.config import settings
from app.schemas.gbfs import (
    StationInformationFeed,
    StationStatusFeed,
    FreeBikeStatusFeed,
    SystemInformationFeed,
)

logger = structlog.get_logger()


class GBFSPollerService:
    """
    Service responsible for polling GBFS API endpoints.

    Handles:
    - Fetching data from GBFS API
    - Validating responses with Pydantic schemas
    - Error handling and retries
    - Caching in Redis
    """

    def __init__(self):
        """Initialize GBFS poller service."""
        self.base_url = settings.GBFS_BASE_URL.rstrip("/")
        self.timeout = settings.GBFS_TIMEOUT
        self.redis_client: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis client."""
        if not self.redis_client:
            self.redis_client = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis_client

    async def _fetch_endpoint(self, endpoint: str) -> dict:
        """
        Fetch data from a GBFS endpoint.

        Args:
            endpoint: GBFS endpoint name (e.g., 'station_status.json')

        Returns:
            dict: Raw JSON response

        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{self.base_url}/{endpoint}"

        logger.info("gbfs_fetch_start", endpoint=endpoint, url=url)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

            logger.info(
                "gbfs_fetch_success",
                endpoint=endpoint,
                last_updated=data.get("last_updated"),
                ttl=data.get("ttl")
            )

            return data

        except httpx.HTTPError as e:
            logger.error(
                "gbfs_fetch_error",
                endpoint=endpoint,
                error=str(e),
                exc_info=True
            )
            raise

    async def fetch_station_information(self) -> StationInformationFeed:
        """
        Fetch and validate station_information.json feed.

        Returns:
            StationInformationFeed: Validated station information

        Raises:
            ValidationError: If response doesn't match schema
        """
        data = await self._fetch_endpoint("station_information.json")
        validated = StationInformationFeed.model_validate(data)

        logger.info(
            "gbfs_station_info_validated",
            num_stations=len(validated.data.stations)
        )

        return validated

    async def fetch_station_status(self) -> StationStatusFeed:
        """
        Fetch and validate station_status.json feed.

        Returns:
            StationStatusFeed: Validated station status

        Raises:
            ValidationError: If response doesn't match schema
        """
        data = await self._fetch_endpoint("station_status.json")
        validated = StationStatusFeed.model_validate(data)

        logger.info(
            "gbfs_station_status_validated",
            num_stations=len(validated.data.stations)
        )

        # Cache in Redis
        await self._cache_station_status(validated)

        return validated

    async def fetch_free_bike_status(self) -> FreeBikeStatusFeed:
        """
        Fetch and validate free_bike_status.json feed.

        Returns:
            FreeBikeStatusFeed: Validated free bike status

        Raises:
            ValidationError: If response doesn't match schema
        """
        data = await self._fetch_endpoint("free_bike_status.json")
        validated = FreeBikeStatusFeed.model_validate(data)

        logger.info(
            "gbfs_bike_status_validated",
            num_bikes=len(validated.data.bikes)
        )

        return validated

    async def fetch_system_information(self) -> SystemInformationFeed:
        """
        Fetch and validate system_information.json feed.

        Returns:
            SystemInformationFeed: Validated system information

        Raises:
            ValidationError: If response doesn't match schema
        """
        data = await self._fetch_endpoint("system_information.json")
        validated = SystemInformationFeed.model_validate(data)

        logger.info(
            "gbfs_system_info_validated",
            system_id=validated.data.system_id,
            system_name=validated.data.name
        )

        return validated

    async def _cache_station_status(self, feed: StationStatusFeed) -> None:
        """
        Cache station status in Redis for fast access.

        Args:
            feed: Validated station status feed
        """
        redis = await self._get_redis()
        ttl = feed.ttl or settings.REDIS_CACHE_TTL

        for station in feed.data.stations:
            cache_key = f"station:{station.station_id}:status"
            cache_value = station.model_dump_json()

            await redis.setex(
                cache_key,
                ttl,
                cache_value
            )

        logger.debug(
            "gbfs_status_cached",
            num_stations=len(feed.data.stations),
            ttl=ttl
        )

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()