"""
Realistic-traffic scenarios, sent as raw binary like a real RSU (see
mock_sender_binary.py for the plain version). Unlike that one, each message
type runs on its OWN schedule, the way the real feeds behave:

  SDSM  - steady, every ~0.5s
  ICA / RSA - rare and irregular: random scenario, random gap
  ego GPS   - steady, every 0.5s (always JSON, as gps_bridge.py sends it)

Load deploy.env first so the ports match the backend:
    set -a; . ./deploy.env; set +a

    python mock_sender_binary_scenarios.py realistic [seconds]   # all of the above together
    python mock_sender_binary_scenarios.py sdsm-only [seconds]   # just the SDSM stream
    python mock_sender_binary_scenarios.py alerts-random [seconds]  # ICA/RSA at random times, nothing else
    python mock_sender_binary_scenarios.py burst                 # 6 alerts within ~3s (stack/overflow check)
    python mock_sender_binary_scenarios.py quiet-alert           # SDSM + GPS only, one alert after 15s, then silence
    python mock_sender_binary_scenarios.py out-of-range          # RSA (100m extent) sent while ego is 400m away (hidden), then 20m away (shown)

[seconds] is optional; without it, runs until Ctrl+C.
"""
import json
import random
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))

import mock_sender as m

SDSM_PERIOD_S = 0.5
EGO_PERIOD_S = 0.5
ALERT_GAP_S = (4.0, 15.0)   # random wait between ICA/RSA messages

_stop = threading.Event()


def _send_binary(hex_str: str, label: str, target=None):
    payload = bytes.fromhex(hex_str)
    m.sock.sendto(payload, target or m.ICA_TARGET)
    print(f'  sent {label} ({len(payload)} raw bytes)')


# mock_sender's send_ica/rsa_accidents look send_hex up at call time
m.send_hex = _send_binary


def sdsm_stream():
    t, cnt, last_log = 0.0, 0, 0.0
    while not _stop.is_set():
        payload = bytes.fromhex(m.sdsm_hex(cnt, m.simulate_sdsm_objects(t)))
        m.sock.sendto(payload, m.SDSM_TARGET)
        cnt += 1
        t += SDSM_PERIOD_S
        if time.time() - last_log > 10:
            last_log = time.time()
            print(f'  sdsm stream running ({cnt} sent so far, one every {SDSM_PERIOD_S}s)')
        _stop.wait(SDSM_PERIOD_S)


def ego_stream():
    t = 0.0
    while not _stop.is_set():
        m.sock.sendto(json.dumps(m.simulate_ego_position(t)).encode('utf-8'), m.EGO_TARGET)
        t += EGO_PERIOD_S
        _stop.wait(EGO_PERIOD_S)


def random_alerts(first_delay=None):
    cnt = 0
    _stop.wait(first_delay if first_delay is not None else random.uniform(*ALERT_GAP_S))
    while not _stop.is_set():
        if random.random() < 0.5:
            m.send_ica_accidents(cnt, random.randrange(len(m._ICA_SCENARIOS)))
        else:
            m.send_rsa_accidents(cnt, random.randrange(len(m._RSA_SCENARIOS)))
        cnt += 1
        _stop.wait(random.uniform(*ALERT_GAP_S))


def _run(threads, duration_s):
    for th in threads:
        th.start()
    try:
        _stop.wait(duration_s)  # None = until Ctrl+C
    except KeyboardInterrupt:
        pass
    _stop.set()
    print('=== stopped ===')


def _thread(fn, *args):
    return threading.Thread(target=fn, args=args, daemon=True)


def realistic(duration_s=None):
    print('=== realistic: SDSM + GPS steady, ICA/RSA at random intervals ===')
    _run([_thread(sdsm_stream), _thread(ego_stream), _thread(random_alerts)], duration_s)


def sdsm_only(duration_s=None):
    print('=== sdsm-only ===')
    _run([_thread(sdsm_stream)], duration_s)


def alerts_random(duration_s=None):
    print('=== alerts-random: ICA/RSA only, random scenario + random gap ===')
    _run([_thread(random_alerts, 1.0)], duration_s)


def burst(duration_s=None):
    print('=== burst: 6 alerts ~0.5s apart, with SDSM + GPS running underneath ===')
    threads = [_thread(sdsm_stream), _thread(ego_stream)]
    for th in threads:
        th.start()
    time.sleep(2)
    for i in range(6):
        if i % 2 == 0:
            m.send_ica_accidents(i, i % len(m._ICA_SCENARIOS))
        else:
            m.send_rsa_accidents(i, i % len(m._RSA_SCENARIOS))
        time.sleep(0.5)
    print('  ...burst done; leaving SDSM/GPS running 15s to watch the alerts clear')
    _run([], 15)


def quiet_alert(duration_s=None):
    print('=== quiet-alert: SDSM + GPS only, one RSA after 15s, then silence ===')
    threads = [_thread(sdsm_stream), _thread(ego_stream)]
    for th in threads:
        th.start()
    time.sleep(15)
    m.send_rsa_accidents(0, 0)
    _run([], 20)


def _send_ego_at(east_m: float, seconds: float):
    lat, lon = m.offset_latlon(m.INTERSECTION_LAT, m.INTERSECTION_LON, east_m, 0.0)
    end = time.time() + seconds
    while time.time() < end:
        m.sock.sendto(json.dumps({'lat': lat, 'lon': lon, 'timestamp': time.time()}).encode('utf-8'), m.EGO_TARGET)
        time.sleep(EGO_PERIOD_S)


def out_of_range(duration_s=None):
    """
    RSA scenario 0 has extent useFor100meters and sits at the mock intersection.
    Ego 400m away -> backend should print 'RSA hidden' and the UI shows nothing;
    ego 20m away -> the same RSA is shown.
    """
    print('=== out-of-range: ego 400m away -> RSA hidden; ego 20m away -> RSA shown ===')
    _send_ego_at(400.0, 2)
    print('  ego is 400m from the hazard, sending RSA (100m extent) - expect it hidden')
    m.send_rsa_accidents(0, 0)
    _send_ego_at(400.0, 4)
    _send_ego_at(20.0, 2)
    print('  ego is 20m from the hazard, sending the same RSA - expect it shown')
    m.send_rsa_accidents(1, 0)
    _send_ego_at(20.0, 8)
    print('=== done ===')


_SCENARIOS = {
    'realistic': realistic,
    'sdsm-only': sdsm_only,
    'alerts-random': alerts_random,
    'burst': burst,
    'quiet-alert': quiet_alert,
    'out-of-range': out_of_range,
}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in _SCENARIOS:
        print(f'Usage: python mock_sender_binary_scenarios.py <{"|".join(_SCENARIOS)}> [seconds]')
        sys.exit(1)
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else None
    _SCENARIOS[sys.argv[1]](dur)
