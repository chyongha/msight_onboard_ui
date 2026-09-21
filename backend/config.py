"""
Deployment configuration - every value can be overridden with an env var
"""
import os

HOST = os.environ.get('BACKEND_HOST', '127.0.0.1') # if frontend and backend run on different server, change 127.0.0.1 to 0.0.0.0
PORT = int(os.environ.get('BACKEND_PORT', '5000'))

# ica, rsa, sdsm, gps
UDP_ICA_PORT = int(os.environ.get('UDP_ICA_PORT', '4000'))
UDP_RSA_PORT = int(os.environ.get('UDP_RSA_PORT', '4001'))
UDP_SDSM_PORT = int(os.environ.get('UDP_SDSM_PORT', '4002'))
EGO_UDP_PORT = int(os.environ.get('EGO_UDP_PORT', '4003'))

# Origin(s) allowed to open a Socket.IO connection. 
# '*' is fine for local dev (frontend + backend on the same machine, different ports)
# if runs somewhere with untrusted network access, set this to the real frontend's origin
FRONTEND_ORIGIN = os.environ.get('FRONTEND_ORIGIN', '*')

# 1 - print the first bytes (hex) of every received packet - for checking what the RSU really sends
DEBUG_HEX = os.environ.get('DEBUG_HEX', '0') == '1'

# RSA alerts carry an `extent` (how far from the hazard they apply). When on,
# an RSA is dropped if this vehicle's latest GPS fix is farther than that
# from the hazard. No fix / a stale fix -> always shown (fail open).
RELEVANCE_FILTER = os.environ.get('RELEVANCE_FILTER', '1') == '1'
EGO_FRESH_S = float(os.environ.get('EGO_FRESH_S', '10'))  # a GPS fix older than this counts as "no fix"
