"""
Decides whether an alert applies to this vehicle

extent is (`extent_m` by alert_formatter.py) is how far from the hazard the alert applies, so it's
relevant only while this vehicle is within that distance

If not sure, just show it
"""
import time

import config
from geometry import distance_m

_ego = None  # (lat, lon, received_at) 


def update_ego(fix: dict):
    global _ego
    lat, lon = fix.get('lat'), fix.get('lon')
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
        _ego = (lat, lon, time.time())


def is_relevant(message: dict) -> tuple[bool, str]:
    """(show?, reason it was hidden - empty when shown)"""
    if not config.RELEVANCE_FILTER or message.get('type') != 'RSA':
        return True, ''

    extent_m = message.get('extent_m')
    lat, lon = message.get('lat'), message.get('lon')
    if extent_m is None or not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return True, ''

    ego = _ego
    if ego is None or time.time() - ego[2] > config.EGO_FRESH_S:
        return True, ''

    dist = distance_m(ego[0], ego[1], lat, lon)
    if dist > extent_m:
        return False, f'vehicle is {dist:.0f} m from the hazard, alert only applies within {extent_m} m'
    return True, ''
