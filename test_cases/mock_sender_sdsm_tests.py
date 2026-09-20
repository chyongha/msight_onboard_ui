"""
Named SDSM test scenarios - same "run a script, watch the real app" pattern
as mock_sender_gps_tests.py/mock_sender_test_cases.py (this project has no
formal test framework; every feature so far has been verified this way).

Unlike the mocked tracking feed, SDSM already has a real encoder
(backend/codec/SDSMEncoder.py) - this sends actual encoded hex frames to
the same UDP port ICA/RSA use (config.UDP_PORT), since that's how the real
dispatch works (one hex-over-UDP channel, told apart by the ASN.1 message
tag - see backend/decoder.py). The encoding itself (sdsm_hex()) and a
default continuously-moving scene (simulate_sdsm_objects()) live in
mock_sender.py now, since `python mock_sender.py` on its own also sends a
live SDSM feed alongside ICA/RSA/ego - this file is just for the extra
named scenarios (a static/rich vehicle, an obstacle, staleness checks)
that script doesn't cover.

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

from mock_sender import send_sdsm as _send_sdsm, simulate_sdsm_objects


def detected_scene(duration_s: float = 30.0):
    """
    One reporting station (this intersection's RSU) sees 2 vehicles + 1
    pedestrian, looping - the main "does this render, on its own layer,
    with its own colors, not in the alert stack" check.
    """
    print(f'=== detected-scene: RSU sees 2 vehicles + 1 pedestrian for {duration_s:.0f}s ===')
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


def moving():
    """
    Continuous frames - one message per second, indefinitely (Ctrl+C to
    stop), with objects actually moving frame to frame (unlike
    detected-scene/single-vehicle/obstacle above, which repeat the same
    fixed positions) - same "leave it running and watch" idiom as
    mock_sender.py's ego_loop()/sdsm_loop(). Confirms markers update
    smoothly in place (not flicker/recreate) as real positions change.
    This is the same scene mock_sender.py's own sdsm_loop() sends by
    default - useful to run standalone when you want SDSM moving without
    ICA/RSA/ego also running.
    """
    print('=== moving: 3 objects continuously moving, one SDSM frame/second - Ctrl+C to stop ===')
    msg_cnt = 0
    t = 0.0
    try:
        while True:
            _send_sdsm(msg_cnt, simulate_sdsm_objects(t), 'moving scene')
            msg_cnt += 1
            t += 1.0
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    print('=== done ===')


def no_signal():
    """Sends nothing - confirms SdsmInfoBox's "No SDSM data yet" state and that no stray markers appear."""
    print('=== no-signal: sending nothing - check the UI shows "No SDSM data yet" and no markers ===')
    print('(nothing to do - just open the app in Both/Map view and look; Ctrl+C when done checking)')
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
