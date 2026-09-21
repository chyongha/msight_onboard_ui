"""
Alert formatting for the frontend
"""
import re
import time
from datetime import datetime

from codec.itis_codes import ITIS
from geometry import offset_latlon

# ITIS code of the event : name of the event
_ITIS_NAME_BY_CODE = {code: name for name, code in ITIS.items()}

# alertVisuals.js compassLabel() 
# bit 0 = 0-22.5deg, bit 1 = 22.5-45deg, ... bit 15 = 337.5-360deg
_COMPASS_16 = [
    'N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
    'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW',
]

# ICA eventFlag bits - skip bit 6
_ICA_EVENT_BITS = {
    0: 'hazard lights on',
    1: 'stop line violation',
    2: 'ABS activated',
    3: 'traction control loss',
    4: 'stability control activated',
    5: 'hazardous materials',
    7: 'hard braking',
    8: 'lights changed',
    9: 'wipers changed',
    10: 'flat tire',
    11: 'disabled vehicle',
    12: 'air bag deployment',
    13: 'jackknife',
}

# which of the bits above should push the banner into the top severity tier
_ICA_CRITICAL_BITS = {1, 3, 4, 7, 10, 12, 13}  # stop line violation, traction/stability loss, hard braking, flat tire, air bag, jackknife
_ICA_CAUTION_BITS = {0, 2, 5, 8, 9, 11}         # hazard lights, ABS, hazmat, lights/wipers changed, disabled vehicle

# used to pick the title of the RSA banner
_RSA_CATEGORY_KEYWORDS = (
    ('pedestrian', ('pedestrian', 'bicycle', 'crosswalk', 'people-on-roadway')),
    ('vehicle', ('vehicle', 'bus', 'motorcycle', 'truck', 'driver', 'chase')),
    ('weather', ('rain', 'fog', 'ice', 'snow', 'pavement', 'flooding')),
)

# ITIS name substrings that always mean critical regardless of the priority
_RSA_CRITICAL_KEYWORDS = ('accident', 'fire', 'chase', 'medical-emergency', 'jack-knife')


def _humanize(name: str) -> str:
    """
    keys in itis_code.py are dashed (-), which is not fine for banner text - change it to a space
    """
    return name.replace('-', ' ')


def _capitalize_first(text: str) -> str:
    """
    Capitalize the first letter of a string
    """
    return text[:1].upper() + text[1:] if text else text


def _itis_label(code) -> str:
    """
    returns name of the event from the numeric itis code 
    """
    if code is None:
        return 'unknown event'
    name = _ITIS_NAME_BY_CODE.get(code)
    return _humanize(name) if name else f'ITIS code {code}'


def _active_ica_labels(event_flag_value) -> list:
    """
    read eventFlag, return the label for each bit that's set
    """
    if not isinstance(event_flag_value, int):
        return []
    return [label for bit, label in _ICA_EVENT_BITS.items() if event_flag_value & (1 << bit)]


def _ica_event_text(labels: list) -> str:
    """
    flattened one-line summary
    """
    if not labels:
        return 'vehicle approaching intersection without right of way'
    return ', '.join(labels)


def _ica_events(labels: list) -> list:
    """
    one bullet per active flag
    """
    if not labels:
        return ['Vehicle approaching intersection without right of way']
    return [_capitalize_first(label) for label in labels]


def _ica_severity(event_flag_value) -> str:
    """
    evaluate severity of the ica event 
    """
    if not isinstance(event_flag_value, int) or event_flag_value == 0:
        return 'caution'
    if any(event_flag_value & (1 << bit) for bit in _ICA_CRITICAL_BITS):
        return 'critical'
    if any(event_flag_value & (1 << bit) for bit in _ICA_CAUTION_BITS):
        return 'caution'
    return 'caution'


def _clean_coord(value):
    """
    if unavailable value for missing values, convert to None
    """
    if value == 'unavailable' or not isinstance(value, (int, float)):
        return None
    return value


