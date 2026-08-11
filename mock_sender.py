"""
sends real, encoded ICA and RSA messages over UDP to test the backend +
frontend without needing a real RSU
"""
import json
import socket
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

import config
from codec.ICAEncoder import ica_encoder
from codec.RSAEncoder import rsa_encoder
from codec.itis_codes import ITIS
from geometry import offset_latlon

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
TARGET = ('127.0.0.1', config.UDP_PORT)
TRACKING_TARGET = ('127.0.0.1', config.TRACKING_UDP_PORT)

# random coordinates
INTERSECTION_LAT = 39.99
INTERSECTION_LON = -83.00


def send_hex(hex_str: str, label: str):
    sock.sendto(hex_str.encode('ascii'), TARGET)
    print(f'  sent {label} ({len(hex_str)} hex chars)')


_ICA_SCENARIOS = [
    {
        'label': 'Hazard Lights On, Stop Sign Violation, Hard Braking',
        'source_id': 'CAR1',
        'eventFlag_value': 131,  # bit0, bit1, bit7
        'brakes_traction': 'engaged', 'brakes_abs': 'engaged', 'brakes_scs': 'off',
        'speed': 12.0, 'heading': 15.0,
        'steering': 15.0, 'accel_long': -6.0, 'accel_lat': 0.5, 'accel_yaw': 2.0,
    },
    {
        'label': 'Hazard Lights On only (caution)',
        'source_id': 'CAR2',
        'eventFlag_value': 1,  # bit0
        'brakes_traction': 'off', 'brakes_abs': 'off', 'brakes_scs': 'off',
        'speed': 8.0, 'heading': 15.0,
        'steering': 1.0, 'accel_long': -0.5, 'accel_lat': 0.0, 'accel_yaw': 0.0,
    },
    {
        'label': 'Stability Control + Traction Loss',
        'source_id': 'CAR3',
        'eventFlag_value': 24,  # bit3, bit4
        'brakes_traction': 'engaged', 'brakes_abs': 'off', 'brakes_scs': 'engaged',
        'speed': 15.0, 'heading': 15.0,
        'steering': -25.0, 'accel_long': -2.0, 'accel_lat': 5.0, 'accel_yaw': 35.0,
    },
    {
        'label': 'Flat Tire, Disabled Vehicle',
        'source_id': 'CAR4',
        'eventFlag_value': 3072,  # bit10, bit11
        'brakes_traction': 'off', 'brakes_abs': 'off', 'brakes_scs': 'off',
        'speed': 0.5, 'heading': 95.0,  # near-stopped - disabled, not braking
        'steering': 0.0, 'accel_long': 0.0, 'accel_lat': 0.0, 'accel_yaw': 0.0,
    },
    {
        'label': 'Air Bag Deployment, Jackknife, Hard Braking',
        'source_id': 'CAR5',
        'eventFlag_value': 12416,  # bit7, bit12, bit13
        'brakes_traction': 'engaged', 'brakes_abs': 'engaged', 'brakes_scs': 'engaged',
        'speed': 0.2, 'heading': 200.0,  # post-crash, essentially stopped
        'steering': 30.0, 'accel_long': -8.0, 'accel_lat': 6.0, 'accel_yaw': 45.0,
    },
]


def send_ica_accidents(msg_cnt: int, scenario_index: int = None):
    """
    scenario_index picks a specific scenario directly (used by the demo
    drivers below, so they don't have to reverse-engineer
    `msg_cnt % len(_ICA_SCENARIOS)`) - defaults to rotating through them by
    msg_cnt, as before.
    """
    index = scenario_index if scenario_index is not None else msg_cnt % len(_ICA_SCENARIOS)
    scenario = _ICA_SCENARIOS[index]


    crumb_lat_offsets = [-0.00014, -0.00011, -0.00008, -0.00004, -0.00001]
    crumb_lon_offsets = [-0.00004, -0.00003, -0.00002, -0.00001, -0.000003]
    crumb_time_offsets = [2.0, 1.5, 1.0, 0.5, 0.1] 

    hex_ica = ica_encoder(
        msgCnt=msg_cnt % 128, sourceID='RSU1',
        partOne_exists=True,
        partOne_msgCnt=msg_cnt % 128, partOne_sourceID=scenario['source_id'], partOne_secMark=12000,
        partOne_lat=INTERSECTION_LAT, partOne_long=INTERSECTION_LON, partOne_elev=250.0,
        partOnePosAcc_semiMajor=1.0, partOnePosAcc_semiMinor=1.0, partOnePosAcc_orientation=0.0,
        partOne_transmission='forwardGears', partOne_speed=scenario['speed'], partOne_heading=scenario['heading'],
        partOne_angle=scenario['steering'], partOne_accelSet_long=scenario['accel_long'], partOne_accelSet_lat=scenario['accel_lat'],
        partOne_accelSet_vert=0.0, partOne_accelSet_yaw=scenario['accel_yaw'],
        partOne_brakes_wheelBrakes=0, partOne_brakes_traction=scenario['brakes_traction'],
        partOne_brakes_abs=scenario['brakes_abs'], partOne_brakes_scs=scenario['brakes_scs'],
        partOne_brakes_brakeBoost='off', partOne_brakes_auxBrakes='off',
        partOne_size_width=180, partOne_size_length=450,
        path_exists=True, path_crumbData_N=5,
        path_crumbData_latOffset=crumb_lat_offsets, path_crumbData_lonOffset=crumb_lon_offsets,
        path_crumbData_elevationOffset=[0.0] * 5, path_crumbData_timeOffset=crumb_time_offsets,
        intersectionID_id=1, laneNumber_type='approach', laneNumber_value=1,
        eventFlag_value=scenario['eventFlag_value'],
    )
    send_hex(hex_ica, f'ICA ({scenario["label"]})')


