"""
    Testing Four Events 
    Event 1. ICA message about stop-line violation
    Event 2. ICA message about hard braking 
    Event 3. RSA message about pedestrian accident 
    Event 4. RSA message about runaway vehicle accident 
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

import config
from codec.ICAEncoder import ica_encoder
from codec.RSAEncoder import rsa_encoder
from mock_sender import sock, ICA_TARGET, RSA_TARGET, INTERSECTION_LAT, INTERSECTION_LON, send_hex  


def send_stopline_violation():
    """
    ICA - stop-line violation (eventFlag bit 1)
    """
    hex_ica = ica_encoder(
        msgCnt=1, sourceID='RSU1', iCATimeStamp=133064,  

        partOne_exists=True,
        partOne_msgCnt=1, partOne_sourceID='CSL1', partOne_secMark=55487,  
        partOne_lat=INTERSECTION_LAT, partOne_long=INTERSECTION_LON, partOne_elev=250.0,
        partOnePosAcc_semiMajor=1.05, partOnePosAcc_semiMinor=4.7, partOnePosAcc_orientation=50.5,
        partOne_transmission='forwardGears', partOne_speed=25.0, partOne_heading=45.0, partOne_angle=10.0,
        partOne_accelSet_long=-10.79, partOne_accelSet_lat=-7.8, partOne_accelSet_vert=-11.57, partOne_accelSet_yaw=271.91,
        partOne_brakes_wheelBrakes=12, partOne_brakes_traction='unavailable', partOne_brakes_abs='engaged',
        partOne_brakes_scs='off', partOne_brakes_brakeBoost='on', partOne_brakes_auxBrakes='off',
        partOne_size_width=288, partOne_size_length=86,

        path_exists=False,

        intersectionID_id=4086, intersectionID_region=9520,
        laneNumber_type='lane', laneNumber_value=9,

        eventFlag_value=2,  # bit1 
    )
    send_hex(hex_ica, 'ICA (stop-line violation)', ICA_TARGET)


def send_hard_braking():
    """
    ICA - hard braking 
    """
    hex_ica = ica_encoder(
        msgCnt=2, sourceID='RSU1', iCATimeStamp=133064,

        partOne_exists=True,
        partOne_msgCnt=2, partOne_sourceID='CHB1', partOne_secMark=55487, 
        partOne_lat=INTERSECTION_LAT, partOne_long=INTERSECTION_LON, partOne_elev=250.0,
        partOnePosAcc_semiMajor=1.05, partOnePosAcc_semiMinor=4.7, partOnePosAcc_orientation=50.5,
        partOne_transmission='forwardGears', partOne_speed=25.0, partOne_heading=45.0, partOne_angle=10.0,
        partOne_accelSet_long=-15.0, partOne_accelSet_lat=-2.0, partOne_accelSet_vert=-1.5, partOne_accelSet_yaw=5.0,
        partOne_brakes_wheelBrakes=31, partOne_brakes_traction='on', partOne_brakes_abs='engaged',
        partOne_brakes_scs='engaged', partOne_brakes_brakeBoost='on', partOne_brakes_auxBrakes='on',
        partOne_size_width=288, partOne_size_length=86,

        path_exists=False,

        intersectionID_id=4086, intersectionID_region=9520,
        laneNumber_type='lane', laneNumber_value=9,

        eventFlag_value=128,  # bit7 
    )
    send_hex(hex_ica, 'ICA (hard braking)', ICA_TARGET)


def send_pedestrian_accident_rsa():
    """
    RSA - accident involving a pedestrian
    """
    hex_rsa = rsa_encoder(
        msgCnt=1,
        timeStamp=133100,  
        typeEvent=522,  # accident-involving-a-pedestrian

        description=[
            9486,  # pedestrians
            8032,  # intersection
            7443,  # reduce-your-speed 
        ],

        priority=7,
        heading=0x8181,  # east + west 
        extent='useFor500meters',  

        position_exists=True,
        position_long=INTERSECTION_LON, position_lat=INTERSECTION_LAT,
        position_elevation=250.0,
        position_heading=180.0,
        position_speed_transmission='park',
        position_speed_velocity=0.0, 
    )
    send_hex(hex_rsa, 'RSA (pedestrian accident)', RSA_TARGET)


def send_runaway_vehicle_rsa():
    """
    RSA - runaway vehicle accident
    """
    hex_rsa = rsa_encoder(
        msgCnt=2,
        timeStamp=133064,

        typeEvent=517,  # multi-vehicle-accident

        description=[
            9256,  # runaway-vehicles 
            8032,  # intersection 
            7993,  # cross-traffic 
            7175,  # cross-intersection-with-care
        ],

        priority=6,
        heading=0x8181,
        extent='useFor500meters',

        position_exists=True,
        position_long=INTERSECTION_LON, position_lat=INTERSECTION_LAT,
        position_elevation=250.0,
        position_heading=90.0,
        position_speed_transmission='forwardGears',
        position_speed_velocity=45.0,  # runaway vehicle - elevated speed
    )
    send_hex(hex_rsa, 'RSA (runaway vehicle accident)', RSA_TARGET)


_CASES = {
    'stopline': ('ICA - stop-line violation', send_stopline_violation),
    'hardbraking': ('ICA - hard braking', send_hard_braking),
    'pedestrian': ('RSA - pedestrian accident', send_pedestrian_accident_rsa),
    'runaway': ('RSA - runaway vehicle accident', send_runaway_vehicle_rsa),
}


if __name__ == '__main__':
    if len(sys.argv) > 1:
        name = sys.argv[1]
        if name not in _CASES:
            print(f'Unknown case {name!r} - choose from: {", ".join(_CASES)}')
            sys.exit(1)
        label, fn = _CASES[name]
        print(f'=== {label} ===')
        fn()
        sys.exit(0)

    print('=== sending all 4 test cases, 3s apart (for the demo recording) ===')
    time.sleep(3)
    for name, (label, fn) in _CASES.items():
        print(f'\n[{name}] {label}')
        fn()
        time.sleep(8)
    print('\n=== done - each alert clears itself ~5s after its last broadcast ===')
