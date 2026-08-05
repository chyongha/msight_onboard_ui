"""
Deployment configuration
"""
import os

HOST = os.environ.get('BACKEND_HOST', '127.0.0.1')
PORT = int(os.environ.get('BACKEND_PORT', '5000'))
UDP_PORT = int(os.environ.get('UDP_PORT', '4000'))
# Separate port for the (currently mocked — see tracking_formatter.py and
# mock_sender.py) live vehicle/pedestrian tracking feed, so it can't
# collide with or complicate the already-working ICA/RSA decode path on
# UDP_PORT above.
TRACKING_UDP_PORT = int(os.environ.get('TRACKING_UDP_PORT', '4001'))

# Origin(s) allowed to open a Socket.IO connection. '*' is fine for local
# dev (frontend + backend on the same machine, different ports). Once this
# runs somewhere with untrusted network access, set this to the real
# frontend's origin (e.g. 'http://192.168.1.50:3000') instead of '*'.
FRONTEND_ORIGIN = os.environ.get('FRONTEND_ORIGIN', '*')
