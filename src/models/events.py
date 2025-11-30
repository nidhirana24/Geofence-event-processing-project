#Models for internally generated events,such as zone transition.
from pydantic import BaseModel
from typing import Optional,List
from datetime import datetime

#Processes my incoming location event
class TransitionEvent(BaseModel):
    """Represents a confirmed entry into or exit from a geofence zone."""
    type: str="zone_transition"
    vehicle_id:str
    from_zone_id:Optional[str]
    to_zone_id: Optional[str]
    timestamp:datetime
    location:dict #"lon":floar,"lat":float}
    meta:dict={"confidence": "low_time_default"} #Placeholder for future confidence metrics.