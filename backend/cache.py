import redis
import json
import os
from typing import Optional, Any
from datetime import timedelta
import asyncio
import aioredis

class CacheManager:
    def __init__(self):
        self.redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = None
        self.connected = False
    
    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = aioredis.from_url(
                self.redis_url, 
                decode_responses=True,
                max_connections=100
            )
            # Test connection
            await self.redis_client.ping()
            self.connected = True
            print("✅ Redis cache connected successfully")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            self.connected = False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.connected:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL"""
        if not self.connected:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            await self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.connected:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> bool:
        """Invalidate all keys matching pattern"""
        if not self.connected:
            return False
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
            return True
        except Exception as e:
            print(f"Cache invalidate error: {e}")
            return False

# Global cache instance
cache_manager = CacheManager()

def cache_key(prefix: str, user_id: str, suffix: str = "") -> str:
    """Generate standardized cache key"""
    key = f"{prefix}:{user_id}"
    if suffix:
        key += f":{suffix}"
    return key

async def cached_user_data(user_id: str, data_type: str, fetch_func, ttl: int = 300):
    """Generic caching decorator for user data"""
    key = cache_key(data_type, user_id)
    
    # Try to get from cache first
    cached_data = await cache_manager.get(key)
    if cached_data is not None:
        return cached_data
    
    # Fetch from database
    fresh_data = await fetch_func()
    
    # Cache the result
    await cache_manager.set(key, fresh_data, ttl)
    
    return fresh_data

async def invalidate_user_cache(user_id: str, data_types: list = None):
    """Invalidate cache for specific user data types"""
    if data_types is None:
        data_types = ["agents", "conversations", "documents", "saved_agents"]
    
    for data_type in data_types:
        pattern = cache_key(data_type, user_id, "*")
        await cache_manager.invalidate_pattern(pattern)