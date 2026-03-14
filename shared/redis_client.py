"""
Redis client wrapper for SEO Automation Platform.
Supports pub/sub for pipeline events and caching.
"""
import os
import json
import logging
from typing import Any, Callable, Optional, AsyncGenerator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Pipeline event channels
CHANNEL_KEYWORDS_DISCOVERED = "seo:keywords:discovered"
CHANNEL_COMPETITORS_ANALYZED = "seo:competitors:analyzed"
CHANNEL_CONTENT_GENERATED = "seo:content:generated"
CHANNEL_SEO_OPTIMIZED = "seo:optimized"
CHANNEL_CONTENT_PUBLISHED = "seo:published"
CHANNEL_ANALYTICS_UPDATED = "seo:analytics:updated"
CHANNEL_PIPELINE_STATUS = "seo:pipeline:status"


class RedisClient:
    """Async Redis client wrapper with pub/sub support."""

    def __init__(self, url: str = REDIS_URL):
        self.url = url
        self._client: Optional[Redis] = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        self._client = await aioredis.from_url(
            self.url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        logger.info(f"Connected to Redis at {self.url}")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Disconnected from Redis")

    @property
    def client(self) -> Redis:
        if self._client is None:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client

    # ==========================================================================
    # Basic operations
    # ==========================================================================

    async def get(self, key: str) -> Optional[str]:
        """Get a value by key."""
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a key-value pair with optional TTL (seconds)."""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key."""
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False

    async def get_json(self, key: str) -> Optional[Any]:
        """Get a JSON value by key."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a JSON value."""
        return await self.set(key, json.dumps(value), ttl)

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        try:
            return bool(await self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False

    async def incr(self, key: str) -> int:
        """Increment a counter."""
        try:
            return await self.client.incr(key)
        except Exception as e:
            logger.error(f"Redis INCR error for key {key}: {e}")
            return 0

    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to a list."""
        try:
            serialized = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in values]
            return await self.client.lpush(key, *serialized)
        except Exception as e:
            logger.error(f"Redis LPUSH error for key {key}: {e}")
            return 0

    async def lrange(self, key: str, start: int = 0, end: int = -1) -> list:
        """Get a range from a list."""
        try:
            values = await self.client.lrange(key, start, end)
            result = []
            for v in values:
                try:
                    result.append(json.loads(v))
                except (json.JSONDecodeError, TypeError):
                    result.append(v)
            return result
        except Exception as e:
            logger.error(f"Redis LRANGE error for key {key}: {e}")
            return []

    # ==========================================================================
    # Pub/Sub
    # ==========================================================================

    async def publish(self, channel: str, message: Any) -> int:
        """Publish a message to a channel."""
        try:
            if isinstance(message, (dict, list)):
                message = json.dumps(message)
            count = await self.client.publish(channel, message)
            logger.debug(f"Published to {channel}, {count} subscribers received")
            return count
        except Exception as e:
            logger.error(f"Redis PUBLISH error on channel {channel}: {e}")
            return 0

    async def subscribe(self, channel: str, callback: Callable) -> None:
        """Subscribe to a channel and call callback for each message."""
        pubsub = self.client.pubsub()
        await pubsub.subscribe(channel)
        logger.info(f"Subscribed to channel: {channel}")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    try:
                        data = json.loads(data)
                    except (json.JSONDecodeError, TypeError):
                        pass
                    await callback(data)
        except Exception as e:
            logger.error(f"Error in subscription to {channel}: {e}")
        finally:
            await pubsub.unsubscribe(channel)

    # ==========================================================================
    # Pipeline event helpers
    # ==========================================================================

    async def emit_pipeline_event(self, stage: str, status: str, data: dict = None) -> None:
        """Emit a pipeline status event."""
        event = {
            "stage": stage,
            "status": status,
            "data": data or {},
        }
        await self.publish(CHANNEL_PIPELINE_STATUS, event)
        logger.info(f"Pipeline event: {stage} -> {status}")

    async def cache_keywords(self, keywords: list, ttl: int = 3600) -> None:
        """Cache discovered keywords."""
        await self.set_json("seo:cache:keywords", keywords, ttl)

    async def get_cached_keywords(self) -> Optional[list]:
        """Get cached keywords."""
        return await self.get_json("seo:cache:keywords")

    async def cache_competitor_analysis(self, competitor: str, data: dict, ttl: int = 86400) -> None:
        """Cache competitor analysis results."""
        key = f"seo:cache:competitor:{competitor}"
        await self.set_json(key, data, ttl)

    async def get_cached_competitor_analysis(self, competitor: str) -> Optional[dict]:
        """Get cached competitor analysis."""
        key = f"seo:cache:competitor:{competitor}"
        return await self.get_json(key)

    async def health_check(self) -> bool:
        """Check Redis connectivity."""
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global instance
redis_client = RedisClient()


@asynccontextmanager
async def get_redis() -> AsyncGenerator[RedisClient, None]:
    """Context manager for Redis client."""
    client = RedisClient()
    await client.connect()
    try:
        yield client
    finally:
        await client.disconnect()
