"""
Receive raw bytes, hand them to a decode function, emit the result on a named socket event.

The RSU sends ICA, RSA and SDSM on separate UDP ports, one listener each.
decode_message() peeks the ASN.1 tag, so each listener would decode any of
the three - the port split only matters for where packets arrive.
"""
import json
import socket
import threading
import time

from decoder import decode_message


def _listen_loop(socketio, host, port, decode_fn, name):
    # creates a udp socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # SOCK_DGRAM = UDP
    sock.bind((host, port))
    print(f'  [udp] Listening on {host}:{port} ({name})')

    last_sdsm_log = 0.0
    while True:
        raw_bytes, addr = sock.recvfrom(4096)  # raw_bytes - actual bytes that were sent / addr - (sender_ip, sender_port)
        try:
            event, message = decode_fn(raw_bytes) 
        except Exception as e:
            print(f'  [udp] Failed to decode {name} packet from {addr} on port {port}: {e!r}')
            continue

        # ICA/RSA -> log each one 
        # SDSM -> one line summary per 10 sec
        if event == 'warning':
            print(f'  [udp] {message.get("type")} from {addr[0]}: {message.get("text")}')
        elif event == 'sdsm' and time.time() - last_sdsm_log > 10:
            last_sdsm_log = time.time()
            print(f'  [udp] SDSM from {addr[0]}: {len(message.get("objects", []))} object(s) (logged every 10s)')

        socketio.emit(event, message)


def _start(socketio, host, port, decode_fn, name):
    threading.Thread(
        target=_listen_loop, args=(socketio, host, port, decode_fn, name),
        daemon=True,
    ).start()

def _decode_ego_frame(raw_bytes: bytes) -> tuple[str, dict]:
    # Already flat lat, long, timestamp JSON format from gps_bridge.py
    return 'ego', json.loads(raw_bytes.decode('utf-8'))

def start_ica_listener(socketio, host='0.0.0.0', port=4000):
    """background thread listening to ICA messages"""
    _start(socketio, host, port, decode_message, 'ICA')


def start_rsa_listener(socketio, host='0.0.0.0', port=4001):
    """background thread listening to RSA messages"""
    _start(socketio, host, port, decode_message, 'RSA')


def start_sdsm_listener(socketio, host='0.0.0.0', port=4002):
    """background thread listening to SDSM messages"""
    _start(socketio, host, port, decode_message, 'SDSM')


def start_ego_listener(socketio, host='0.0.0.0', port=4003):
    """Own vehicle position"""
    _start(socketio, host, port, _decode_ego_frame, 'ego GPS')
