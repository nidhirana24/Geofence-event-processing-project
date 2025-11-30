"""Entry point for FastAPI application.Initializes logging and loads geofence zones."""

from fastapi import FastAPI
from src.api import events, vehicles
from src.services.geofence_service import geofence_service
import logging
import sys

# configured logging. Production system will use JSON formatter
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(names)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger("Geofenceserviceapp")

# Initializing FastAPI app
app = FastAPI(
    title="GeoFence Transirion Service",
    version="v1",
    description="Microservices to track vehicle location against geofence zones and detect transitions.",
)

# Include api routers
app.include_router(events.router, prefix="/v1", tags=["Events"])
app.include_router(vehicles.router, prefix="/v1", tags=["Vehicles"])


# Load zones at application startup
@app.lifespan("startup")
def load_zones():
    # loading geofence zones from zones.json and pre-process geometry.
    logger.info("Application startup: Initializing geofence service....")
    geofence_service.init_zones("zones.json")
    logger.info("Geofence service initialization complete.")


@app.get("/", include_in_schema=False)
def read():
    return {
        "message": "Welcome to the Geofence Service v1. See /docs for API documentation."
    }