"""
ITIS code lookup - got from the v2xlib.py J2540ITIS class
from itis_codes import ITIS
"""

ITIS = {
    # Accidents and Incidents (513-639)
    'accident': 513,
    'serious-accident': 514,
    'injury-accident': 515,
    'minor-accident': 516,
    'multi-vehicle-accident': 517,
    'accident-involving-a-bicycle': 519,
    'accident-involving-a-bus': 520,
    'accident-involving-a-motorcycle': 521,
    'accident-involving-a-pedestrian': 522,
    'accident-involving-a-truck': 524,
    'medical-emergency': 527,
    'incident': 531,
    'stalled-vehicle': 532,
    'abandoned-vehicle': 533,
    'disabled-vehicle': 534,
    'vehicle-on-fire': 540,
    'overturned-vehicle': 554,
    'accident-cleared': 638,
    'incident-cleared': 639,

    # Closures (769-895)
    'closed-to-traffic': 769,
    'closed': 770,
    'closed-ahead': 771,
    'blocked': 775,
    'blocked-ahead': 776,
    'reduced-to-one-lane': 777,
    'reduced-to-two-lanes': 778,
    'open-to-traffic': 891,
    'open': 892,
    'reopened-to-traffic': 893,
    'cleared-from-road': 895,

    # Roadwork (1025-1151)
    'road-construction': 1025,
    'construction-work': 1028,
    'road-maintenance-operations': 1036,
    'road-work-cleared': 1151,

    # Obstruction (1281-1407)
    'obstruction-on-roadway': 1281,
    'object-on-roadway': 1282,
    'debris-on-roadway': 1284,
    'people-on-roadway': 1286,
    'animal-on-roadway': 1290,
    'pothole': 1300,
    'flooding': 1301,
    'obstruction-cleared': 1407,

    # Unusual Driving (1793-1919)
    'vehicle-traveling-wrong-way': 1793,
    'reckless-driver': 1794,
    'prohibited-vehicle-on-roadway': 1795,
    'emergency-vehicles-on-roadway': 1796,
    'high-speed-emergency-vehicles': 1797,
    'high-speed-chase': 1798,
    'dangerous-vehicle-warning-cleared': 1918,
    'emergency-vehicle-warning-cleared': 1919,

    # Device Status (2305-2431)
    'traffic-lights-not-working': 2313,
    'traffic-signals-repaired': 2430,

    # Restriction Class (2561-2687)
    'speed-restriction': 2564,
    'no-through-traffic': 2571,
    'height-limit': 2574,

    # Incident Response Status (2817-2833)
    'unconfirmed-report': 2817,
    'confirmed-report': 2822,
    'incident-closed': 2833,

    # Weather / Pavement (4609-4991, 5889-6015)
    'heavy-rain': 4884,
    'rain': 4885,
    'dense-fog': 5377,
    'fog': 5378,
    'wet-pavement': 5895,
    'black-ice': 5908,
    'snow-on-roadway': 5916,

    # Warning / Danger Advice (6913-7039)
    'risk': 6913,
    'watch': 6914,
    'warning': 6915,
    'alert': 6916,
    'danger': 6917,
    'increased-risk-of-accident': 6922,
    'police-at-scene': 6924,
    'police-directing-traffic': 6927,
    'warning-canceled': 7034,
    'cleared': 7038,

    # Advice / Instructions - Recommendations (7169-7205)
    'drive-carefully': 7169,
    'drive-with-extreme-caution': 7170,
    'approach-with-care': 7171,
    'keep-your-distance': 7172,
    'increase-normal-following-distance': 7173,
    'cross-intersection-with-care': 7175,
    'use-hazard-warning-lights': 7179,
    'prepare-to-stop': 7186,
    'stop-at-next-safe-place': 7188,

    # Advice / Instructions - Mandatory (7425-7454, 7547)
    'no-passing': 7433,
    'allow-emergency-vehicles-to-pass': 7438,
    'pull-over-to-the-edge-of-the-roadway': 7440,
    'reduce-your-speed': 7443,
    'observe-speed-limits': 7444,
    'stay-in-lane': 7450,

    # Generic Locations (7937-8034)
    'on-bridges': 7937,
    'in-tunnels': 7938,
    'in-road-construction-area': 7941,
    'in-the-median': 7948,
    'on-the-roadway': 7951,
    'north': 7998,
    'south': 7999,
    'east': 8000,
    'west': 8001,
    'shoulder': 8027,
    'bus-stop': 8031,
    'intersection': 8032,

    # VehicleGroupAffected (9217-9261) - scoping tag, not an event
    'bicycles': 9218,

    # TravelerGroupAffected (9473-9487) - scoping tag, not an event
    'pedestrian': 9486,

    # RoadsideAssets (10496-10573)
    'countdown-pedestrian-sign': 10571,

    # Objects (11009-11064)
    'pedestrian-Signal-Stop': 11042,
    'pedestrian-Signal-Caution': 11043,
    'pedestrian-Signal-Walk': 11044,
    'pedestrian-Signal-Light': 11045,
    'pedestrian-Signal-Time-Display': 11046,

    # MUTCD Locations (13569-13641)
    'ahead': 13569,
    'right': 13579,
    'left': 13580,
    'crossing': 13585,
    'crosswalks': 13586,
}