"""
Named SDSM test scenarios - same "run a script, watch the real app" pattern
as mock_sender_gps_tests.py/mock_sender_test_cases.py (this project has no
formal test framework; every feature so far has been verified this way).

Unlike the mocked tracking feed, SDSM already has a real encoder
(backend/codec/SDSMEncoder.py) - this sends actual encoded hex frames to
the same UDP port ICA/RSA use (config.UDP_PORT), since that's how the real
dispatch works (one hex-over-UDP channel, told apart by the ASN.1 message
tag - see backend/decoder.py).

Run one scenario at a time:
    python mock_sender_sdsm_tests.py detected-scene
    python mock_sender_sdsm_tests.py single-vehicle
    python mock_sender_sdsm_tests.py obstacle
    python mock_sender_sdsm_tests.py moving
    python mock_sender_sdsm_tests.py no-signal
    python mock_sender_sdsm_tests.py signal-loss
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from mock_sender import INTERSECTION_LAT, INTERSECTION_LON, send_hex
from codec.SDSMEncoder import sdsm_encoder


def _sdsm_hex(msg_cnt: int, objects: list) -> str:
    """
    objects: list of per-object dicts (see scenarios below). Builds the
    parallel index-aligned lists sdsm_encoder expects - detVeh/detVRU/
    detObst-only params are still given one slot per object (unused slots
    are never read by the encoder since it branches on opt_type first, see
    SDSMEncoder.py), just to keep every list the same length as objects_N.
    """
    n = len(objects)
    return sdsm_encoder(
        msgCnt=msg_cnt % 128,
        sourceID='RSU1',
        equipmentType='rsu',
        sDSMTimeStamp_month=9, sDSMTimeStamp_day=17,
        sDSMTimeStamp_hour=12, sDSMTimeStamp_minute=0, sDSMTimeStamp_second=0.0,
        refPos_lat=INTERSECTION_LAT, refPos_long=INTERSECTION_LON, refPos_elevation=250.0,
        refPosXYConf_semiMajor=1.0, refPosXYConf_semiMinor=1.0, refPosXYConf_orientation=0.0,
        objects_N=n,
        objects_detObjCommon_objType=[o['obj_type'] for o in objects],
        objects_detObjCommon_objTypeCfd=[90] * n,
        objects_detObjCommon_objectID=[o['id'] for o in objects],
        objects_detObjCommon_measurementTime=[0.0] * n,
        objects_detObjCommon_timeConfidence=[0.01] * n,
        objects_detObjCommon_pos_offsetX=[o['offset_x'] for o in objects],
        objects_detObjCommon_pos_offsetY=[o['offset_y'] for o in objects],
        objects_detObjCommon_posConfidence_pos=[1.0] * n,
        objects_detObjCommon_posConfidence_elevation=[1.0] * n,
        objects_detObjCommon_speed=[o['speed'] for o in objects],
        objects_detObjCommon_speedConfidence=[95] * n,
        objects_detObjCommon_heading=[o['heading'] for o in objects],
        objects_detObjCommon_headingConf=[2.0] * n,
        objects_detObjOptData_type=[o['opt_type'] for o in objects],
        objects_detObjOptData_detVeh_size_width=[o.get('size_width', 1.8) for o in objects],
        objects_detObjOptData_detVeh_size_length=[o.get('size_length', 4.0) for o in objects],
        objects_detObjOptData_detVeh_lights=[o.get('lights', b'0') for o in objects],
        objects_detObjOptData_detVeh_vehicleClass=[o.get('vehicle_class', 0) for o in objects],
        objects_detObjOptData_detVRU_basicType=[o.get('basic_type', 'unavailable') for o in objects],
        objects_detObjOptData_detVRU_radius=[o.get('vru_radius_cm', 0) for o in objects],
        objects_detObjOptData_detObst_obstSize_width=[o.get('obst_width', 0.5) for o in objects],
        objects_detObjOptData_detObst_obstSize_length=[o.get('obst_length', 0.5) for o in objects],
        # the real ASN.1 schema requires obstSizeConfidence whenever detObst
        # is used, even though SDSMEncoder.py's own Python-side validation
        # treats it as optional (only sets it when both lists are given) -
        # omitting these makes pycrate reject the message at encode time
        # with "missing mandatory value(s): {'obstSizeConfidence'}"
        objects_detObjOptData_detObst_obstSizeConfidence_widthConfidence=[0.1] * n,
        objects_detObjOptData_detObst_obstSizeConfidence_lengthConfidence=[0.1] * n,
    )


def _send_sdsm(msg_cnt: int, objects: list, label: str):
    hex_sdsm = _sdsm_hex(msg_cnt, objects)
    send_hex(hex_sdsm, f'SDSM ({label})')


def detected_scene(duration_s: float = 30.0):
    """
    One reporting station (this intersection's RSU) sees 2 vehicles + 1
    pedestrian, looping - the main "does this render, on its own layer,
    with its own colors, not in the alert stack" check.
    """
    print(f'=== detected-scene: RSU sees 2 vehicles + 1 pedestrian for {duration_s:.0f}s - toggle "Show SDSM" on ===')
    objects = [
        {
            'id': 101, 'obj_type': 'vehicle', 'offset_x': 20.0, 'offset_y': 10.0,
            'speed': 8.0, 'heading': 270.0,
            'opt_type': 'Veh', 'size_width': 1.8, 'size_length': 4.5,
        },
        {
            'id': 102, 'obj_type': 'vehicle', 'offset_x': -15.0, 'offset_y': -6.0,
            'speed': 6.0, 'heading': 90.0,
            'opt_type': 'Veh', 'size_width': 1.9, 'size_length': 5.0,
        },
        {
            'id': 103, 'obj_type': 'vru', 'offset_x': -8.0, 'offset_y': 3.0,
            'speed': 1.2, 'heading': 200.0,
            'opt_type': 'VRU', 'basic_type': 'aPEDESTRIAN', 'vru_radius_cm': 40,
        },
    ]
    msg_cnt = 0
    end = time.time() + duration_s
    while time.time() < end:
        _send_sdsm(msg_cnt, objects, '2 vehicles + 1 pedestrian')
        msg_cnt += 1
        time.sleep(1.0)
    print('=== done ===')


def single_vehicle(duration_s: float = 20.0):
    """
    One vehicle with the richer optional detVeh fields set (size, lights,
    vehicle class) - confirms those decode and show up in the marker's
    tooltip (`detail`, see alert_formatter.py's _sdsm_object_detail()).
    """
    print(f'=== single-vehicle: one fully-described vehicle for {duration_s:.0f}s ===')
    objects = [
        {
            'id': 201, 'obj_type': 'vehicle', 'offset_x': 12.0, 'offset_y': -8.0,
            'speed': 10.0, 'heading': 45.0,
            'opt_type': 'Veh', 'size_width': 2.0, 'size_length': 5.2,
            'lights': b'2', 'vehicle_class': 10,  # leftTurnSignalOn
        },
    ]
    msg_cnt = 0
    end = time.time() + duration_s
    while time.time() < end:
        _send_sdsm(msg_cnt, objects, 'fully-described vehicle')
        msg_cnt += 1
        time.sleep(1.0)
    print('=== done ===')


def obstacle(duration_s: float = 20.0):
    """A static detObst object, no vehicle-only fields - confirms the 'obstacle' category/color renders."""
    print(f'=== obstacle: one static obstacle for {duration_s:.0f}s ===')
    objects = [
        {
            'id': 301, 'obj_type': 'unknown', 'offset_x': 6.0, 'offset_y': 6.0,
            'speed': 0.0, 'heading': 0.0,
            'opt_type': 'Obst', 'obst_width': 0.8, 'obst_length': 0.8,
        },
    ]
    msg_cnt = 0
    end = time.time() + duration_s
    while time.time() < end:
        _send_sdsm(msg_cnt, objects, 'static obstacle')
        msg_cnt += 1
        time.sleep(1.0)
    print('=== done ===')


def _moving_objects(t: float) -> list:
    """
    Same back-and-forth motion idea as mock_sender.py's
    simulate_tracking_objects(t), but directly in SDSM's own offset-from-
    refPos meters - no lat/lon conversion needed, unlike tracking.
    """
    return [
        {
            'id': 501, 'obj_type': 'vehicle',
            'offset_x': 30.0 - (t * 5.0 % 80.0), 'offset_y': 5.0,
            'speed': 8.0, 'heading': 270.0,  # moving west (offset_x decreasing)
            'opt_type': 'Veh', 'size_width': 1.8, 'size_length': 4.5,
        },
        {
            'id': 502, 'obj_type': 'vehicle',
            'offset_x': -5.0, 'offset_y': -20.0 + (t * 4.0 % 60.0),
            'speed': 6.0, 'heading': 0.0,  # moving north (offset_y increasing)
            'opt_type': 'Veh', 'size_width': 1.8, 'size_length': 4.5,
        },
        {
            'id': 503, 'obj_type': 'vru',
            'offset_x': -8.0 + (t * 1.0 % 16.0), 'offset_y': 0.0,
            'speed': 1.2, 'heading': 90.0,  # moving east (offset_x increasing)
            'opt_type': 'VRU', 'basic_type': 'aPEDESTRIAN', 'vru_radius_cm': 40,
        },
    ]


def moving():
    """
    Continuous frames - one message per second, indefinitely (Ctrl+C to
    stop), with objects actually moving frame to frame (unlike
    detected-scene/single-vehicle/obstacle above, which repeat the same
    fixed positions) - same "leave it running and watch" idiom as
    mock_sender.py's tracking_loop()/ego_loop(). Confirms markers update
    smoothly in place (not flicker/recreate) as real positions change.
    """
    print('=== moving: 3 objects continuously moving, one SDSM frame/second - Ctrl+C to stop ===')
    msg_cnt = 0
    t = 0.0
    try:
        while True:
            _send_sdsm(msg_cnt, _moving_objects(t), 'moving scene')
            msg_cnt += 1
            t += 1.0
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    print('=== done ===')


def no_signal():
    """Sends nothing - confirms SdsmInfoBox's "No SDSM data yet" state and that no stray markers appear."""
    print('=== no-signal: sending nothing - check the UI shows "No SDSM data yet" and no markers ===')
    print('(nothing to do - just open the app, toggle "Show SDSM" on, and look; Ctrl+C when done checking)')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


def signal_loss(active_s: float = 10.0, silent_s: float = 15.0):
    """Sends frames for a while, then stops - confirms markers/SdsmInfoBox clear themselves after SDSM_STALE_AFTER_MS, same as the ego marker."""
    print(f'=== signal-loss: {active_s:.0f}s of frames, then {silent_s:.0f}s of silence ===')
    objects = [
        {
            'id': 401, 'obj_type': 'vehicle', 'offset_x': 10.0, 'offset_y': 5.0,
            'speed': 5.0, 'heading': 180.0,
            'opt_type': 'Veh', 'size_width': 1.8, 'size_length': 4.5,
        },
    ]
    msg_cnt = 0
    end = time.time() + active_s
    while time.time() < end:
        _send_sdsm(msg_cnt, objects, 'signal-loss vehicle')
        msg_cnt += 1
        time.sleep(1.0)
    print(f'=== signal stopped - marker/SdsmInfoBox should clear within ~3s, unlike the frozen tracking feed ===')
    time.sleep(silent_s)
    print('=== done ===')


_SCENARIOS = {
    'detected-scene': detected_scene,
    'single-vehicle': single_vehicle,
    'obstacle': obstacle,
    'moving': moving,
    'no-signal': no_signal,
    'signal-loss': signal_loss,
}


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in _SCENARIOS:
        print(f'Usage: python mock_sender_sdsm_tests.py <{"|".join(_SCENARIOS)}>')
        sys.exit(1)

    _SCENARIOS[sys.argv[1]]()
