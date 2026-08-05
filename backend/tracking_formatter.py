"""
Turns a decoded live-tracking message into the 'frame' socket event
payload the frontend renders — same shape as
msight_original_script/realtime_plot.py's 'frame' event, minus the
fields that don't apply to this project:

  - no conflict_ids / warning_circles: this project doesn't recompute
    conflicts itself — the RSU already decided that and reported it via
    ICA/RSA (see alert_formatter.py). This layer is just "where is
    everything right now."
  - no tl_phases / traffic light bars: no SPaT message decoder exists.
  - no ego_id: there's no single "ego vehicle" here — this is a
    roadside/infrastructure view, not one vehicle's own dashboard.

Input shape, for now: whatever mock_sender.py's placeholder JSON tracking
format produces (see its module docstring) — NOT a real decoded SDSM
message, since no real encoder/decoder for that exists yet. Swapping in
a real decoder later only means replacing whatever calls this function
with something that builds the same `raw` dict shape; this function and
everything downstream of it (geometry.py, MapView.vue) doesn't change.
"""
from geometry import rectangle_corners_latlon

_VEHICLE_CATEGORIES = {'vehicle', 'sedan', 'suv', 'truck', 'bus'}
_DEFAULT_LENGTH_M = 4.0
_DEFAULT_WIDTH_M = 1.8
_VRU_RADIUS_M = 1.5


def format_tracking_frame(raw: dict) -> dict:
    objects = []
    for obj in raw.get('objects', []):
        lat, lon = obj.get('lat'), obj.get('lon')
        if lat is None or lon is None:
            continue

        category = 'vehicle' if obj.get('category') in _VEHICLE_CATEGORIES else 'vru'
        heading_deg = float(obj.get('heading_deg', 0.0))
        speed = float(obj.get('speed', 0.0))

        if category == 'vehicle':
            length_m = float(obj.get('length_m') or _DEFAULT_LENGTH_M)
            width_m = float(obj.get('width_m') or _DEFAULT_WIDTH_M)
            corners = rectangle_corners_latlon(lat, lon, heading_deg, length_m, width_m)
            shape = 'vehicle_box'
            radius_m = max(width_m / 2.0, 0.2)
        else:
            corners = None
            shape = 'circle'
            radius_m = _VRU_RADIUS_M

        objects.append({
            'id': obj.get('id'),
            'lat': round(lat, 7),
            'lon': round(lon, 7),
            'category': category,
            'speed': round(speed, 2),
            'heading_deg': round(heading_deg, 1),
            'shape': shape,
            'radius_m': round(radius_m, 2),
            'corners': corners,
        })

    return {
        'objects': objects,
        'timestamp': raw.get('timestamp'),
    }
