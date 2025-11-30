"""Pydantic models for request/response payloads.
Coordinates for polygons are defined as [longitude,latitude](WGS84)"""

from pydantic import BaseModel,Field
from typing import Optional,List
from datetime import datetime,timezone
from shapely.geometry import Polygon,box

#Input models: 
#For POST /v1/events endpoint
class LocationEvent(BaseModel):
    vehicle_id:str=Field(...,min_length=1)
    latitude: float=Field(...,ge=-90.0,le=90.0)
    longitude: float=Field(...,ge=-180.0,le=180.0)
    timestamp: datetime #datetime object will be timezone-aware after validation/processing.
    accuracy_m: Optional[float]=None

    #Custom validator to ensure timestamp is in UTC
    def model_post_init(self,__context):
        #cannonicalized timestamp to timezone-aware UTC
        if self.timestamp.tzinfo is None:
            self.timestamp= self.timestamp.replace(tzinfo=timezone.utc)
        elif self.timestamp.tzinfo != timezone.utc:
            self.timestamp=self.timestamp.astimezone(timezone.utc)

#Zone config models:
class ZonePolygon(BaseModel):
    #Model for defining geofence zone loaded from zones.json
    zone_id: str
    name: str
    polygon: List[List[float]] #defined as List[[longitude,latitude]]
    priority: Optional[int]=0 #higher priority comes first when overlapping
    meta: Optional[dict]=None
    #Internal properties used for geofencing logic (not loaded directly)
    _shapely_polygon: Optional[Polygon]=None
    _bbox: Optional[tuple]=None #(minx,miny,maxx,maxy)

    def get_shapely_polygon(self)->Polygon:
        #Creates and returns shapely polygon objects
        if self._shapely_polygon is None:
            #shapely expects coordinates as (lon,lat) tuples
            coords=[(lon,lat) for lon,lat in self.polygon]

            self._shapely_polygon=Polygon(coords)
        return self._shapely_polygon
    
    def get_bbox(self)->tuple:
        if self.bbox is None:
            poly= self.get_shapely_polygon()
            self._bbox=poly.bounds #Converts (minx,miny,maxx,maxy)->(min_lon,min_lat,max_lon,max_lat)
        return self._bbox

#State and status models
class ZoneCurrent(BaseModel):
    #Inner Model for current zone status in GET response.
    zone_id:str
    name:str
    entered_at:datetime

class VehicleZoneStatus(BaseModel):
    #Ouput model for GET /v1/vehicles/{id}/zone endpoint.
    vehicle_id:str
    current_zone_id: Optional[str]=None
    entered_at: Optional[datetime]=None
    last_seen_at: Optional[datetime]=None
    last_coords: Optional[tuple]=None #(lon,lat)
    last_timestamp: Optional[datetime]=None
    #Debouncing state
    debounce_candidate_zone:Optional[str]=None
    debounce_count:int =0
    debounce_first_seen: Optional[datetime]=None