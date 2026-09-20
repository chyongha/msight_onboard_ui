"""
Backend

Frontend runs on its own dev server and talks to backend over socketio 
"""
from flask import Flask
from flask_socketio import SocketIO

import config
from udp_listener import start_ica_listener, start_rsa_listener, start_sdsm_listener, start_ego_listener

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins=config.FRONTEND_ORIGIN) # main thread - tells flask to accept socketio connection from frontend

if __name__ == '__main__':
    # start listening for UDP packets on background threads
    start_ica_listener(socketio, port=config.UDP_ICA_PORT) # background thread 1 - ica
    start_rsa_listener(socketio, port=config.UDP_RSA_PORT) # background thread 2 - rsa
    start_sdsm_listener(socketio, port=config.UDP_SDSM_PORT) # background thread 3 - sdsm
    start_ego_listener(socketio, port=config.EGO_UDP_PORT) # background thread 4 - vehicle gps location 

    print(f'Backend running at http://{config.HOST}:{config.PORT}')
    socketio.run(app, host=config.HOST, port=config.PORT, allow_unsafe_werkzeug=True) # main thread running forever