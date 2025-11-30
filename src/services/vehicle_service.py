#manages vehicle state and interacts with the storage layer.

#implements logic like TTL purging and state retrieval.

from typing import Optional,List
from src.models.schemas import VehicleZoneStatus,ZoneStatus,ZoneCurrent
from storage.memory_store import memory_store

class VehicleService:
    #service layer for vehicle state management
    def get_zone_status(self,vehicle_id:str)-> VehicleZoneStatus:
        #Retrives current zone status for a vehicle, formatted for API response.
        status: Optional[ZoneStatus]=memory_store.get_status(vehicle_id)

        response_status = VehicleZoneStatus(
            vehicle_id=vehicle_id,
            current_zone=None,
            last_seen_at=None
        )

        if not status:
            return response_status
        
        response_status.last_seen_at=status.last_seen_at

        if status.current_zone_id and status.entered_at:
            # In a real system, we'd fetch the zone details here. We rely on geofence_service's zone mapping for the 'name' since it's loaded only there.
            # Placeholder for name: In this project, I assume the zone_id is sufficient.
            # For a complete solution, I would inject a ZoneConfigService here.
            zone_name=status.current_zone_id.title()

            response_status.current_zone=ZoneCurrent(
                zone_id=status.current_zone_id,
                name=zone_name,
                entered_at=status.entered_at
            )
        return response_status
    
    def update_vehicle_status(self,vehicle_id:str,new_status:ZoneStatus):
        #updates the vehicle's state in store.
        memory_store.update_status(vehicle_id,new_status)

#global instance
vehicle_service=VehicleService()