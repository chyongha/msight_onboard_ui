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


def send_ica_accidents(msg_cnt: int):
    hex_ica = ica_encoder(
        msgCnt=msg_cnt % 128, sourceID='RSU1',
        partOne_exists=True,
        partOne_msgCnt=msg_cnt % 128, partOne_sourceID='CAR1', partOne_secMark=12000,
        partOne_lat=INTERSECTION_LAT, partOne_long=INTERSECTION_LON, partOne_elev=250.0,
        partOnePosAcc_semiMajor=1.0, partOnePosAcc_semiMinor=1.0, partOnePosAcc_orientation=0.0,
        partOne_transmission='forwardGears', partOne_speed=12.0, partOne_heading=90.0,
        partOne_angle=0.0, partOne_accelSet_long=-1.0, partOne_accelSet_lat=0.0,
        partOne_accelSet_vert=0.0, partOne_accelSet_yaw=0.0,
        partOne_brakes_wheelBrakes=0, partOne_brakes_traction='off', partOne_brakes_abs='off',
        partOne_brakes_scs='off', partOne_brakes_brakeBoost='off', partOne_brakes_auxBrakes='off',
        partOne_size_width=180, partOne_size_length=450,
        path_exists=True, path_crumbData_N=1,
        path_crumbData_latOffset=[0.0], path_crumbData_lonOffset=[0.0],
        path_crumbData_elevationOffset=[0.0], path_crumbData_timeOffset=[0.1],
        intersectionID_id=1, laneNumber_type='approach', laneNumber_value=1,
        eventFlag_value=131,  # bit0, bit1, bit7
    )
    send_hex(hex_ica, 'ICA (Hazard Lights On, Stop Sign Violation, Hard Braking)')


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


def send_rsa_accidents(msg_cnt: int):
    hex_rsa = rsa_encoder(
        msgCnt=msg_cnt % 128,
        typeEvent=ITIS['accident-involving-a-pedestrian'],
        description=[ITIS['reduce-your-speed'], ITIS['crosswalks'], ITIS['minor-accident'], ITIS['reckless-driver']],
        priority=6,
        position_exists=True,
        position_lat=INTERSECTION_LAT, position_long=INTERSECTION_LON,
    )
    send_hex(hex_rsa, 'RSA (accident involving a pedestrian)')


if __name__ == '__main__':
    threading.Thread(target=tracking_loop, daemon=True).start()

    msg_cnt = 0
    while True:
        send_ica_accidents(msg_cnt)
        time.sleep(1)
        msg_cnt += 1

        time.sleep(4)  

        send_rsa_accidents(msg_cnt)
        time.sleep(1)
        msg_cnt += 1

        time.sleep(4)  
