"""
Turns a decoded live-tracking message into the frame socket event

Input shape, for now: whatever mock_sender.py's placeholder JSON tracking format produces 
format_tracking_frame needs changes once the encoder / decoder for tracking is set 
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
