"""Minimal HS256 JWT — uses only stdlib (hmac, hashlib, base64, json)."""
import base64
import hashlib
import hmac
import json
import time
from typing import Optional


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    if pad != 4:
        s += "=" * pad
    return base64.urlsafe_b64decode(s)


def encode(payload: dict, secret: str) -> str:
    header  = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body    = _b64url_encode(json.dumps(payload).encode())
    signing = f"{header}.{body}".encode()
    sig     = hmac.new(secret.encode(), signing, hashlib.sha256).digest()
    return f"{header}.{body}.{_b64url_encode(sig)}"


def decode(token: str, secret: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Malformed token")

    header_b64, body_b64, sig_b64 = parts
    expected = hmac.new(
        secret.encode(),
        f"{header_b64}.{body_b64}".encode(),
        hashlib.sha256,
    ).digest()

    if not hmac.compare_digest(expected, _b64url_decode(sig_b64)):
        raise ValueError("Invalid signature")

    payload = json.loads(_b64url_decode(body_b64))
    exp: Optional[float] = payload.get("exp")
    if exp is not None and time.time() > exp:
        raise ValueError("Token expired")
    return payload
