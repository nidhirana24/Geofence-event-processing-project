#!/bin/bash
# A simple demo script to showcase the Geofence Service functionality.
# Set the base URL for the service
BASE_URL="http://localhost:8000/v1"
VEHICLE_ID="TX-DEMO-001"

# Function to post an event
post_event() {
  LON=$1
  LAT=$2
  ZONE_NAME=$3
  TIME_OFFSET=$4 # In seconds from start time
  TIMESTAMP=$(date -u -Iseconds -d "@$(($(date +%s) + $TIME_OFFSET))")
  
  echo "--- POST: Vehicle ${VEHICLE_ID} to ${ZONE_NAME} at $TIMESTAMP (Offset: ${TIME_OFFSET}s) ---"
  curl -s -X POST "${BASE_URL}/events" \
    -H "Content-Type: application/json" \
    -d '{
      "vehicle_id": "'"${VEHICLE_ID}"'",
      "latitude": '"${LAT}"',
      "longitude": '"${LON}"',
      "timestamp": "'"${TIMESTAMP}"'"
    }' | jq .
  echo ""
  sleep 1 # Wait one second between events
}

# Function to get the current zone status
get_status() {
  echo "--- GET: Current Zone Status for ${VEHICLE_ID} ---"
  curl -s "${BASE_URL}/vehicles/${VEHICLE_ID}/zone" | jq .
  echo ""
}
#Start Demo
echo "Starting Geofence Service Demo..."
echo "NOTE: This demo assumes uvicorn is running in a separate terminal via:"
echo "      uvicorn src.main:app --reload --port 8000"
echo "--- Zone Coordinates (from zones.json) ---"
echo "  - Downtown: Lon ~77.59, Lat ~12.97 (Priority 50)"
echo "  - Park: Lon ~77.596, Lat ~12.976 (Priority 10, Overlaps Downtown)"
echo "  - Outside: Lon 1.0, Lat 1.0"
echo "--- Debounce is set to N=2 consecutive events to confirm transition ---"

# Initial status check
get_status
# 1. Initial event: Vehicle is OUTSIDE all zones
post_event ${VEHICLE_ID} 1.0 1.0 "OUTSIDE" 0

# 2. Vehicle moves to Downtown (Event 1 in Candidate: Downtown)
DT_LON=77.595
DT_LAT=12.975
post_event ${VEHICLE_ID} ${DT_LON} ${DT_LAT} "DOWNTOWN (Candidate 1)" 1
get_status
# 3. Vehicle stays in Downtown (Event 2 in Candidate: Downtown -> CONFIRM)
# This should trigger the 'Enter' transition event.
post_event ${VEHICLE_ID} 77.594 12.974 "DOWNTOWN (Confirm)" 2
get_status
# 4. Jitter to Park (Event 1 in Candidate: Park) - Park is a lower priority sub-zone
# NOTE: The priority logic will pick Downtown (50) over Park (10) for this event. 
# Let's adjust the coordinates to be squarely in Downtown and outside Park 
DT_LON_ONLY=77.591
DT_LAT_ONLY=12.971

echo "--- Jitter Test (Stay in Downtown: Same as current zone) ---"
post_event ${VEHICLE_ID} ${DT_LON_ONLY} ${DT_LAT_ONLY} "DOWNTOWN (Jitter)" 3
get_status
# 5. Exit to Outside (Event 1 in Candidate: None)
post_event ${VEHICLE_ID} 1.0 1.0 "OUTSIDE (Candidate 1)" 4
get_status
# 6. Stay Outside (Event 2 in Candidate: None -> CONFIRM EXIT)
# This should trigger the 'Exit' transition event.
post_event ${VEHICLE_ID} 1.0 1.0 "OUTSIDE (Confirm Exit)" 5
get_status
echo "Demo complete."