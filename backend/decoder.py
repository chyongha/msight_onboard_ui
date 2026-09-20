"""
Turns raw bytes into dictionary {type, warning, text, lat, lon}  that gets socketio.emit() to the frontend
RSU sends out hex strings 
"""
from binascii import unhexlify

from codec.utils import load_v2xlib
from codec.ICADecoder import ica_decoder
from codec.RSADecoder import rsa_decoder
from codec.SDSMDecoder import sdsm_decoder
from alert_formatter import format_ica, format_rsa, format_sdsm

v2xlib = load_v2xlib()

_DISPATCH = {
    'IntersectionCollision': (ica_decoder, format_ica, 'warning'),
    'RoadSideAlert': (rsa_decoder, format_rsa, 'warning'),
    'SensorDataSharingMessage': (sdsm_decoder, format_sdsm, 'sdsm'),
}


def _peek_message_type(hex_str: str) -> str:
    """
    Check the message type
    """
    frame = v2xlib.MessageFrame.MessageFrame
    frame.from_uper_ws(unhexlify(hex_str))
    return frame()['value'][0]


def _to_hex_str(raw_bytes: bytes) -> str:
    """
    RSU - raw binary UPER bytes
    mock_sender.py - ASCII hex string. 
    if the payload is entirely hex characters treat it as the mock's text form, otherwise hex-encode it
    """
    try:
        text = raw_bytes.decode('ascii').strip()
        int(text, 16)
        return text
    except (UnicodeDecodeError, ValueError):
        return raw_bytes.hex()


def decode_message(raw_bytes: bytes) -> tuple[str, dict]:
    """
    Perform decoding using the alert_formatter functions.
    returns event name, socket dictionary
    """
    hex_str = _to_hex_str(raw_bytes)

    # check message type 
    msg_type = _peek_message_type(hex_str)
    if msg_type not in _DISPATCH:
        raise ValueError(f'Unrecognized message type: {msg_type!r}')

    decode_fn, format_fn, event = _DISPATCH[msg_type]
    decoded = decode_fn(hex_str)
    return event, format_fn(decoded)
