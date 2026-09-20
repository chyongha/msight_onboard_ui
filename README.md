# msight_onboard_ui

Decodes ICA (Intersection Collision Avoidance), RSA (RoadSideAlert), and
SDSM (Sensor Data Sharing Message) J2735-style messages arriving over UDP
from an MSight roadside unit (RSU). ICA/RSA display a warning banner + a
map pin at the alert location. SDSM is different — real sensor data (a
reporting station plus whatever vehicles/pedestrians/obstacles it
currently sees), not an alert, shown as a live map overlay instead (see
"SDSM (detected objects)" below). Built with Flask + Flask-SocketIO
(backend) and Vue 3 + Vite (frontend).

## Prerequisites

- Python 3 with `pip install -r backend/requirements.txt`
- Node.js with `npm install` run inside `frontend/`
- A `v2xlib.py` (+ `v2xlib.json`) file somewhere on disk — this is the
  pycrate-generated ASN.1 codec `backend/codec/` depends on at runtime.
  It is **not** part of this repo (see `backend/codec/utils.py`); point
  the `PYV2XLIB_VENDOR_DIR` environment variable at whatever folder
  contains it before running the backend or the mock sender.
- `pycrate` (confirmed package/version pinned in `backend/requirements.txt`)
  installed in the same Python environment as the backend.

## Configuration (env vars)

**Backend** (`backend/config.py`):

