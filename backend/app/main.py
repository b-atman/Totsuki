"""
Totsuki - Grocery Optimizer API

Main FastAPI application entry point.
This module creates the app instance, configures middleware,
and registers all routes.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import create_tables, AsyncSessionLocal
from app.api.routes import inventory_router, planner_router
from app.crud.recipe import get_recipe_count, seed_recipes


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Startup:
    - Creates database tables if they don't exist
    - (Later: initialize connections, warm caches, etc.)
    
    Shutdown:
    - Clean up resources
    - (Later: close connections, flush buffers, etc.)
    """
    # === STARTUP ===
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Database: {settings.DATABASE_URL}")
    
    # Create tables (for development - use Alembic migrations in production)
    await create_tables()
    print("Database tables created/verified")
    
    # Seed recipes if database is empty
    async with AsyncSessionLocal() as db:
        recipe_count = await get_recipe_count(db)
        if recipe_count == 0:
            count = await seed_recipes(db)
            await db.commit()
            print(f"Seeded {count} recipes into database")
        else:
            print(f"Found {recipe_count} existing recipes")
    
    yield  # App runs here
    
    # === SHUTDOWN ===
    print(f"Shutting down {settings.APP_NAME}")


# =============================================================================
# Create FastAPI Application
# =============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    description="""
    **Totsuki** - Your intelligent grocery optimizer.
    
    Features:
    - 📦 Pantry inventory management
    - 🍽️ Meal planning with personalized 7-day plans
    - 🧾 Receipt scanning (coming soon)
    - 📊 Budget analytics (coming soon)
    
    Built with FastAPI, SQLAlchemy, and React.
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    # API docs configuration
    docs_url="/docs",           # Swagger UI at /docs
    redoc_url="/redoc",         # ReDoc at /redoc
    openapi_url="/openapi.json",
)


# =============================================================================
# CORS Middleware (allows React frontend to call API)
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# =============================================================================
# Register Routes
# =============================================================================

# Include inventory routes under /api/v1 prefix
app.include_router(
    inventory_router,
    prefix=settings.API_V1_PREFIX,  # /api/v1
)

# Include meal planner routes under /api/v1 prefix
app.include_router(
    planner_router,
    prefix=settings.API_V1_PREFIX,  # /api/v1
)


# =============================================================================
# Root & Health Check Endpoints
# =============================================================================

@app.get(
    "/",
    tags=["Health"],
    summary="API Root",
)
async def root() -> dict:
    """
    API root - returns basic info about the service.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "running",
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
)
async def health_check() -> dict:
    """
    Health check endpoint for monitoring/load balancers.
    
    Returns 200 OK if the service is running.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }
