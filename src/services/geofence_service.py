#core geofence logic: zone loading, point-in polygon checks, and state transitions. Implements debounce logic and handles out-of-order events.
import json
from typing import List,Optional,Dict
from datetime import datetime,timezone,timedelta
import logging
import os

from shapely.geometry import Point,box
from src.models.schemas import ZonePolygon,LocationEvent,ZoneStatus
from src.models.events import TransitionEvent
from src.storage.memory_store import memory_store,INACTIVE_TTL
 
logger=logging.getLogger(__name__)

#configuration
GEOFENCE_CONFIG ={
    "DEBOUNCE_TYPE":"CONSECUTIVE", #OR DWELL_TIME
    "CONSECUTIVE_COUNT":2, #N consecutive events in new zone
    "DWELL_TIME_SECONDS":10, #Minimum time in new zone
    "OUT_OF_ORDER_TOLERANCE_S":5 #Ignore events older than last_seen_at - tolerance
}

class GeofenceService:
    #Manages geofence definitions,permance checks and handles state transitions.

    #Storing zones,keyed by zone_id, pre-processed with shapely polygon
    _zones: Dict[str,ZonePolygon]={}

    def init_zones(self,config_path: str="zones.json"):
        #Loads and pre-processes zones from configuration file.

        if not os.path.exists(config_path):
            logger.error(f"Zone configuration file not found at: {config_path}")
            return
        
        try:
            with open(config_path,'r') as f:
                raw_zones=json.load(f)

            self._zones={}
            for raw_zone in raw_zones:
                zone= ZonePolygon(**raw_zone)
                #pre-calculating shapely object and bbox

                zone.get_shapely_polygon()
                zone.get_bbox()
                self._zones[zone.zone_id]=zone
            
            logger.info(f"Loaded {len(self._zones)} geofence zones from {config_path}.")
        except Exception as e:
            logger.error(f"Failed to load or process zones: {e}")
    
    def _find_containing_zone(self,point:Point)-> Optional[ZonePolygon]:
        #Finds highest priority zone containing given point. Uses bounding box for fast rejection before full polygon check.

        candidate_zones:List[ZonePolygon]=[]

        #1. Bounding box quick reject -> pointing coordinates in (lon,lat) for comparison with bbox(minx,miny,maxx,maxy)
        lon,lat=point.x,point.y

        for zone in self._zones.values():
            min_lon,min_lat,max_lon,max_lat=zone.get_bbox()

            #if point is inside bbox
            if min_lon <= lon <=max_lon and min_lat<= lat<= max_lat:
                candidate_zones.append(zone)

        if not candidate_zones:
            return None
        
        #2. Point-in-polygon check -> filtering for zones that actually contain the points
        containing_zones =[zone for zone in candidate_zones if zone.get_shapely_polygon().contains(point) or zone.get_shapely_polygon().boundary.contains(point)]

        if not containing_zones:
            return None
        
        #3. Priority Resolution (Highest priority wins) -> Sorting by priority (descending) and will return first one
        containing_zones.sort(key=lambda z:z.priority,reverse=True)
        return containing_zones[0]
    
    def _process_transition(self,event:LocationEvent,prev_status:ZoneStatus,detected_zone_id: Optional[str])-> Optional[TransitionEvent]:
        #handles state transition logic with debounce. Returns TransitionEvent if confirmed transition occurs, else None

        vehicle_id=event.vehicle_id
        current_ts=event.timestamp
        current_zoneid=prev_status.current_zone_id

        #case1: No change or staying outside all zones
        if detected_zone_id==current_zoneid:
            #clear debounce state if the vehicle is confirmed in current zone
            prev_status.debounce_candidate_zone=None
            prev_status.debounce_count=0
            prev_status.debounce_first_seen=None
            return None
        
        #Case2: Potential transition (prev!= detected)
        candidate_zone=prev_status.debounce_candidate_zone

        if detected_zone_id!= candidate_zone:
            #new candidate zone or vehicle has moved to a non-candidate zone
            prev_status.debounce_candidate_zone=detected_zone_id
            prev_status.debounce_count=1
            prev_status.debounce_first_seen=current_ts
            return None
        
        #case3: Potential transition (candidate==detected)-> check debounce
        #1. consecutive event debounce
        if GEOFENCE_CONFIG["DEBOUNCE_TYPE"]=="CONSECUTIVE":
            prev_status.debounce_count+=1
            if prev_status.debounce_count<GEOFENCE_CONFIG["CONSECUTIVE_COUNT"]:
                return None #not enough consecutive events yet
            
        #2. dwell time debounce
        elif GEOFENCE_CONFIG["DEBOUNCE_TYPE"]=="DWELL_TIME":
            dwell_time=current_ts-prev_status.debounce_first_seen
            if dwell_time.total_seconds() < GEOFENCE_CONFIG["DWELL_TIME_SECONDS"]:
                #not enough dwell time yet
                return None
            
        #3. Confirmed Transition
        #create transition event
        transition= TransitionEvent(
            vehicle_id=vehicle_id,
            from_zone_id=current_zoneid,
            to_zone_id=detected_zone_id,
            timestamp=current_ts,
            location={"lon":event.longitude,"lat":event.latitude}
        )

        #Update vehicle state
        prev_status.current_zone_id=detected_zone_id

        #reset entered_at only if entering a zone i.e. detected_zone_id is not None

        if detected_zone_id:
            prev_status.entered_at=current_ts
        else:
            prev_status.entered_at=None

        #Clear debounce state
        prev_status.debounce_candidate_zone=None
        prev_status.debounce_count=0
        prev_status.debounce_first_seen=None

        logger.info(f"Confirmed transiton for {vehicle_id}: {transition.from_zone_id}-> {transition.to_zone_id}")
        return transition
    
    def process_event(self,event:LocationEvent)-> Optional[TransitionEvent]:
        #Main entry point for proceswsing a location event. Returns a transitionevent if a zone change is confirmed and passes debounce.

        vehicle_id=event.vehicle_id

        #1. get current vehicle status
        prev_status=memory_store.get_status(vehicle_id)
        if not prev_status:
            prev_status=ZoneStatus(vehicle_id=vehicle_id) #for new vehicle, first event establishes the baseline

        #2. OUT-OF-ORDER event check(edge case) 
        if prev_status.last_timestamp:
            time_diff=(prev_status.last_timestamp-event.timestamp).total_seconds()
            if time_diff > GEOFENCE_CONFIG["OUT_OF_ORDER_TOLERANCE_S"]:
                logger.warning(f"Ignored out-of-order event for {vehicle_id}")
                #update last_seen_at if event is ignored but keep state. Here , we ignore the event and do not update any state.
                return None
        
        #3. Geofence Detection
        point=Point(event.longitude,event.latitude)
        detected_zone=self._find_containing_zone(point)
        detected_zone_id=detected_zone.zone_id if detected_zone else None

        #4. State transition & debounce
        transition_event=self._process_transition(event,prev_status,detected_zone_id)

        #5. Updating last_seen/coords/timestamp (always update on valid,in-order event)
        prev_status.last_seen_at=event.timestamp
        prev_status.last_coords=(event.longitude,event.latitude)
        prev_status.last_timestamp=event.timestamp

        #6. Saving the potentially updated status
        memory_store.update_status(vehicle_id,prev_status)

        memory_store.purge_inactive_vehicles()

        #Log the transition 
        if transition_event:
            logger.info(f"TRANSITION_EMITTED: {transition_event.model_dump_json()}")
        return transition_event
    
#global instance
geofence_service=GeofenceService()

