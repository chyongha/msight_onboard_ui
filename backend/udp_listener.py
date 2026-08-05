"""
Owns UDP sockets: receive raw bytes, hand them to a decode function, emit
the result on a named socket event. Two independent listeners run this
same loop on different ports — ICA/RSA alerts, and (mocked for now, see
tracking_formatter.py's docstring) live tracking frames.
"""
import json
import socket
import threading

from decoder import decode_message
from tracking_formatter import format_tracking_frame


def _listen_loop(socketio, host, port, decode_fn, emit_event):
    # creates a udp socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # SOCK_DGRAM = UDP
    sock.bind((host, port))
    print(f'  [udp] Listening on {host}:{port} -> {emit_event!r} events')

    while True:
        raw_bytes, addr = sock.recvfrom(4096)  # raw_bytes - actual byte that was sent / addr - (sender_ip, sender_port)
        try:
            message = decode_fn(raw_bytes)
        except Exception as e:
            print(f'  [udp] Failed to decode packet from {addr} on port {port}: {e}')
            continue

        socketio.emit(emit_event, message)


def start_udp_listener(socketio, host='0.0.0.0', port=4000):
    """
    ICA/RSA alerts -> 'warning' events. Starts on a background thread so
    it doesn't block the Flask-SocketIO server.
    """
    threading.Thread(
        target=_listen_loop, args=(socketio, host, port, decode_message, 'warning'),
        daemon=True,
    ).start()


def _decode_tracking_frame(raw_bytes: bytes) -> dict:
    # MOCK wire format: plain JSON — NOT the real encoding a real live-
    # tracking feed would use (that'd very likely be hex-encoded UPER,
    # like ICA/RSA, once a real decoder exists). See mock_sender.py's
    # docstring for the exact schema this expects. Swapping in a real
    # decoder later means replacing this function's body only —
    # format_tracking_frame() and everything downstream doesn't change.
    raw = json.loads(raw_bytes.decode('utf-8'))
    return format_tracking_frame(raw)


def start_tracking_listener(socketio, host='0.0.0.0', port=4001):
    """Live object tracking (mocked) -> 'frame' events."""
    threading.Thread(
        target=_listen_loop, args=(socketio, host, port, _decode_tracking_frame, 'frame'),
        daemon=True,
    ).start()
