# app/main.py
"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.core.database import ensure_db_initialized
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting application...")
    
    # Ensure attachments directory exists
    Path(settings.attachments_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize database
    await ensure_db_initialized()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


app = FastAPI(
    title="Integracao Centauro API",
    description="API for shipment and CTe management",
    version="2.0.0",
    lifespan=lifespan,
)

# Serve uploaded attachments
app.mount(
    settings.attachment_base_url,
    StaticFiles(directory=settings.attachments_dir),
    name="attachments",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes (async, English names only)
from app.api.routes import api_router

# Register API routes under /api/v2
app.include_router(api_router, prefix="/api/v2")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}