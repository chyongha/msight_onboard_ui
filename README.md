# msight_onboard_ui

Decodes ICA (Intersection Collision Avoidance) and RSA (RoadSideAlert)
J2735-style messages arriving over UDP from an MSight roadside unit (RSU),
and displays a warning banner + a map pin at the alert location — plus a
live map of tracked vehicles/pedestrians (currently backed by a mock feed,
see below). Built with Flask + Flask-SocketIO (backend) and Vue 3 + Vite
(frontend).

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

Nothing here is hardcoded — same code runs on a dev laptop or a deployed
roadside box, just with different env vars set.

**Backend** (`backend/config.py`):

| Var | Default | What it's for |
|---|---|---|
| `BACKEND_HOST` | `127.0.0.1` | Interface the Flask/Socket.IO server binds to. Use `0.0.0.0` if the frontend runs on a different device than the backend. |
| `BACKEND_PORT` | `5000` | Port for the Flask/Socket.IO server. |
| `UDP_PORT` | `4000` | Port the UDP listener binds to, for incoming ICA/RSA alert messages. |
| `TRACKING_UDP_PORT` | `4001` | Port the (mocked, see below) live-tracking UDP listener binds to. |
| `FRONTEND_ORIGIN` | `*` | Origin(s) allowed to open a Socket.IO connection. `*` is fine for local dev; lock this to the real frontend's origin once deployed somewhere with untrusted network access. |

**Frontend** (copy `frontend/.env.example` to `frontend/.env` and edit):

| Var | Default | What it's for |
|---|---|---|
| `VITE_BACKEND_URL` | `http://127.0.0.1:5000` | Where the browser looks for the backend's Socket.IO server. Must match wherever `BACKEND_HOST`/`BACKEND_PORT` above actually end up reachable from. |
| `VITE_DEFAULT_LAT` / `VITE_DEFAULT_LON` | `42.2808` / `-83.7430` | Map center shown before the first alert arrives. Set to your actual intersection. |

`mock_sender.py` reads `UDP_PORT`/`TRACKING_UDP_PORT` from the same
`backend/config.py` as the real backend, so they can't drift apart.

## Running it (3 terminals)

**Terminal 1 — backend**
```bash
cd backend
export PYV2XLIB_VENDOR_DIR=/path/to/folder/containing/v2xlib.py
python app.py
```
Should print `Backend running at http://127.0.0.1:5000` and two
`[udp] Listening on 0.0.0.0:...` lines (alerts + tracking), then keep running.

**Terminal 2 — mock sender** (stands in for a real RSU; sends real
encoded ICA/RSA hex messages over UDP, plus a simulated live-tracking
feed, so you can test without hardware)
```bash
export PYV2XLIB_VENDOR_DIR=/path/to/folder/containing/v2xlib.py
python mock_sender.py
```

**Terminal 3 — frontend**
```bash
cd frontend
npm run dev
```
Open the URL it prints (port 3000 by default).

## How it works

```
RSU --(UDP, ASCII hex string)--> udp_listener.py --> decoder.py
                                                          |
                                          peeks the ASN.1 CHOICE tag to
                                          tell ICA from RSA, then calls
                                          the matching decode function
                                                          |
                                                          v
                                              alert_formatter.py
                                     (decoded dict -> {type, warning,
                                      text, lat, lon})
                                                          |
                                          socketio.emit('warning', ...)
                                                          |
                                                          v
                                    useSocket.js (frontend) -> MapView.vue
                                                             -> WarningBanner.vue

Live tracking (separate UDP port, separate socket event):

(mocked feed) --(UDP, JSON)--> udp_listener.py --> tracking_formatter.py
                                                          |
                                        (raw dict -> {objects: [...],
                                         timestamp}, corner/shape math
                                         via geometry.py)
                                                          |
                                          socketio.emit('frame', ...)
                                                          |
                                                          v
                                    useSocket.js (frontend) -> MapView.vue
```

**There is no "all clear" message for alerts.** ICA and RSA are alert-only
message types — their existence *is* the warning. The RSU just stops
sending when there's nothing to report, so the frontend clears the banner
+ map pin after ~3s of silence (`useSocket.js`) rather than waiting for an
explicit `warning: false`.

**The live-tracking feed is currently mocked.** No real encoder/decoder
exists yet for whatever message type will actually carry continuous
vehicle/pedestrian positions (presumably SDSM). `mock_sender.py` sends a
placeholder JSON format instead (see its docstring) on `TRACKING_UDP_PORT`,
confirmed to use lat/lon directly (not local x/y — no `lanelet2` dependency
needed here, unlike `msight_original_script/realtime_plot.py`/
`msight_old_structure`, which do need it). Swapping in a real decoder later
means replacing `udp_listener.py`'s `_decode_tracking_frame()` function
only — `tracking_formatter.py`, `geometry.py`, and the entire frontend
don't need to change, as long as the real decoder produces the same
`{objects: [{id, lat, lon, category, speed, heading_deg, length_m,
width_m}], timestamp}` shape `format_tracking_frame()` expects as input.

## Known open items

- **No authentication yet.** `cors_allowed_origins` defaults to `*` and
  there's no token/session check anywhere. Fine for local dev; needs
  addressing before deploying on a network you don't fully control — see
  `msight_old_structure/backend/sockets.py` + `config.py` for a
  token-gate pattern already written elsewhere in this repo tree, not
  yet ported here.
- **No real live-tracking decoder** — see above. `geometry.py`'s lat/lon
  math is a flat-earth approximation, fine at intersection scale but not
  meant for anything larger.
- Whether every RSA/ICA message should count as a "warning," or only ones
  above some priority/severity, hasn't been decided — right now arrival
  always means `warning: true`.
