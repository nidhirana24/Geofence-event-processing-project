#simple in-memory store for vehicle state.
#provides CRUD operations for vehicle status and handles TTL for inactive vehicles.

from typing import Dict,Optional,List
from datetime import datetime,timedelta,timezone
import logging
from src.models.schemas import ZoneStatus
logger = logging.getLogger(__name__)

#config for TTL (time to live)
INACTIVE_TTL=timedelta(minutes=15)

class MemoryStore:
    #In memory storage for vehicles zone status and state.
    #key: vehicle_id (str), value:Zonestatus(dict is used internally)
    _store:Dict[str,dict]={}

    def __init__(self):
        #intialize store
        self._store={}
        logger.info("In-memory store intialized.")

    def get_status(self,vehicle_id:str)->Optional[ZoneStatus]:
        #Retrieves current status for a vehicle.
        data = self._store.get(vehicle_id)
        if data:
            return ZoneStatus(**data)
        return None
    
    def update_status(self,vehicle_id:str,status:ZoneStatus)->None:
        #updates the status for a vehicle
        self._store[vehicle_id]=status.model_dump()

    def purge_inactive_vehicles(self):
        #removes vehicles that haven't been seen for longer than INACTIVE TTL.
        now=datetime.now(timezone.utc)
        keys_to_purge=[]
        for vehicle_id,data in self._store.items():
            last_seen_at=data.get("last_seen_at")
            if last_seen_at and now -last_seen_at>INACTIVE_TTL:
                keys_to_purge.append(vehicle_id)

        for vehicle_id in keys_to_purge:
            del self._store[vehicle_id]
            logger.info(f"Purged inactive vehicle: {vehicle_id}")
        
        if keys_to_purge:
            logger.info(f"Purge complete. Total vehicles purged: {len(keys_to_purge)}")

    def get_all_vehicle_ids(self)-> List[str]:
        #returns a list of all vehicle ids currently in the store.
        return list(self._store.keys())
    
#global instance
memory_store=MemoryStore()