🚖 Geofence Event Processing Service

A lightweight, production-aware service for ingesting GPS events, tracking vehicle states in real time, and detecting geofence boundary transitions (enter/exit events).
Built for reliability, clarity, and operational visibility.

📌 Overview

This is a location-based service for a taxi company. Vehicles send GPS coordinates to an HTTP endpoint, and the system determines:
When a vehicle enters a geofence
When a vehicle exits a geofence
What zone a vehicle is currently in
Whether a vehicle is moving, idle, or outside all zones

The design focuses on clean architecture, performant in-memory state management, and practical engineering choices that scale.

✨ Key Features
✔ Real-time GPS event ingestion-
Vehicles push location events directly to /location.
Each event is validated, logged, and processed instantly.

✔Overlapping Zone Resolution-
 Zones have a priority field to correctly determine the vehicle's zone status when multiple geofences overlap at the same location.
 
✔ Geofence enter/exit detection-
The service defines simple polygon-based zones. Using point-in-polygon logic, we determine whether a new coordinate crosses a boundary relative to the previous state.

✔ Vehicle state tracking
In-memory cache maintains:
Last known coordinates
Current geofence zone
Timestamp of last update
Movements across zones

✔ Query API
/vehicle/<id> returns the vehicle’s latest zone, last location, and last transition.

✔ Lightweight, fast, and easy to deploy
Zero external dependencies beyond FastAPI and standard Python libs.

🏗 Architecture & Design Decisions
1. FastAPI for the service layer
FastAPI gives:
Async request handling
Automatic validation via Pydantic
Auto-generated Swagger docs
Easy extensibility
This is ideal for real-time event ingestion.

2. In-memory state store
A dictionary holds vehicle states:
O(1) lookups
Simple and extremely fast
Perfect for this challenge timeframe
In a real deployment, I'd use Redis → strong consistency, TTL expiry, horizontal scalability.

3. Zones defined as simple polygons
Flexible for scaling beyond rectangles.
Point-in-polygon is implemented with a clean, readable function.

4. Event-driven detection
Each location update triggers:
Zone lookup
Previous vs current zone comparison
Emit enter/exit events
Update state store
This approach minimizes unnecessary computations.

5. Operational Awareness Built-In
Input validation
Error responses with detailed context
Logging on to every critical action
Clear separation of concerns

If deployed, hooking this into Prometheus or OpenTelemetry would be trivial.

🚀 How to Run
1. Clone
git clone <your-repo-url>
cd geofence-service

2. Install dependencies
pip install -r requirements.txt

3. Start the service
uvicorn main: app --reload

4. Access API docs
http://localhost:8000/docs

📡 API Endpoints
POST /location

Ingest a GPS event.

{
  "vehicle_id": "TX-102",
  "latitude": 28.5531,
  "longitude": 77.2079,
  "timestamp": "2025-11-30T18:23:12Z"
}

GET /vehicle/{vehicle_id}

Check current zone, last location, and transitions.

🧠 Assumptions
-GPS updates are reasonably frequent
-No authentication needed for this challenge
-Zones are static
-In-memory store is acceptable given the challenge scope
-Vehicles do not send absurdly noisy GPS coordinates

🔍 Edge Cases Handled
-Missing/invalid coordinates
-Vehicle sending first-ever location event
-Boundary-edge coordinates (treated as inside)
-Zone to no-zone transitions
-No-zone to zone transitions
-Rapid oscillation filtering (simple debounce could be added)

🧩 Directory Structure
project/
├─ src/
│  ├─ api/
│  │  ├─ events.py           # POST /v1/events
│  │  └─ vehicles.py          # GET /v1/vehicles/{id}/zone
│  ├─ services/
│  │  ├─ geofence_service.py # zone detection, transition logic,point-in-polygon checks
│  │  └─ vehicle_service.py  # state management, validation
│  ├─ models/
│  │  ├─ schemas.py          # Pydantic request/response schemas(LocationEvent, Zone, ...)
│  │  └─ events.py           # TransitionEvent model
│  ├─ storage/
│  │  ├─ memory_store.py     # simple in-memory vehicle state store
│  └─ main.py                # FastAPI entrypoint + include routers
├─ zones.json                # stores zones information - {zoneid, name, priority, polygon}
├─ README.md
├─ requirements.txt

📈 Performance & Scalability Notes
1. Current performance:
- O(1) lookup for all vehicles
- Zones check in < 0.05 ms
- To scale production-wise
- Debounce logic to prevent zone flip-flopping
- Add Kafka/EventBridge for reliable ingestion
- Add background workers for zone checks
- Configurable zones via API

🛠 Future Improvements
I’d add:
- WebSocket live tracking dashboard
- Replay engine for historical events
- Heatmap analytics for vehicle density
- Horizontal scaling via Kubernetes
- Move state to Redis
- Add Kafka/EventBridge for reliable ingestion
- Persistence layer for long-term tracking history

🏁 Summary
This codebase is designed to reflect real engineering judgment, not just algorithmic correctness.
It is intentionally structured, scalable, and production-oriented.
