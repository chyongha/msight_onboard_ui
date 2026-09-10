"""
Named GPS test scenarios for the live-map ego marker + coordinates box -
same "run a script, watch the real app" pattern as mock_sender_test_cases.py
(this project has no formal test framework; every feature so far has been
verified this way).

Reuses mock_sender.py's existing socket/target/coordinates/helper rather
than duplicating them - this file only adds new *scenarios*, not new
plumbing.

Run one scenario at a time:
    python mock_sender_gps_tests.py moving
    python mock_sender_gps_tests.py stationary
    python mock_sender_gps_tests.py no-signal
    python mock_sender_gps_tests.py signal-loss
    python mock_sender_gps_tests.py with-alerts
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from mock_sender import (
    sock, EGO_TARGET, INTERSECTION_LAT, INTERSECTION_LON,
    simulate_ego_position, send_ica_accidents, send_rsa_accidents,
)
from geometry import offset_latlon


def send_ego_fix(lat: float, lon: float):
    sock.sendto(json.dumps({'lat': lat, 'lon': lon, 'timestamp': time.time()}).encode('utf-8'), EGO_TARGET)


def moving(duration_s: float = 30.0):
    """Baseline - the same back-and-forth path mock_sender.py's ego_loop() sends continuously."""
    print(f'=== moving: sending a back-and-forth GPS path for {duration_s:.0f}s ===')
    t = 0.0
    end = time.time() + duration_s
    while time.time() < end:
        fix = simulate_ego_position(t)
        sock.sendto(json.dumps(fix).encode('utf-8'), EGO_TARGET)
        t += 0.5
        time.sleep(0.5)
    print('=== done ===')


def stationary(duration_s: float = 15.0):
    """
    Fixed lat/lon sent repeatedly - confirms a parked/non-moving vehicle
    renders correctly and repeated identical fixes don't cause flicker.
    """
    print(f'=== stationary: sending the same fixed GPS position for {duration_s:.0f}s ===')
    lat, lon = offset_latlon(INTERSECTION_LAT, INTERSECTION_LON, 5.0, -8.0)
    end = time.time() + duration_s
    while time.time() < end:
        send_ego_fix(lat, lon)
        time.sleep(0.5)
    print('=== done ===')


def no_signal():
    """
    Sends nothing at all, on purpose - confirms EgoCoordinatesBox's "No GPS
    signal yet" state and that no stray marker appears on the map.
    """
    print('=== no-signal: sending nothing - check the UI shows "No GPS signal yet" and no marker ===')
    print('(nothing to do - just open the app and look; Ctrl+C when done checking)')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


def signal_loss(active_s: float = 10.0, silent_s: float = 20.0):
    """
    Sends fixes for a while, then stops - shows what a dropout looks like
    today: the marker/box just freeze at the last known fix, no "stale"
    indicator. This scenario is for SEEING that plainly, not a claim that
    anything new was built to handle it - that wasn't asked for.
    """
    print(f'=== signal-loss: {active_s:.0f}s of fixes, then {silent_s:.0f}s of silence ===')
    t = 0.0
    end = time.time() + active_s
    while time.time() < end:
        fix = simulate_ego_position(t)
        sock.sendto(json.dumps(fix).encode('utf-8'), EGO_TARGET)
        t += 0.5
        time.sleep(0.5)
    print(f'=== signal stopped - marker/box should now be frozen at the last fix for {silent_s:.0f}s ===')
    time.sleep(silent_s)
    print('=== done ===')


def with_alerts():
    """
    Runs the moving GPS path *and* fires a couple of ICA/RSA alerts at the
    same time - the direct test for "alerts block the map": flip through
    Both/Map/Alerts in the UI while both are live and confirm each mode
    shows exactly what it should.
    """
    print('=== with-alerts: moving GPS path + two alerts, ~20s - switch view modes while this runs ===')
    t = 0.0
    msg_cnt = 0
    next_ica_at = 2.0
    next_rsa_at = 6.0
    end = time.time() + 20.0
    start = time.time()
    while time.time() < end:
        elapsed = time.time() - start
        fix = simulate_ego_position(t)
        sock.sendto(json.dumps(fix).encode('utf-8'), EGO_TARGET)
        t += 0.5

        if next_ica_at is not None and elapsed >= next_ica_at:
            send_ica_accidents(msg_cnt, scenario_index=0)  # CAR1 - hazard lights, stop line violation, hard braking
            msg_cnt += 1
            next_ica_at = None
        if next_rsa_at is not None and elapsed >= next_rsa_at:
            send_rsa_accidents(msg_cnt, scenario_index=0)  # accident involving a pedestrian
            msg_cnt += 1
            next_rsa_at = None

        time.sleep(0.5)
    print('=== done - both alerts clear themselves ~7s after their last broadcast ===')


_SCENARIOS = {
    'moving': moving,
    'stationary': stationary,
    'no-signal': no_signal,
    'signal-loss': signal_loss,
    'with-alerts': with_alerts,
}


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in _SCENARIOS:
        print(f'Usage: python mock_sender_gps_tests.py <{"|".join(_SCENARIOS)}>')
        sys.exit(1)

    _SCENARIOS[sys.argv[1]]()
