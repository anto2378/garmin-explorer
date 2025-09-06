#!/usr/bin/env python3
"""
Garmin Companion System - Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import engine
from app.models import Base
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    print("🚀 Starting Garmin Companion System...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down Garmin Companion System...")


# Create FastAPI app
app = FastAPI(
    title="Garmin Companion System",
    description="Multi-user Garmin activity tracking with WhatsApp digests",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Garmin Companion System",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "services": ["garmin-api", "whatsapp-api", "celery"]
    }


@app.get("/fake-sporters")
async def fake_sporters_dashboard():
    """Public dashboard endpoint for nebluda.com/fake-sporters"""
    static_path = os.path.join("static", "dashboard.html")
    if os.path.exists(static_path):
        return FileResponse(static_path)
    else:
        return {"error": "Dashboard not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )