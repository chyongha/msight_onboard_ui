"""
Turns a decoded ICA/RSA dict into the shape frontend can understand:
    {type, warning, text, headline, events, lat, lon, timestamp, severity, category, subject, trajectory}

text: flattened one-line summary, used for the map alert-pin tooltip
    (MapView.vue) - always a single string for both message types.
headline: the single key primary event. Only RSA (typeEvent)
events: the card's bulleted/chipped list. For ICA this is every active
    eventFlag condition (the whole story - ICA has no separate headline)
    For RSA this is description code that supports the RSA's typeEvent flag
subject: info about who/what triggered the alert (speed, heading, active
    flags). For ICA this is partOne, the offending vehicle's own BSM core
    data - always present. For RSA it's whatever heading/speed came with the
    position report
trajectory: recent path of the offending vehicle, decoded from ICA's
    path.crumbData breadcrumbs. None when there isn't at least an anchor +
    one usable crumb point 
"""
import time

from codec.itis_codes import ITIS

# ITIS code of the event : name of the event
_ITIS_NAME_BY_CODE = {code: name for name, code in ITIS.items()}

# ICA eventFlag bits - bit6 is skipped since it is reserved for future use 
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

# ITIS name substrings that always mean "critical" regardless of priority
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
    read eventFlag, return the label for each bit that's set (lowercase,
    e.g. 'hard braking'), oldest-defined-bit first
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


def _ica_subject(part_one: dict) -> dict | None:
    """
    Who/what triggered the alert: the offending vehicle's speed, heading,
    and any active brake/traction/stability flags worth surfacing
    """
    if not part_one:
        return None

    speed = part_one.get('speed')
    heading = part_one.get('heading')
    brakes = part_one.get('brakes') or {}

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

    return {
        'kind': 'vehicle',
        'source_id': part_one.get('id'),
        'speed_mps': speed if isinstance(speed, (int, float)) else None,
        'heading_deg': heading if isinstance(heading, (int, float)) else None,
        'flags': flags,
    }


def _ica_trajectory(part_one: dict, path: dict) -> list | None:
    """
    recent path of the offending vehicle 
    from partOne's timeOffset seconds in the past (oldest to newest)
    ends at vehicle's current position
    none if there is nothing usable to draw 
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
            continue  # 'unavailable' or missing
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
        'timestamp': time.time(),
        'subject': _ica_subject(part_one),
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
    Whatever heading/speed came with the position report - ex. a probe
    vehicle's own reading at the moment it passed/reported the hazard.

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
        'timestamp': time.time(),
        'subject': _rsa_subject(position, category),
        'trajectory': None,   # no path history for rsa 
    }
