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

# J2735 DSRCmsgID 
_MSG_ID_ICA = 23 # 0x17
_MSG_ID_RSA = 27 #0x1b
_MSG_ID_SDSM = 41 #0x29

_DISPATCH = {
    _MSG_ID_ICA: (ica_decoder, format_ica, 'warning'),
    _MSG_ID_RSA: (rsa_decoder, format_rsa, 'warning'),
    _MSG_ID_SDSM: (sdsm_decoder, format_sdsm, 'sdsm'),
}


_NAME_TO_ID = {
    'IntersectionCollision': _MSG_ID_ICA,
    'RoadSideAlert': _MSG_ID_RSA,
    'SensorDataSharingMessage': _MSG_ID_SDSM,
}


def _peek_message_id(hex_str: str) -> int:
    """
    1. J2735 encoded message starts with 1 extension bit + the 15-bit DSRCmsgID, 
        so the ID is the first 2 bytes masked to 15 bits
    2. If 1 doesnt work, let pycrate parse the whole MessageFrame
    """
    fast_id = int(hex_str[:4], 16) & 0x7FFF
    if fast_id in _DISPATCH:
        return fast_id
    try:
        frame = v2xlib.MessageFrame.MessageFrame
        frame.from_uper_ws(unhexlify(hex_str))
        name = frame()['value'][0]
        if name in _NAME_TO_ID:
            return _NAME_TO_ID[name]
    except Exception:
        pass
    return fast_id  # not one of ours - caller reports it


def _to_hex_str(raw_bytes: bytes) -> str:
    """
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
    returns event name, socket dictionary
    """
    hex_str = _to_hex_str(raw_bytes)

    # check message type 
    msg_id = _peek_message_id(hex_str)
    if msg_id not in _DISPATCH:
        raise ValueError(f'Unrecognized message id: {msg_id} (0x{msg_id:04x}), starts with hex {hex_str[:24]}')

    decode_fn, format_fn, event = _DISPATCH[msg_id]
    decoded = decode_fn(hex_str)
    return event, format_fn(decoded)
