# API router for querying current vehicle zone status (GET /v1/vehicles/{id}/zone)
from fastapi import APIRouter, Path
from src.services.vehicle_service import vehicle_service
from src.models.schemas import VehicleZoneStatus
from starlette.responses import JSONResponse

router = APIRouter()


@router.get("/vehicles/{vehicle_id}/zone", response_model=VehicleZoneStatus)
async def get_vehicle_zone(vehicle_id: str = Path(..., title="The ID of the vehicle")):
    """Retrieves the current geofence zone status for a specified vehicle. Returns current zone null if vehicle is unknown or outside all zones"""

    # service handles retrieving state and formatting the response
    status = vehicle_service.get_zone_status(vehicle_id)

    return status