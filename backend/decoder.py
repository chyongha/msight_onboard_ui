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


def decode_message(raw_bytes: bytes) -> tuple[str, dict]:
    """
    Perform decoding using the alert_formatter functions.
    Returns (socket_event_name, formatted_dict).
    """
    hex_str = raw_bytes.decode('ascii').strip()

    # check message type - ICA, RSA, or SDSM
    msg_type = _peek_message_type(hex_str)
    if msg_type not in _DISPATCH:
        raise ValueError(f'Unrecognized message type: {msg_type!r}')

    decode_fn, format_fn, event = _DISPATCH[msg_type]
    decoded = decode_fn(hex_str)
    return event, format_fn(decoded)
