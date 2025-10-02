"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
import structlog

from app.config import settings
from app.database import init_db
from app.api.endpoints import stations, bikes, analytics, interventions, routes, websocket, auth, route_optimization, bike_flows, multi_technician, data_refresh, movements_analysis

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("application_startup", version=settings.APP_VERSION)
    await init_db()
    logger.info("database_initialized")
    yield
    # Shutdown
    logger.info("application_shutdown")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Plateforme d'analyse et d'optimisation pour Vélivert Saint-Étienne",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with dependency status."""
    from app.database import async_engine
    from redis import asyncio as aioredis

    checks = {
        "api": "ok",
        "database": "unknown",
        "redis": "unknown",
    }

    # Check database
    try:
        async with async_engine.connect() as conn:
            await conn.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        logger.error("health_check_database_failed", error=str(e))

    # Check Redis
    try:
        redis_client = aioredis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"
        logger.error("health_check_redis_failed", error=str(e))

    overall_status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"

    return {
        "status": overall_status,
        "version": settings.APP_VERSION,
        "checks": checks
    }


# Include API routers
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["authentication"]
)

app.include_router(
    stations.router,
    prefix=f"{settings.API_V1_PREFIX}/stations",
    tags=["stations"]
)

app.include_router(
    bikes.router,
    prefix=f"{settings.API_V1_PREFIX}/bikes",
    tags=["bikes"]
)

app.include_router(
    analytics.router,
    prefix=f"{settings.API_V1_PREFIX}/analytics",
    tags=["analytics"]
)

app.include_router(
    interventions.router,
    prefix=f"{settings.API_V1_PREFIX}/interventions",
    tags=["interventions"]
)

app.include_router(
    routes.router,
    prefix=f"{settings.API_V1_PREFIX}/routes",
    tags=["routes"]
)

app.include_router(
    route_optimization.router,
    prefix=f"{settings.API_V1_PREFIX}/route-optimization",
    tags=["route-optimization"]
)

app.include_router(
    bike_flows.router,
    prefix=f"{settings.API_V1_PREFIX}/bike-flows",
    tags=["bike-flows"]
)

app.include_router(
    multi_technician.router,
    prefix=f"{settings.API_V1_PREFIX}/multi-technician",
    tags=["multi-technician"]
)

app.include_router(
    data_refresh.router,
    prefix=f"{settings.API_V1_PREFIX}/data",
    tags=["data-refresh"]
)

app.include_router(
    movements_analysis.router,
    prefix=f"{settings.API_V1_PREFIX}/movements",
    tags=["movements-analysis"]
)

app.include_router(
    websocket.router,
    tags=["websocket"]
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )