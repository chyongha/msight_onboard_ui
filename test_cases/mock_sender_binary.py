"""
Same ICA/RSA/SDSM messages as mock_sender.py, but sent the way a real RSU
does: raw binary UPER bytes in the UDP payload, NOT an ASCII hex string.
Use this to check the backend decodes what the real RSU actually sends.

    python mock_sender_binary.py            # send to the running backend, forever (Ctrl+C)
    python mock_sender_binary.py selftest   # no backend needed: encode -> raw bytes -> decode_message(), print result
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))

import mock_sender as m


def send_binary(hex_str: str, label: str, target=None):
    payload = bytes.fromhex(hex_str)
    m.sock.sendto(payload, target or m.ICA_TARGET)
    print(f'  sent {label} as {len(payload)} raw bytes (first byte 0x{payload[0]:02x})')


def selftest():
    from decoder import decode_message
    hexes = {}
    # capture what mock_sender's senders would send, instead of sending it
    m.send_hex = lambda h, label, target=None: hexes.__setitem__(label, h)
    m.send_ica_accidents(0)
    m.send_rsa_accidents(0)
    m.send_sdsm(0, m.simulate_sdsm_objects(0), 'moving scene')
    ok = True
    for label, h in hexes.items():
        payload = bytes.fromhex(h)
        try:
            event, msg = decode_message(payload)
            print(f'OK   {label}: {len(payload)} bytes -> event {event!r}, type {msg.get("type")!r}')
        except Exception as e:
            ok = False
            print(f'FAIL {label}: {e!r}')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'selftest':
        selftest()

    m.send_hex = lambda h, label, target=None: send_binary(h, label, target)  # send_ica/rsa_accidents look this up at call time
    i = 0
    while True:
        m.send_ica_accidents(i)
        m.send_sdsm(i, m.simulate_sdsm_objects(float(i)), 'moving scene')
        time.sleep(3)
        m.send_rsa_accidents(i)
        m.send_sdsm(i, m.simulate_sdsm_objects(float(i) + 0.5), 'moving scene')
        time.sleep(3)
        i += 1