def _event_epoch(message_type: str, raw: dict, relay_time: float) -> float:
    """
    when the event happened 
    """
    if message_type == "sdsm":
        ts = raw.get('sDSMTimeStamp') or {}
        month, day, hour, minute = ts.get('month'), ts.get('day'), ts.get('hour'), ts.get('minute')
        if None in (month, day, hour, minute):
            return relay_time
        year = ts.get('year') or datetime.now().year
        second = ts.get('second', 0)
        try:
            return datetime(year, month, day, hour, minute).timestamp() + second
        except ValueError:
            return relay_time
    minutes = raw.get('timeStamp')
    if not isinstance(minutes, int):
        return relay_time
    year_start = datetime(datetime.now().year, 1, 1)
    return (year_start.timestamp()) + minutes * 60


def _ica_subject(part_one: dict) -> dict | None:
    """
    who/what triggered the alert
    """
    if not part_one:
        return None

    speed = part_one.get('speed')
    heading = part_one.get('heading')
    brakes = part_one.get('brakes') or {}
    accel = part_one.get('accelSet') or {}
    size = part_one.get('size') or {}

    flags = []
    if brakes.get('abs') in ('on', 'engaged'):
        flags.append('ABS activated')
    if brakes.get('traction') in ('on', 'engaged'):
        flags.append('Traction control active')
    if brakes.get('scs') in ('on', 'engaged'):
        flags.append('Stability control active')
    if brakes.get('auxBrakes') == 'on':
        flags.append('Auxiliary brakes on')
    wheel_brakes = brakes.get('wheelBrakes')
    if isinstance(wheel_brakes, int) and wheel_brakes not in (0, 1):  # bit0 = unavailable
        flags.append('Wheel brakes engaged')

    yaw = accel.get('yaw')
    lat_accel = accel.get('lat')
    if isinstance(yaw, (int, float)) and abs(yaw) > 20:  # deg/s
        flags.append('Spinning')
    if isinstance(lat_accel, (int, float)) and abs(lat_accel) > 3:  # m/s^2
        flags.append('Sliding sideways')

    gear = part_one.get('transmission')
    long_accel = accel.get('long')
    length_cm = size.get('length')
    width_cm = size.get('width')

    return {
        'kind': 'vehicle',
        'source_id': part_one.get('id'),
        'speed_mps': speed if isinstance(speed, (int, float)) else None,
        'heading_deg': heading if isinstance(heading, (int, float)) else None,
        'flags': flags,
        'gear': gear if gear not in (None, 'unavailable') else None,
        'steering_deg': part_one.get('angle') if isinstance(part_one.get('angle'), (int, float)) else None,
        'accel_mps2': long_accel if isinstance(long_accel, (int, float)) else None,
        'length_m': round(length_cm / 100, 1) if isinstance(length_cm, (int, float)) else None,
        'width_m': round(width_cm / 100, 1) if isinstance(width_cm, (int, float)) else None,
    }


def _ica_trajectory(part_one: dict, path: dict) -> list | None:
    """
    recent path of the offending vehicle 
    from partOne's timeOffset seconds in the past (oldest to newest) ends at vehicle's current position
    """
    if not part_one or not path:
        return None

    anchor_lat = _clean_coord(part_one.get('lat'))
    anchor_lon = _clean_coord(part_one.get('long'))
    if anchor_lat is None or anchor_lon is None:
        return None

    points = []
    for crumb in path.get('crumbData') or []:
        lat_offset = crumb.get('latOffset')
        lon_offset = crumb.get('lonOffset')
        if not isinstance(lat_offset, (int, float)) or not isinstance(lon_offset, (int, float)):
            continue  # unavailable or missing 
        t_offset = crumb.get('timeOffset')
        points.append({
            'lat': round(anchor_lat + lat_offset, 7),
            'lon': round(anchor_lon + lon_offset, 7),
            't_offset': t_offset if isinstance(t_offset, (int, float)) else None,
        })

    if not points:
        return None

    points.sort(key=lambda p: -(p['t_offset'] or 0))  # furthest back in time first
    points.append({'lat': anchor_lat, 'lon': anchor_lon, 't_offset': 0})  # current position, last
    return points


