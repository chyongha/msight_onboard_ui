"""
Turns a decoded live-tracking message into the frame socket event

Input shape, for now: whatever mock_sender.py's placeholder JSON tracking format produces
format_tracking_frame needs changes once the encoder / decoder for tracking is set
"""
_VEHICLE_CATEGORIES = {'vehicle', 'sedan', 'suv', 'truck', 'bus'}


def format_tracking_frame(raw: dict) -> dict:
    objects = []
    for obj in raw.get('objects', []):
        lat, lon = obj.get('lat'), obj.get('lon')
        if lat is None or lon is None:
            continue

        category = 'vehicle' if obj.get('category') in _VEHICLE_CATEGORIES else 'vru'
        heading_deg = float(obj.get('heading_deg', 0.0))
        speed = float(obj.get('speed', 0.0))

        objects.append({
            'id': obj.get('id'),
            'lat': round(lat, 7),
            'lon': round(lon, 7),
            'category': category,
            'speed': round(speed, 2),
            'heading_deg': round(heading_deg, 1),
        })

    return {
        'objects': objects,
        'timestamp': raw.get('timestamp'),
    }
