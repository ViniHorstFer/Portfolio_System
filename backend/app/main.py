"""
Fund Analytics Platform - FastAPI Backend
Main application entry point.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.dependencies import data_cache
from app.core import load_all_data
from app.routers import (
    funds_router,
    risk_router,
    portfolio_router,
    benchmarks_router,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# APPLICATION LIFESPAN
# ═══════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Loads data on startup and cleans up on shutdown.
    """
    # Startup
    logger.info("Starting Fund Analytics Platform API...")
    
    # Load all data
    try:
        logger.info("Loading fund data...")
        data = await load_all_data()
        
        if data['fund_metrics'] is not None:
            logger.info(f"Loaded fund_metrics: {len(data['fund_metrics'])} funds")
        else:
            logger.warning("Failed to load fund_metrics")
        
        if data['fund_details'] is not None:
            logger.info(f"Loaded fund_details: {len(data['fund_details'])} records")
        else:
            logger.warning("Failed to load fund_details")
        
        if data['benchmarks'] is not None:
            logger.info(f"Loaded benchmarks: {list(data['benchmarks'].columns)}")
        else:
            logger.warning("Failed to load benchmarks")
            
    except Exception as e:
        logger.error(f"Error loading data: {e}")
    
    logger.info("API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Fund Analytics Platform API...")
    data_cache.clear()
    logger.info("Cleanup complete")


# ═══════════════════════════════════════════════════════════════════════════════
# APPLICATION SETUP
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Professional Fund Analytics Platform API",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTERS
# ═══════════════════════════════════════════════════════════════════════════════

app.include_router(funds_router, prefix=settings.api_prefix)
app.include_router(risk_router, prefix=settings.api_prefix)
app.include_router(portfolio_router, prefix=settings.api_prefix)
app.include_router(benchmarks_router, prefix=settings.api_prefix)


# ═══════════════════════════════════════════════════════════════════════════════
# ROOT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "data_loaded": data_cache.is_loaded(),
        "fund_metrics_loaded": data_cache.fund_metrics is not None,
        "fund_details_loaded": data_cache.fund_details is not None,
        "benchmarks_loaded": data_cache.benchmarks is not None,
    }


@app.post("/reload-data")
async def reload_data():
    """Force reload all data from sources."""
    try:
        data_cache.clear()
        data = await load_all_data()
        
        return {
            "success": True,
            "fund_metrics_loaded": data['fund_metrics'] is not None,
            "fund_details_loaded": data['fund_details'] is not None,
            "benchmarks_loaded": data['benchmarks'] is not None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "success": False,
        "error": str(exc),
        "detail": "An unexpected error occurred",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# RUN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