def format_ica(ica: dict) -> dict:
    part_one = ica.get('partOne')
    lat = _clean_coord((part_one or {}).get('lat'))
    lon = _clean_coord((part_one or {}).get('long'))

    event_flag = ica.get('eventFlag')
    event_flag_value = event_flag[0] if isinstance(event_flag, tuple) else event_flag
    labels = _active_ica_labels(event_flag_value)
    relay_time = time.time()

    return {
        'type': 'ICA',
        'warning': True,
        'severity': _ica_severity(event_flag_value),
        'category': 'vehicle',
        'text': f'Intersection collision warning: {_ica_event_text(labels)}',
        'headline': None,  # ICA has no single headline separate from its flag list
        'events': _ica_events(labels),  # one bullet per active flag, for the expanded card
        'lat': lat,
        'lon': lon,
        'timestamp': relay_time,
        'occurred_at': _event_epoch("ica", ica, relay_time),
        'subject': _ica_subject(part_one),
        'extent': None,  # only from RSA
        'extent_m': None,
        'direction_slices': None,  # only from RSA
        'trajectory': _ica_trajectory(part_one, ica.get('path')),
    }


def _rsa_names(type_event, description) -> list:
    """
    get name of all events and descriptions of RSA messages 
    """
    codes = [type_event] + list(description or [])
    return [_ITIS_NAME_BY_CODE.get(code, '') for code in codes]


def _rsa_category(names: list) -> str:
    """
    get the corresponding cateogry of the event (vehicle, pedestrian, weather...)
    road_hazard if nothing is corresponding 
    """
    for category, keywords in _RSA_CATEGORY_KEYWORDS:
        if any(any(kw in name for kw in keywords) for name in names):
            return category
    return 'road_hazard'


def _rsa_severity(priority, names: list) -> str:
    """
    get severity of the vent 
    """
    if any(any(kw in name for kw in _RSA_CRITICAL_KEYWORDS) for name in names):
        return 'critical'
    if not isinstance(priority, int):
        return 'caution'
    if priority >= 5:
        return 'critical'
    if priority >= 2:
        return 'caution'
    return 'info'


def _rsa_subject(position: dict, category: str) -> dict | None:
    """
    Whatever heading/speed came with the position report
    """
    heading = _clean_coord(position.get('heading'))
    speed = _clean_coord((position.get('speed') or {}).get('speed'))
    if heading is None and speed is None:
        return None

    return {
        'kind': 'pedestrian' if category == 'pedestrian' else 'vehicle',
        'source_id': None,  
        'speed_mps': speed,
        'heading_deg': heading,
        'flags': [],
    }


_RSA_EXTENT_LABELS = {
    'useInstantlyOnly': 'Applies at this point only',
    'forever': 'No distance limit',
}


def _rsa_extent_label(extent) -> str | None:
    """
    Edit `extent` enum into how far past the hazard this stays relevant banner text.
    """
    if not isinstance(extent, str):
        return None
    if extent in _RSA_EXTENT_LABELS:
        return _RSA_EXTENT_LABELS[extent]

    match = re.fullmatch(r'useFor(\d+)meters', extent)
    if not match:
        return None
    meters = int(match.group(1))
    distance = f'{meters / 1000:g}km' if meters >= 1000 else f'{meters}m'
    return f'Applies for {distance}'


def _rsa_extent_meters(extent) -> int | None:
    """
    RSA's `extent` enum as a plain distance in meters, for deciding whether
    this vehicle is close enough for the alert to matter
    None = no usable limit: not sent, 'forever', or 'useInstantlyOnly' (no
    radius to compare against), so the alert is always shown.
    """
    if not isinstance(extent, str):
        return None
    match = re.fullmatch(r'useFor(\d+)meters', extent)
    return int(match.group(1)) if match else None


