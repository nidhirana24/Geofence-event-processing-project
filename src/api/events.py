# API router for recieving LocationEvents (POST /v1/events).

from fastapi import APIRouter, HTTPException
from src.models.schemas import LocationEvent
from src.services.geofence_service import geofence_service
from starlette.responses import JSONResponse
from datetime import datetime, timezone
import logging

router = APIRouter()


@router.post("/events", status_code=200)
async def post_location_event(event: LocationEvent):
    """Recieves a new vehicle location event, processes it for geofence transitions and updates the vehicle state."""
    try:
        # Pydantic validation handles coordinate range, field presence, & timestamp

        # calling geofence processing logic
        geofence_service.process_event(event)

        # Return success response
        response = {
            "status": "accepted",
            "vehicle_id": event.vehicle_id,
            "recieved_at": datetime.now(timezone.utc).isoformat(),
        }
        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        logger = logging.getLogger()
        # Catch unexpected errors
        logger.error(
            f"Error processing event for {event.vehicle_id}:{e}", exc_info=True
        )

        # 400 for validation errors (handled by pydantic/FastAPI automatically)
        # 500 for service errors
        raise HTTPException(status_code=500, detail="Internal Server Error")
