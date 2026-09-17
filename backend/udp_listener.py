"""
Receive raw bytes, hand them to a decode function, emit the result on a named socket event.
Three independent listeners run this same loop on different ports — ICA/RSA/SDSM alerts, live
tracking frames, and this vehicle's own GPS.
"""
import json
import socket
import threading

from decoder import decode_message
from tracking_formatter import format_tracking_frame


def _listen_loop(socketio, host, port, decode_fn, default_event):
    # creates a udp socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # SOCK_DGRAM = UDP
    sock.bind((host, port))
    print(f'  [udp] Listening on {host}:{port} -> {default_event!r} events')

    while True:
        raw_bytes, addr = sock.recvfrom(4096)  # raw_bytes - actual byte that was sent / addr - (sender_ip, sender_port)
        try:
            # decode_fn returns (event_name, message) - the event isn't
            # always fixed per-port, e.g. port 4000 carries both ICA/RSA
            # ('warning') and SDSM ('sdsm'), told apart only after decoding
            event, message = decode_fn(raw_bytes)
        except Exception as e:
            print(f'  [udp] Failed to decode packet from {addr} on port {port}: {e}')
            continue

        socketio.emit(event, message)


def start_udp_listener(socketio, host='0.0.0.0', port=4000):
    """
    ICA/RSA -> 'warning' events, SDSM -> 'sdsm' events (same port, told
    apart by the ASN.1 message tag - see decoder.py). Starts on a background
    thread so it doesn't block the Flask-SocketIO server.
    """
    threading.Thread(
        target=_listen_loop, args=(socketio, host, port, decode_message, 'warning/sdsm'),
        daemon=True,
    ).start()


def _decode_tracking_frame(raw_bytes: bytes) -> tuple[str, dict]:
    # Not the real encoding a real-time tracking would use - replace with real decoder later
    raw = json.loads(raw_bytes.decode('utf-8'))
    return 'frame', format_tracking_frame(raw)


def start_tracking_listener(socketio, host='0.0.0.0', port=4001):
    """Live object tracking (mocked) -> 'frame' events."""
    threading.Thread(
        target=_listen_loop, args=(socketio, host, port, _decode_tracking_frame, 'frame'),
        daemon=True,
    ).start()


def _decode_ego_frame(raw_bytes: bytes) -> tuple[str, dict]:
    # Already flat lat, long, timestamp format received by the gps_bridge.py or mock_sender.py
    return 'ego', json.loads(raw_bytes.decode('utf-8'))


def start_ego_listener(socketio, host='0.0.0.0', port=4002):
    """Live ego (this vehicle's own GPS) position -> 'ego' events."""
    threading.Thread(
        target=_listen_loop, args=(socketio, host, port, _decode_ego_frame, 'ego'),
        daemon=True,
    ).start()
