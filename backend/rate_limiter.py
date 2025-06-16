import time
import asyncio
from collections import defaultdict
from typing import Dict, Tuple
import os

class RateLimiter:
    def __init__(self):
        # In-memory rate limiting (in production, use Redis)
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = 60  # Clean up old entries every 60 seconds
        self.last_cleanup = time.time()
        
        # Rate limits per endpoint type
        self.limits = {
            'auth': {'requests': 5, 'window': 60},      # 5 requests per minute for auth
            'api': {'requests': 100, 'window': 60},     # 100 requests per minute for API
            'upload': {'requests': 10, 'window': 60},   # 10 uploads per minute
            'create': {'requests': 20, 'window': 60},   # 20 creates per minute
            'admin': {'requests': 200, 'window': 60},   # 200 requests per minute for admin
        }
    
    async def is_allowed(self, identifier: str, limit_type: str = 'api') -> Tuple[bool, dict]:
        """
        Check if request is allowed based on rate limits
        Returns: (allowed: bool, info: dict)
        """
        current_time = time.time()
        
        # Clean up old entries periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            await self._cleanup_old_requests(current_time)
            self.last_cleanup = current_time
        
        # Get rate limit configuration
        config = self.limits.get(limit_type, self.limits['api'])
        window_start = current_time - config['window']
        
        # Filter requests within the current window
        user_requests = self.requests[identifier]
        recent_requests = [req_time for req_time in user_requests if req_time > window_start]
        
        # Update the requests list
        self.requests[identifier] = recent_requests
        
        # Check if limit is exceeded
        if len(recent_requests) >= config['requests']:
            return False, {
                'limit': config['requests'],
                'window': config['window'],
                'current': len(recent_requests),
                'reset_time': int(window_start + config['window'])
            }
        
        # Add current request
        self.requests[identifier].append(current_time)
        
        return True, {
            'limit': config['requests'],
            'window': config['window'],
            'remaining': config['requests'] - len(recent_requests) - 1,
            'reset_time': int(current_time + config['window'])
        }
    
    async def _cleanup_old_requests(self, current_time: float):
        """Remove old request entries to prevent memory leaks"""
        max_window = max(config['window'] for config in self.limits.values())
        cutoff_time = current_time - max_window
        
        for identifier in list(self.requests.keys()):
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier] 
                if req_time > cutoff_time
            ]
            
            # Remove empty entries
            if not self.requests[identifier]:
                del self.requests[identifier]

# Global rate limiter instance
rate_limiter = RateLimiter()

async def check_rate_limit(identifier: str, limit_type: str = 'api'):
    """Convenience function to check rate limits"""
    return await rate_limiter.is_allowed(identifier, limit_type)