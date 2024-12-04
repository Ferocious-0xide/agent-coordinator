import logging
from typing import Any, Dict, List, Optional, Union
import json
import aioredis
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client wrapper with common operations"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.redis = None
        self._connect()

    async def _connect(self):
        """Initialize Redis connection"""
        try:
            self.redis = await aioredis.from_url(
                f"redis://{self.config['redis']['host']}:{self.config['redis']['port']}",
                password=self.config['redis']['password'],
                db=self.config['redis']['db'],
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set key with optional expiration"""
        try:
            value_str = json.dumps(value)
            await self.redis.set(key, value_str, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Get value for key"""
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """Delete key"""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking existence of key {key}: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration"""
        try:
            return await self.redis.expire(key, seconds)
        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {e}")
            return False

    async def publish(self, channel: str, message: Any) -> bool:
        """Publish message to channel"""
        try:
            message_str = json.dumps(message)
            await self.redis.publish(channel, message_str)
            return True
        except Exception as e:
            logger.error(f"Error publishing to channel {channel}: {e}")
            return False

    async def subscribe(self, channel: str):
        """Subscribe to channel"""
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(channel)
            return pubsub
        except Exception as e:
            logger.error(f"Error subscribing to channel {channel}: {e}")
            raise

    async def set_hash(self, key: str, mapping: Dict) -> bool:
        """Set hash fields"""
        try:
            mapping_str = {k: json.dumps(v) for k, v in mapping.items()}
            await self.redis.hset(key, mapping=mapping_str)
            return True
        except Exception as e:
            logger.error(f"Error setting hash {key}: {e}")
            return False

    async def get_hash(self, key: str) -> Dict:
        """Get all hash fields"""
        try:
            result = await self.redis.hgetall(key)
            return {k: json.loads(v) for k, v in result.items()}
        except Exception as e:
            logger.error(f"Error getting hash {key}: {e}")
            return {}

    async def add_to_set(self, key: str, *values: List[Any]) -> bool:
        """Add values to set"""
        try:
            values_str = [json.dumps(v) for v in values]
            await self.redis.sadd(key, *values_str)
            return True
        except Exception as e:
            logger.error(f"Error adding to set {key}: {e}")
            return False

    async def get_set_members(self, key: str) -> List[Any]:
        """Get all set members"""
        try:
            result = await self.redis.smembers(key)
            return [json.loads(v) for v in result]
        except Exception as e:
            logger.error(f"Error getting set members {key}: {e}")
            return []