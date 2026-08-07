"""
Turns a decoded ICA/RSA dict into the shape frontend can understand
    {type, warning, text, lat, lon}
"""
from codec.itis_codes import ITIS

# ITIS code of the event : name of the event 
_ITIS_NAME_BY_CODE = {code: name for name, code in ITIS.items()}

# ICA eventFlag bit - only the one useful for the warning banner is listed here 
_ICA_EVENT_BITS = {
    0: 'hazard lights on',
    1: 'stop line violation',
    2: 'ABS activated',
    3: 'traction control loss',
    4: 'stability control activated',
    5: 'hazardous materials',
    7: 'hard braking',
}


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
    returns name of the event from the numeric ITIS-code
    """
    if code is None:
        return 'unknown event'
    name = _ITIS_NAME_BY_CODE.get(code)
    return _humanize(name) if name else f'ITIS code {code}'


def _ica_event_text(event_flag_value) -> str:
    """
    read eventFlag, find which bits are set, and joins their labels into a readable phrase
    """
    if not isinstance(event_flag_value, int):
        return 'vehicle approaching intersection without right of way'
    active = [label for bit, label in _ICA_EVENT_BITS.items() if event_flag_value & (1 << bit)]
    if not active:
        return 'vehicle approaching intersection without right of way'
    return ', '.join(active)


def _clean_coord(value):
    """
    if unavailable value for missing values, convert to None
    """
    return None if value == 'unavailable' else value


def format_ica(ica: dict) -> dict:
    part_one = ica.get('partOne', {})
    lat = _clean_coord(part_one.get('lat'))
    lon = _clean_coord(part_one.get('long'))

    event_flag = ica.get('eventFlag')
    event_flag_value = event_flag[0] if isinstance(event_flag, tuple) else event_flag

    return {
        'type': 'ICA',
        'warning': True,
        'text': f'Intersection collision warning: {_ica_event_text(event_flag_value)}',
        'lat': lat,
        'lon': lon,
    }


def format_rsa(rsa: dict) -> dict:
    position = rsa.get('position', {})
    lat = _clean_coord(position.get('lat'))
    lon = _clean_coord(position.get('long'))

    labels = [_itis_label(rsa.get('typeEvent'))]
    labels += [_itis_label(code) for code in rsa.get('description', [])]

    return {
        'type': 'RSA',
        'warning': True,
        'text': _capitalize_first('; '.join(labels)),
        'lat': lat,
        'lon': lon,
    }