def _rsa_heading_slices(heading) -> list | None:
    """
    Which ~22.5deg compass slices this alert applies to (RSA's top-level
    `heading` HeadingSlice bitmask) - NOT a single object's direction of
    travel, that's `subject`'s heading_deg. This is "relevant to traffic
    heading these ways" (can be several, non-adjacent slices at once).
    """
    if not isinstance(heading, int) or heading == 0:
        return None
    return [
        {'index': i, 'label': _COMPASS_16[i]}
        for i in range(16)
        if heading & (1 << (15 - i))
    ]
    

def format_rsa(rsa: dict) -> dict:
    position = rsa.get('position', {})
    lat = _clean_coord(position.get('lat'))
    lon = _clean_coord(position.get('long'))

    type_event = rsa.get('typeEvent')
    description = rsa.get('description', [])
    names = _rsa_names(type_event, description)
    category = _rsa_category(names)

    # typeEvent is the primary/headline label, description codes elaborate on it -
    # text (map tooltip) still flattens both together, but headline/events split
    # them for the card so the primary event and its supporting detail read as
    # two distinct blocks (see module docstring)
    description_labels = [_itis_label(code) for code in description]
    labels = [_itis_label(type_event)] + description_labels
    relay_time = time.time()

    return {
        'type': 'RSA',
        'warning': True,
        'severity': _rsa_severity(rsa.get('priority'), names),
        'category': category,
        'text': _capitalize_first('; '.join(labels)),
        'headline': _capitalize_first(_itis_label(type_event)),
        'events': [_capitalize_first(label) for label in description_labels],  # supporting detail only
        'lat': lat,
        'lon': lon,
        'timestamp': relay_time,
        'occurred_at': _event_epoch("rsa", rsa, relay_time),
        'subject': _rsa_subject(position, category),
        'extent': _rsa_extent_label(rsa.get('extent')),
        'extent_m': _rsa_extent_meters(rsa.get('extent')),
        'direction_slices': _rsa_heading_slices(rsa.get('heading')),
        'trajectory': None,   # no path history for rsa
    }


def _sdsm_object_category(det_common: dict, opt_data) -> str:
    """
    opt_data is decoder's `(choice_name, value_dict)` tuple for
    detObjOptData
    """
    opt_choice = opt_data[0] if isinstance(opt_data, (list, tuple)) and opt_data else None
    if opt_choice == 'detVeh':
        return 'vehicle'
    if opt_choice == 'detVRU':
        return 'vru'
    if opt_choice == 'detObst':
        return 'obstacle'

    obj_type = det_common.get('objType')
    if obj_type in ('vehicle', 'vru', 'animal'):
        return obj_type
    return 'unknown'


def _sdsm_object_detail(category: str, det_common: dict, opt_data) -> str | None:
    """Short human string for the object's tooltip/info box - only as much detail as the message actually carries."""
    opt_choice, opt_value = (opt_data[0], opt_data[1]) if isinstance(opt_data, (list, tuple)) and opt_data else (None, {})

    parts = []
    if category == 'vehicle' and opt_choice == 'detVeh':
        lights = opt_value.get('lights')
        if isinstance(lights, str):  # decoder already turns the recognized codes into a label
            parts.append(lights)
        vehicle_class = opt_value.get('vehicleClass')
        if isinstance(vehicle_class, int):
            parts.append(f'class {vehicle_class}')
    elif category == 'vru' and opt_choice == 'detVRU':
        basic_type = opt_value.get('basicType')
        if isinstance(basic_type, str):
            parts.append(basic_type)

    # how confident the sensor is in objType (not in the position/speed) -
    # available for every category, not just detVeh/detVRU, so it's checked
    # unconditionally rather than folded into the branches above
    confidence = det_common.get('objTypeCfd')
    if isinstance(confidence, int) and confidence > 0:
        parts.append(f'~{min(confidence, 100)}% confidence')

    return ', '.join(parts) if parts else None