_RSA_SCENARIOS = [
    {
        'label': 'accident involving a pedestrian (critical, pedestrian)',
        'typeEvent': 'accident-involving-a-pedestrian',
        'description': ['reduce-your-speed', 'crosswalks', 'minor-accident', 'reckless-driver'],
        'priority': 6,
        'position_heading': 200.0, 'position_speed': 6.0,
        'extent': 'useFor100meters',
        # HeadingSlice bitmask - which compass directions this alert applies
        # to (not this scenario's own heading above - see _rsa_heading_slices
        # in alert_formatter.py). Same value the supervisor's reference
        # script uses - verified against the real ASN.1 schema this actually
        # lights N/SSE/S/NNW, not "east and west" as that script's comment claims.
        'heading': 0x8181,
    },
    {
        'label': 'wet pavement ahead (caution, weather)',
        'typeEvent': 'wet-pavement',
        'description': ['reduce-your-speed', 'drive-with-extreme-caution'],
        'priority': 3,
        'position_heading': 80.0, 'position_speed': 11.0,
        'extent': 'useFor1000meters',
    },
    {
        'label': 'debris on roadway (info, road hazard)',
        'typeEvent': 'debris-on-roadway',
        'description': ['approach-with-care'],
        'priority': 1,
        'position_heading': 300.0, 'position_speed': 13.0,
    },
    {
        'label': 'black ice ahead (critical via priority, weather)',
        'typeEvent': 'black-ice',
        'description': ['reduce-your-speed', 'drive-with-extreme-caution'],
        'priority': 5,
        'position_heading': 350.0, 'position_speed': 9.0,
        'extent': 'useFor500meters',
        'heading': 0x0808,  # genuinely E+W this time (index4=E -> python bit11=2048, index12=W -> python bit3=8)
    },
    {
        'label': 'vehicle on fire (critical, vehicle)',
        'typeEvent': 'vehicle-on-fire',
        'description': ['reduce-your-speed', 'approach-with-care'],
        'priority': 6,
        'position_heading': 120.0, 'position_speed': 14.0,
        'extent': 'useInstantlyOnly',
    },
]


def send_rsa_accidents(msg_cnt: int, scenario_index: int = None):
    index = scenario_index if scenario_index is not None else msg_cnt % len(_RSA_SCENARIOS)
    scenario = _RSA_SCENARIOS[index]
    hex_rsa = rsa_encoder(
        msgCnt=msg_cnt % 128,
        typeEvent=ITIS[scenario['typeEvent']],
        description=[ITIS[name] for name in scenario['description']],
        priority=scenario['priority'],
        position_exists=True,
        position_lat=INTERSECTION_LAT, position_long=INTERSECTION_LON,
        position_heading=scenario['position_heading'],
        position_speed_transmission='forwardGears',
        position_speed_velocity=scenario['position_speed'],
        extent=scenario.get('extent'),  # omitted entirely (not defaulted) when a scenario doesn't set one
        heading=scenario.get('heading'),  # HeadingSlice bitmask - also omitted when unset
    )
    send_hex(hex_rsa, f'RSA ({scenario["label"]})')


