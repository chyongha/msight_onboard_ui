"""
lat/lon <-> local meters

Uses a flat-earth (equirectangular) approximation rather than a real
geodetic projection library
"""
import math

_METERS_PER_DEG_LAT = 111320.0


def meters_per_deg_lon(lat_deg: float) -> float:
    return _METERS_PER_DEG_LAT * math.cos(math.radians(lat_deg))


def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line meters between two lat/lon points (same flat-earth approximation as above)."""
    north = (lat2 - lat1) * _METERS_PER_DEG_LAT
    east = (lon2 - lon1) * meters_per_deg_lon((lat1 + lat2) / 2)
    return math.hypot(east, north)


def offset_latlon(lat: float, lon: float, east_m: float, north_m: float):
    """(lat, lon) shifted by (east_m, north_m) meters."""
    dlat = north_m / _METERS_PER_DEG_LAT
    dlon = east_m / meters_per_deg_lon(lat)
    return lat + dlat, lon + dlon


def rectangle_corners_latlon(lat: float, lon: float, heading_deg: float,
                              length_m: float, width_m: float):
    """4 corners of a vehicle-footprint rectangle centered at (lat, lon),
    as [lat, lon] pairs, front-right/front-left/rear-left/rear-right order.

    heading_deg: compass heading, clockwise from north (0=N, 90=E) -- same
    convention as ICA/RSA's heading fields elsewhere in this repo, chosen
    deliberately so there's one heading convention across the whole app.
    """
    heading_rad = math.radians(heading_deg)
    hl = max(length_m, 0.1) / 2.0
    hw = max(width_m, 0.1) / 2.0
    sin_h = math.sin(heading_rad)
    cos_h = math.cos(heading_rad)

    corners = []
    for forward, left in ((hl, -hw), (hl, hw), (-hl, hw), (-hl, -hw)):
        east = forward * sin_h - left * cos_h
        north = forward * cos_h + left * sin_h
        c_lat, c_lon = offset_latlon(lat, lon, east, north)
        corners.append([round(c_lat, 7), round(c_lon, 7)])
    return corners
