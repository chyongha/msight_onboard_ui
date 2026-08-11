"""
Backend

Frontend runs on its own dev server and talks to backend over socketio 
"""
from flask import Flask
from flask_socketio import SocketIO

import config
from udp_listener import start_udp_listener, start_tracking_listener

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins=config.FRONTEND_ORIGIN) # tells flask to accept socketio connection from frontend

if __name__ == '__main__':
    # start listening for UDP packets on background threads
    start_udp_listener(socketio, port=config.UDP_PORT) # background thread 1 - ica/rsa alerts and emitting warning events 
    start_tracking_listener(socketio, port=config.TRACKING_UDP_PORT) # background thread 2 - tracking objects 

    print(f'Backend running at http://{config.HOST}:{config.PORT}')
    socketio.run(app, host=config.HOST, port=config.PORT, allow_unsafe_werkzeug=True) # main thread running forever