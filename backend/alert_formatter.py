"""
Turns a decoded ICA/RSA dict (rich, deeply nested, matches the ASN.1
message layout) into the flat shape the frontend actually renders:

    {type, warning, text, lat, lon}

Both ICA and RSA are alert-only message types — per ICA's own docstring,
its existence IS "a warning that a vehicle is likely entering an
intersection without the right of way." There's no expected "all clear"
message, so `warning` is always True here — clearing the banner after a
period of silence is the frontend's job (useSocket.js), not something
decided from message content.
"""
from codec.itis_codes import ITIS

_ITIS_NAME_BY_CODE = {code: name for name, code in ITIS.items()}

# ICA eventFlag bit -> human text. See ICAEncoder.py's docstring for the
# full 14-bit layout; only the ones useful on a warning banner are named.
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
    """itis_codes.py keys are dashed slugs ('accident-involving-a-pedestrian')
    — fine as dict keys, not as banner text. Just despace the dashes."""
    return name.replace('-', ' ')


def _capitalize_first(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def _itis_label(code) -> str:
    if code is None:
        return 'unknown event'
    name = _ITIS_NAME_BY_CODE.get(code)
    return _humanize(name) if name else f'ITIS code {code}'


def _ica_event_text(event_flag_value) -> str:
    if not isinstance(event_flag_value, int):
        return 'vehicle approaching intersection without right of way'
    active = [label for bit, label in _ICA_EVENT_BITS.items() if event_flag_value & (1 << bit)]
    if not active:
        return 'vehicle approaching intersection without right of way'
    return ', '.join(active)


def _clean_coord(value):
    """ICADecoder.py/RSADecoder.py use the string 'unavailable' as their
    sentinel for a missing lat/long. Normalize that to None for the
    frontend/map rather than leaking the sentinel string through."""
    return None if value == 'unavailable' else value


def format_ica(ica: dict) -> dict:
    part_one = ica.get('partOne', {})
    lat = _clean_coord(part_one.get('lat'))
    lon = _clean_coord(part_one.get('long'))

    event_flag = ica.get('eventFlag')
    # ica_decoder() doesn't unwrap the (value, bit_length) tuple ICAEncoder
    # builds for eventFlag, so handle both shapes defensively.
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
