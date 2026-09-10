"""
Deployment configuration
"""
import os

HOST = os.environ.get('BACKEND_HOST', '127.0.0.1') # if frontend and backend run on different server, change 127.0.0.1 to 0.0.0.0
PORT = int(os.environ.get('BACKEND_PORT', '5000')) 
UDP_PORT = int(os.environ.get('UDP_PORT', '4000'))
# Separate port for the live vehicle/pedestrian tracking feed
TRACKING_UDP_PORT = int(os.environ.get('TRACKING_UDP_PORT', '4001'))
# Separate port for this vehicle's own live GPS position (gps_bridge.py, real RTK GPS via ROS2 - or mock_sender.py's ego_loop() for local testing)
EGO_UDP_PORT = int(os.environ.get('EGO_UDP_PORT', '4002'))

# Origin(s) allowed to open a Socket.IO connection. '*' is fine for local
# dev (frontend + backend on the same machine, different ports). Once this
# runs somewhere with untrusted network access, set this to the real
# frontend's origin (e.g. 'http://192.168.1.50:3000') instead of '*'.
FRONTEND_ORIGIN = os.environ.get('FRONTEND_ORIGIN', '*')
