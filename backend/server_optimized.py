import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn

# Import optimization modules
from cache import cache_manager, cached_user_data, invalidate_user_cache
from database import db_manager, get_db
from rate_limiter import rate_limiter, check_rate_limit
from monitoring import monitor
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Observer AI Backend with optimizations...")
    
    # Initialize database connection
    await db_manager.connect()
    
    # Initialize cache
    await cache_manager.connect()
    
    # Start monitoring
    await monitor.start_monitoring()
    
    logger.info("✅ All services initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down services...")
    if db_manager.client:
        db_manager.client.close()
    
    logger.info("✅ Shutdown complete")

# Create FastAPI app with optimizations
app = FastAPI(
    title="Observer AI API - Optimized",
    description="High-performance multi-agent simulation API",
    version="2.0.0",
    lifespan=lifespan
)

# Security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # Configure for production

# CORS with optimization
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Rate limiting middleware
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Apply rate limiting based on endpoint type"""
    start_time = time.time()
    
    # Get client identifier (IP address or user ID)
    client_id = request.client.host
    if hasattr(request.state, 'user') and request.state.user:
        client_id = f"user_{request.state.user.id}"
    
    # Determine rate limit type
    path = request.url.path
    if path.startswith('/api/auth/'):
        limit_type = 'auth'
    elif path.startswith('/api/upload/'):
        limit_type = 'upload'
    elif any(method in path for method in ['/create', '/agents', '/documents']):
        limit_type = 'create'
    elif path.startswith('/api/admin/'):
        limit_type = 'admin'
    else:
        limit_type = 'api'
    
    # Check rate limit
    allowed, info = await check_rate_limit(client_id, limit_type)
    
    if not allowed:
        # Add rate limit headers
        response = HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {info['reset_time'] - int(time.time())} seconds."
        )
        response.headers = {
            "X-RateLimit-Limit": str(info['limit']),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(info['reset_time']),
            "Retry-After": str(info['reset_time'] - int(time.time()))
        }
        raise response
    
    # Process request
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    monitor.record_request(
        method=request.method,
        endpoint=path,
        status_code=response.status_code,
        duration=duration
    )
    
    # Add rate limit headers to successful responses
    response.headers["X-RateLimit-Limit"] = str(info['limit'])
    response.headers["X-RateLimit-Remaining"] = str(info.get('remaining', 0))
    response.headers["X-RateLimit-Reset"] = str(info['reset_time'])
    
    return response

# Performance monitoring middleware
@app.middleware("http")
async def performance_monitoring_middleware(request: Request, call_next):
    """Monitor request performance"""
    start_time = time.time()
    
    # Increment active requests
    monitor.active_requests += 1
    
    try:
        response = await call_next(request)
        return response
    finally:
        # Decrement active requests
        monitor.active_requests -= 1
        
        # Log slow requests
        duration = time.time() - start_time
        if duration > 1.0:  # Log requests taking more than 1 second
            logger.warning(
                "Slow request detected",
                path=request.url.path,
                method=request.method,
                duration=duration
            )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    db_healthy = await db_manager.health_check()
    cache_healthy = cache_manager.connected
    
    status = "healthy" if db_healthy and cache_healthy else "unhealthy"
    
    return {
        "status": status,
        "database": "healthy" if db_healthy else "unhealthy",
        "cache": "healthy" if cache_healthy else "unhealthy",
        "timestamp": time.time()
    }

# Performance metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get performance metrics"""
    stats = monitor.get_performance_stats()
    
    # Add database connection stats
    db_stats = await db_manager.get_connection_stats()
    if db_stats:
        stats["database"] = db_stats
    
    return stats

# Import and include your existing API routes
# Note: You'll need to modify your existing endpoints to use the new caching and database systems

if __name__ == "__main__":
    # Production server configuration
    uvicorn.run(
        "server_optimized:app",
        host="0.0.0.0",
        port=8001,
        workers=4,  # Adjust based on CPU cores
        loop="uvloop",  # Faster event loop
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    )