| Var | Default | What it's for |
|---|---|---|
| `BACKEND_HOST` | `127.0.0.1` | Interface the Flask/Socket.IO server binds to. Use `0.0.0.0` if the frontend runs on a different device than the backend. |
| `BACKEND_PORT` | `5000` | Port for the Flask/Socket.IO server. |
| `UDP_ICA_PORT` / `UDP_RSA_PORT` / `UDP_SDSM_PORT` | `4000` / `4001` / `4002` | Ports the RSU sends ICA / RSA / SDSM to (one listener each). |
| `EGO_UDP_PORT` | `4003` | Port the live ego (this vehicle's own GPS) listener binds to - see `gps_bridge.py` below. |
| `FRONTEND_ORIGIN` | `*` | Origin(s) allowed to open a Socket.IO connection. `*` is fine for local dev; lock this to the real frontend's origin once deployed somewhere with untrusted network access. |

**Frontend** (copy `frontend/.env.example` to `frontend/.env` and edit):

| Var | Default | What it's for |
|---|---|---|
| `VITE_BACKEND_URL` | `http://127.0.0.1:5000` | Where the browser looks for the backend's Socket.IO server. Must match wherever `BACKEND_HOST`/`BACKEND_PORT` above actually end up reachable from. |
| `VITE_DEFAULT_LAT` / `VITE_DEFAULT_LON` | `42.2975` / `-83.7042` | Map center shown before the first alert arrives. Set to your actual intersection. |

`mock_sender.py` reads the UDP ports from the same `backend/config.py` as the
real backend, so they can't drift apart.

## Setup (end to end, from a fresh clone)

1. **Get `v2xlib.py`/`v2xlib.json`** - not part of this repo, needs to come
   from wherever it's normally distributed. Place both files in
   `backend/codec/v2xlib/` (the default `codec/utils.py` looks in), or
   anywhere else + point `PYV2XLIB_VENDOR_DIR` at that folder.
2. **Backend Python env:**
   ```bash
   conda create -n msight_ui python=3.11
   conda activate msight_ui
   pip install -r backend/requirements.txt
   ```
3. **Frontend:**
   ```bash
   cd frontend
   npm install
   cp .env.example .env   # then edit VITE_DEFAULT_LAT/LON to your real intersection
   ```
4. **Only if running the real GPS bridge** (see below) - a *separate*
   ROS2 environment for `gps_bridge.py`. `rclpy` can't be pip-installed;
   it has to come from an actual ROS2 distribution (`apt` on Ubuntu, or a
   Docker/VM sandbox elsewhere). If this is the vehicle's own onboard
   computer, it likely already has this set up for other nodes (e.g.
   `veh_coord_node/sub_veh_ros2.py`) - confirm the real GPS/INS driver is
   actually publishing on `/ins/nav_sat_fix` before expecting fixes.

Once those are in place, see "Running it" below for local/mock testing,
or "Running the real GPS bridge" + point your real RSU's broadcast at
`<backend-host>:4000` (see "Configuration" above for `BACKEND_HOST`) for
a real end-to-end test.

## Running it (3 terminals)

**Terminal 1 — backend** (or `./run_all.sh`, which starts everything from `deploy.env` - see below)
```bash
cd backend
export PYV2XLIB_VENDOR_DIR=/path/to/folder/containing/v2xlib.py
python app.py
```
Should print `Backend running at http://127.0.0.1:5000` and two
`[udp] Listening on 0.0.0.0:...` lines (alerts/SDSM, ego), then keep running.

**Terminal 2 — mock sender** (stands in for a real RSU *and* the real
`gps_bridge.py`; sends real encoded ICA/RSA hex messages, a real encoded
SDSM feed (continuously-moving detected objects), and a simulated ego GPS
path, all at once, so you can test without any hardware)
```bash
export PYV2XLIB_VENDOR_DIR=/path/to/folder/containing/v2xlib.py
python test_cases/mock_sender.py
```
For GPS-specific scenarios (a stationary vehicle, a dropped signal, etc.),
see `mock_sender_gps_tests.py` instead - `python test_cases/mock_sender_gps_tests.py`
with no arguments lists them. For extra named SDSM scenarios beyond the
default moving one (a richly-described vehicle, an obstacle, staleness
checks), see `mock_sender_sdsm_tests.py` the same way.

**Terminal 3 — frontend**
```bash
cd frontend
npm run dev
```
Open the URL it prints (port 3000 by default).

## Running the real GPS bridge

`gps_bridge.py` (project root) is what feeds the map's live ego marker from
a *real* vehicle, instead of `mock_sender.py`'s simulated path - it
subscribes to the real ROS2 topic a vehicle's GPS/INS driver publishes on
(`/ins/nav_sat_fix`, the same mechanism proven in `veh_coord_node/
sub_veh_ros2.py`) and forwards each fix to the backend over UDP.

This needs an actual ROS2 environment - `rclpy` is not a `pip install`able
package, it has to come from a real ROS2 distribution (installed via `apt`
on Ubuntu, or a Docker/VM sandbox for local development on other OSes). Run
it separately from the Flask backend's own Python environment, wherever it
can actually reach the vehicle's ROS2 network - almost certainly the
vehicle's own onboard computer, not necessarily the same machine the
backend runs on:
```bash
GPS_TARGET_HOST=192.168.1.50 EGO_UDP_PORT=4003 python3 backend/gps_bridge.py
```
(`GPS_TARGET_HOST` defaults to `127.0.0.1`, `EGO_UDP_PORT` to `4003` - only
override what's actually different from the backend's own `config.py` values.)

Because `mock_sender.py`/`mock_sender_gps_tests.py` send the exact same
`{lat, lon, timestamp}` JSON to the same port, testing entirely with the
mocks (no ROS2, no vehicle) already exercises the identical backend/
frontend code path `gps_bridge.py` feeds for real - not an approximation of
the real integration, the same one.

## How it works

```
RSU --(UDP, ASCII hex string)--> udp_listener.py --> decoder.py
                                                          |
                                          peeks the ASN.1 CHOICE tag to
                                          tell ICA/RSA/SDSM apart, then
                                          calls the matching decode function
                                                          |
                                                          v
                                              alert_formatter.py
                                     (decoded dict -> {type, warning,
                                      text, lat, lon} for ICA/RSA - SDSM's
                                      own shape is below, it's not an alert)
                                                          |
                                          socketio.emit('warning', ...)  # ICA/RSA only
                                                          |
                                                          v
                                    useSocket.js (frontend) -> MapView.vue
                                                             -> AlertStack.vue (the card stack)

This vehicle's own live GPS position (separate UDP port, separate socket event):

gps_bridge.py --(UDP, JSON: {lat, lon, timestamp})--> udp_listener.py
                                                          |
                                          socketio.emit('ego', ...)
                                                          |
                                                          v
                                    useSocket.js (frontend) -> MapView.vue

SDSM (detected objects) - same UDP port/hex-over-UDP mechanism as ICA/RSA
(decoder.py peeks the same ASN.1 tag), but its own socket event so it never
lands in the alert stack:

RSU --(UDP, ASCII hex string)--> udp_listener.py --> decoder.py --> SDSMDecoder.py
                                                          |
                                              alert_formatter.py's format_sdsm()
                                       (refPos + each object's meters-offset ->
                                        real lat/lon via geometry.offset_latlon())
                                                          |
                                          socketio.emit('sdsm', ...)
                                                          |
                                                          v
                                    useSocket.js (frontend) -> MapView.vue
                                    (its own marker layer/color palette,
                                     shown whenever the map itself is -
                                     see below)
```

### SDSM (detected objects)

SDSM is real sensor data from an RSU - a reporting station (`refPos`) plus
whatever vehicles/pedestrians/obstacles it currently sees, each given as a
meters offset from that station. It is **not an alert** (there's no
single "subject" the way ICA/RSA have one), so it's deliberately kept off
the alert stack: its own `'sdsm'` socket event (not `'warning'`) and its
own map marker layer/color palette. It's also the map's only live-object
overlay - there's no separate "tracking" feed - so there's no dedicated
toggle for it either: it's visible whenever the map is (view mode "Both"
or "Map" in `AlertControls.vue`; "Alerts" mode doesn't render the map at
all, useful for testing ICA/RSA in isolation). `mock_sender_sdsm_tests.py`
sends real encoded SDSM frames (via the real
`backend/codec/SDSMEncoder.py`/`SDSMDecoder.py`) to exercise this without
real hardware.

**There is no "all clear" message for alerts.** ICA and RSA are alert-only
message types — their existence *is* the warning. The RSU just stops
sending when there's nothing to report, so the frontend clears the banner
+ map pin after ~3s of silence (`useSocket.js`) rather than waiting for an
explicit `warning: false`.

## Known open items

- **No authentication yet.** `cors_allowed_origins` defaults to `*` and
  there's no token/session check anywhere. Fine for local dev; needs
  addressing before deploying on a network you don't fully control — see
  `msight_old_structure/backend/sockets.py` + `config.py` for a
  token-gate pattern already written elsewhere in this repo tree, not
  yet ported here.
- `geometry.py`'s lat/lon math (used to place SDSM's detected objects from
  their meters-offset) is a flat-earth approximation, fine at intersection
  scale but not meant for anything larger.
- Whether every RSA/ICA message should count as a "warning," or only ones
  above some priority/severity, hasn't been decided — right now arrival
  always means `warning: true`.

## One-command run (`run_all.sh`)

```bash
cp deploy.env.example deploy.env   # once; deploy.env is git-ignored
# edit deploy.env: ports, BACKEND_HOST, VITE_BACKEND_URL, RUN_GPS_BRIDGE=1 on the vehicle...
./run_all.sh                       # backend + frontend (+ gps_bridge); Ctrl+C stops all
```