# live tracking 
def simulate_tracking_objects(t: float):
    objects = []

    v1_east = 30.0 - (t * 5.0 % 80.0)
    v1_lat, v1_lon = offset_latlon(INTERSECTION_LAT, INTERSECTION_LON, v1_east, 5.0)
    objects.append({
        'id': 1, 'lat': v1_lat, 'lon': v1_lon, 'category': 'vehicle',
        'speed': 8.0, 'heading_deg': 270.0, 'length_m': 4.5, 'width_m': 1.8,
    })

    v2_east, v2_north = -5.0, -20.0 + (t * 4.0 % 60.0)
    v2_lat, v2_lon = offset_latlon(INTERSECTION_LAT, INTERSECTION_LON, v2_east, v2_north)
    objects.append({
        'id': 2, 'lat': v2_lat, 'lon': v2_lon, 'category': 'vehicle',
        'speed': 6.0, 'heading_deg': 0.0, 'length_m': 4.5, 'width_m': 1.8,
    })

    p_east = -8.0 + (t * 1.0 % 16.0)
    p_lat, p_lon = offset_latlon(INTERSECTION_LAT, INTERSECTION_LON, p_east, 0.0)
    objects.append({
        'id': 3, 'lat': p_lat, 'lon': p_lon, 'category': 'vru',
        'speed': 1.2, 'heading_deg': 90.0,
    })

    return objects


def tracking_loop():
    t = 0.0
    while True:
        payload = {'objects': simulate_tracking_objects(t), 'timestamp': time.time()}
        sock.sendto(json.dumps(payload).encode('utf-8'), TRACKING_TARGET)
        t += 0.2
        time.sleep(0.2)


# demo 
def send_events_sequence():
    msg_cnt = 0

    def ica(scenario_index):
        nonlocal msg_cnt
        send_ica_accidents(msg_cnt, scenario_index=scenario_index)
        msg_cnt += 1

    def rsa(scenario_index):
        nonlocal msg_cnt
        send_rsa_accidents(msg_cnt, scenario_index=scenario_index)
        msg_cnt += 1

    print('============demo for events sent within 5 sec tiemframe===========')
    num = 1
    while num <= 3:
        print(f"demo #{num}")
        for i in range(len(_ICA_SCENARIOS)):
            ica(i)
            time.sleep(1)
        time.sleep(3)
        for i in range(len(_RSA_SCENARIOS)):
            rsa(i)
            time.sleep(1)
        for i in range(min(len(_ICA_SCENARIOS), len(_RSA_SCENARIOS))):
            ica(i)
            time.sleep(1)
            rsa(i)
            time.sleep(1)
        time.sleep(5)
        num += 1

    print('done')


def send_events_tgt():
    msg_cnt = 0

    def ica(scenario_index):
        nonlocal msg_cnt
        send_ica_accidents(msg_cnt, scenario_index=scenario_index)
        msg_cnt += 1

    def rsa(scenario_index):
        nonlocal msg_cnt
        send_rsa_accidents(msg_cnt, scenario_index=scenario_index)
        msg_cnt += 1

    num = 0
    print('===========begin testing=============')
    while num <= 3:
        print(f"event #{num}")
        for i in range(min(len(_ICA_SCENARIOS), len(_RSA_SCENARIOS))):
            ica(i)
            rsa(i)
            time.sleep(3)
        num += 1
    print("-===done========")


def send_stack_demo():
    msg_cnt = 0

    def ica(scenario_index):
        nonlocal msg_cnt
        send_ica_accidents(msg_cnt, scenario_index=scenario_index)
        msg_cnt += 1

    def rsa(scenario_index):
        nonlocal msg_cnt
        send_rsa_accidents(msg_cnt, scenario_index=scenario_index)
        msg_cnt += 1

    print('\n=== stack demo ===')
    print('[t=0.0s] two alerts at the same instant: CAR1 + a pedestrian accident')
    ica(0)  # CAR1 - hazard lights, stop line violation, hard braking
    rsa(0)  # accident involving a pedestrian

    time.sleep(6)
    print('[t=1.5s] a second, different vehicle')
    ica(1)  # CAR2 - hazard lights only (caution)
    time.sleep(2)
    rsa(1)

    time.sleep(5)
    print('[t=3.2s] another road hazard')
    rsa(3)  # wet pavement (caution)
    ica(3)

    print('=== demo sent - all 4 stay stacked, then expire on their own 5s timers ===\n')


if __name__ == '__main__':
    threading.Thread(target=tracking_loop, daemon=True).start()
    mode = sys.argv[1] if len(sys.argv) > 1 else None

    if mode == 'stack-demo':
        send_stack_demo()

    elif mode == 'demo-sequence':
        send_events_sequence()

    elif mode == 'demo-tgt':
        send_events_tgt()
    
    time.sleep(5)
    while True:
        for i in range(len(_ICA_SCENARIOS)):
            send_ica_accidents(i)
            time.sleep(6)
            send_rsa_accidents(i)
            time.sleep(6)


        time.sleep(3)
