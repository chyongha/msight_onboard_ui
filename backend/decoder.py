"""
Turns raw bytes into dictionary {type, warning, text, lat, lon}  that gets socketio.emit() to the frontend
RSU sends out hex strings 

Message-type dispatch: ica_decoder() and rsa_decoder() each assume the hex
string decodes to their own message type and will crash on the wrong one
(e.g. ica_decoder() raises on RSA's missing 'id' field). ASN.1 CHOICE
encoding is self-describing though — the UPER bits themselves say which
alternative was encoded — so we do one generic MessageFrame decode first
to read that off, then call the matching decoder.
"""
from binascii import unhexlify

from codec.utils import load_v2xlib
from codec.ICADecoder import ica_decoder
from codec.RSADecoder import rsa_decoder
from alert_formatter import format_ica, format_rsa

v2xlib = load_v2xlib()

# ASN.1 CHOICE alternative name (set by ica_encoder()/rsa_encoder() as the
# first element of header['value']) -> (decode_fn, format_fn).
_DISPATCH = {
    'IntersectionCollision': (ica_decoder, format_ica),
    'RoadSideAlert': (rsa_decoder, format_rsa),
}


def _peek_message_type(hex_str: str) -> str:
    frame = v2xlib.MessageFrame.MessageFrame
    frame.from_uper_ws(unhexlify(hex_str))
    return frame()['value'][0]


def decode_message(raw_bytes: bytes) -> dict:
    hex_str = raw_bytes.decode('ascii').strip()

    # check message type - ICA or RSA
    msg_type = _peek_message_type(hex_str)
    if msg_type not in _DISPATCH:
        raise ValueError(f'Unrecognized message type: {msg_type!r}')

    decode_fn, format_fn = _DISPATCH[msg_type]
    decoded = decode_fn(hex_str)
    return format_fn(decoded)
