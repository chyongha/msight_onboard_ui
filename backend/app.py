"""
Backend

This does NOT serve the frontend — with Vite, the frontend runs on its own
dev server (usually http://localhost:5173) and talks to this backend over
Socket.IO (default http://localhost:5000). Two separate processes while
developing; only combined at build/deploy time if you choose to.

Host/port/origin come from config.py (env vars) rather than being
hardcoded, so this same code runs on a dev laptop or a deployed roadside
box without source edits — see config.py and README.md for the env vars.
"""
from flask import Flask
from flask_socketio import SocketIO

import config
from udp_listener import start_udp_listener, start_tracking_listener

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins=config.FRONTEND_ORIGIN)

if __name__ == '__main__':
    # start listening for UDP packets on background threads
    start_udp_listener(socketio, port=config.UDP_PORT)
    start_tracking_listener(socketio, port=config.TRACKING_UDP_PORT)

    print(f'Backend running at http://{config.HOST}:{config.PORT}')
    # allow_unsafe_werkzeug=True: fine for local dev (no eventlet/gevent
    # installed here, per requirements.txt using simple-websocket instead).
    # Flask-SocketIO otherwise refuses to run its dev server this way
    socketio.run(app, host=config.HOST, port=config.PORT, allow_unsafe_werkzeug=True)
