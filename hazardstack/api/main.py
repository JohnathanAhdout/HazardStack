"""Main FastAPI application."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.routes import risk, health, events

# Default configuration (load_config disabled for now to avoid dependencies)
config = {
    "grid": {"h3_resolution": 4},
    "time": {"horizons": ["1h", "6h", "12h", "24h"]},
    "serving": {
        "api": {
            "cors_origins": ["*"],
            "host": "0.0.0.0",
            "port": 8000
        }
    }
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    print("🚀 HazardStack API starting up...")
    print(f"   Grid resolution: H3 level {config['grid']['h3_resolution']}")
    print(f"   Horizons: {config['time']['horizons']}")
    print("   Using real USGS earthquake data")

    yield

    # Shutdown
    print("👋 HazardStack API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="HazardStack API",
    description="India Multi-Hazard Nowcasting System (Monsoon + Flood + Earthquake)",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config["serving"]["api"].get("cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(risk.router, prefix="/api/v1", tags=["risk"])
app.include_router(events.router, prefix="/api/v1", tags=["events"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "HazardStack API",
        "version": "0.1.0",
        "description": "India Multi-Hazard Nowcasting System",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=config["serving"]["api"]["host"],
        port=config["serving"]["api"]["port"],
        reload=True,
    )
