import time
import psutil
import asyncio
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from typing import Dict, Any
import structlog

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
ACTIVE_CONNECTIONS = Gauge('active_database_connections', 'Active database connections')
CACHE_HITS = Counter('cache_hits_total', 'Cache hits', ['operation'])
CACHE_MISSES = Counter('cache_misses_total', 'Cache misses', ['operation'])
SYSTEM_CPU = Gauge('system_cpu_percent', 'System CPU usage')
SYSTEM_MEMORY = Gauge('system_memory_percent', 'System memory usage')
ACTIVE_USERS = Gauge('active_users_count', 'Number of active users')

# Structured logging
logger = structlog.get_logger()

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.active_requests = 0
        
    async def start_monitoring(self):
        """Start background monitoring tasks"""
        # Start Prometheus metrics server
        start_http_server(8000)
        
        # Start system metrics collection
        asyncio.create_task(self._collect_system_metrics())
        
        logger.info("Performance monitoring started", port=8000)
    
    async def _collect_system_metrics(self):
        """Collect system metrics periodically"""
        while True:
            try:
                # CPU and memory usage
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                SYSTEM_CPU.set(cpu_percent)
                SYSTEM_MEMORY.set(memory.percent)
                
                # Log critical metrics
                if cpu_percent > 80:
                    logger.warning("High CPU usage detected", cpu_percent=cpu_percent)
                
                if memory.percent > 80:
                    logger.warning("High memory usage detected", memory_percent=memory.percent)
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                logger.error("Error collecting system metrics", error=str(e))
                await asyncio.sleep(60)
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record request metrics"""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        
        self.request_count += 1
        if status_code >= 400:
            self.error_count += 1
    
    def record_cache_hit(self, operation: str):
        """Record cache hit"""
        CACHE_HITS.labels(operation=operation).inc()
    
    def record_cache_miss(self, operation: str):
        """Record cache miss"""
        CACHE_MISSES.labels(operation=operation).inc()
    
    def set_active_users(self, count: int):
        """Update active users count"""
        ACTIVE_USERS.set(count)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        uptime = time.time() - self.start_time
        
        return {
            "uptime_seconds": uptime,
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
        }

# Global monitor instance
monitor = PerformanceMonitor()