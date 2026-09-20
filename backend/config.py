"""
Deployment configuration - every value can be overridden with an env var
(see run_backend.sh at the project root, which sets them in one place).
"""
import os

HOST = os.environ.get('BACKEND_HOST', '127.0.0.1') # if frontend and backend run on different server, change 127.0.0.1 to 0.0.0.0
PORT = int(os.environ.get('BACKEND_PORT', '5000'))

# The RSU sends ICA, RSA and SDSM on three different UDP ports
UDP_ICA_PORT = int(os.environ.get('UDP_ICA_PORT', '4000'))
UDP_RSA_PORT = int(os.environ.get('UDP_RSA_PORT', '4001'))
UDP_SDSM_PORT = int(os.environ.get('UDP_SDSM_PORT', '4002'))
# Separate port for this vehicle's own live GPS position (gps_bridge.py, real RTK GPS via ROS2 - or mock_sender.py's ego_loop() for local testing)
EGO_UDP_PORT = int(os.environ.get('EGO_UDP_PORT', '4003'))

# Origin(s) allowed to open a Socket.IO connection. '*' is fine for local
# dev (frontend + backend on the same machine, different ports). Once this
# runs somewhere with untrusted network access, set this to the real
# frontend's origin (e.g. 'http://192.168.1.50:3000') instead of '*'.
FRONTEND_ORIGIN = os.environ.get('FRONTEND_ORIGIN', '*')
