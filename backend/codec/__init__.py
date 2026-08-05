"""
J2735 RSA/ICA encode/decode — vendored from the separate msight_codec
project. Kept as a self-contained package because its modules use
relative imports (`from .utils import load_v2xlib`) between each other.

The one thing NOT in here is v2xlib.py/v2xlib.json themselves (the
pycrate-generated ASN.1 codec) — those are supplied at runtime via the
PYV2XLIB_VENDOR_DIR environment variable, not bundled in this repo.
"""