def _sdsm_object_size_m(category: str, opt_data) -> str | None:
    """
    Human-readable footprint size - only when the message actually carries
    it for this object's category, never fabricated/defaulted.
    """
    opt_choice, opt_value = (opt_data[0], opt_data[1]) if isinstance(opt_data, (list, tuple)) and opt_data else (None, {})

    if category == 'vehicle' and opt_choice == 'detVeh':
        size = opt_value.get('size') or {}
        width, length = size.get('width'), size.get('length')
        if isinstance(width, (int, float)) and isinstance(length, (int, float)):
            return f'{width:.1f}×{length:.1f}m'

    if category == 'obstacle' and opt_choice == 'detObst':
        obst_size = opt_value.get('obstSize') or {}
        width, length = obst_size.get('width'), obst_size.get('length')
        if isinstance(width, (int, float)) and isinstance(length, (int, float)):
            return f'{width:.1f}×{length:.1f}m'

    if category == 'vru' and opt_choice == 'detVRU':
        # SDSMDecoder.py doesn't convert this field the way it does detVeh's
        # size/height - it's PersonalSafetyMessage.AttachmentRadius per the
        # real ASN.1 schema, raw units of centimeters
        radius = opt_value.get('radius')
        if isinstance(radius, (int, float)) and radius > 0:
            return f'~{radius / 100:.1f}m radius'

    return None


def _sdsm_objects(sdsm: dict, ref_lat: float | None, ref_lon: float | None) -> list:
    """
    Turns SDSM's `objects` (each given as a meters offset from refPos, see
    SDSMDecoder.py) into `{id, lat, lon, category, speed, heading_deg,
    size_m, detail}` per object, for MapView.vue's marker rendering.
    """
    if ref_lat is None or ref_lon is None:
        return []  # nothing to offset the objects from

    objects = []
    for obj in sdsm.get('objects', []):
        det_common = obj.get('detObjCommon') or {}
        pos = det_common.get('pos') or {}
        offset_x, offset_y = pos.get('offsetX'), pos.get('offsetY')
        if not isinstance(offset_x, (int, float)) or not isinstance(offset_y, (int, float)):
            continue

        # offsetX/offsetY are meters east/north of refPos - the only frame
        # SDSM gives us, there's no separate heading for the reporting
        # station itself to rotate this by
        lat, lon = offset_latlon(ref_lat, ref_lon, offset_x, offset_y)

        opt_data = obj.get('detObjOptData')
        category = _sdsm_object_category(det_common, opt_data)
        heading_deg = float(det_common.get('heading') or 0.0)
        speed = float(det_common.get('speed') or 0.0)

        objects.append({
            'id': det_common.get('objectID'),
            'lat': round(lat, 7),
            'lon': round(lon, 7),
            'category': category,
            'speed': round(speed, 2),
            'heading_deg': round(heading_deg, 1),
            'size_m': _sdsm_object_size_m(category, opt_data),
            'detail': _sdsm_object_detail(category, det_common, opt_data),
        })

    return objects


def format_sdsm(sdsm: dict) -> dict:
    """
    SDSM is a sensor frame, not an alert - one reporting station plus a list of objects it currently sees
    """
    ref_pos = sdsm.get('refPos', {})
    lat = _clean_coord(ref_pos.get('lat'))
    lon = _clean_coord(ref_pos.get('long'))
    relay_time = time.time()

    return {
        'type': 'SDSM',
        'source_id': sdsm.get('sourceID'),
        'equipment_type': sdsm.get('equipmentType'),
        'lat': lat,
        'lon': lon,
        'timestamp': relay_time,
        'occurred_at': _event_epoch('sdsm', sdsm, relay_time),
        'objects': _sdsm_objects(sdsm, lat, lon),
    }