# MedPharm ERP - Copyright (C) 2026 Enlightec Ltd.
# Licensed under the GNU General Public License v3.0 or later.
"""
RFC 6238 TOTP implementation for optional multi-factor auth.

Compatible with Google Authenticator, 1Password, Authy, etc. Deliberately
zero-dependency so deployments without a full `pyotp` install still work.
"""

import base64
import hashlib
import hmac
import secrets
import struct
import time
import urllib.parse


def generate_totp_secret(length_bytes: int = 20) -> str:
    return base64.b32encode(secrets.token_bytes(length_bytes)).decode("ascii").rstrip("=")


def _hotp(secret_b32: str, counter: int, digits: int = 6) -> str:
    padding = "=" * (-len(secret_b32) % 8)
    key = base64.b32decode(secret_b32 + padding, casefold=True)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    snippet = (
        (digest[offset] & 0x7F) << 24
        | (digest[offset + 1] & 0xFF) << 16
        | (digest[offset + 2] & 0xFF) << 8
        | (digest[offset + 3] & 0xFF)
    )
    return str(snippet % (10 ** digits)).zfill(digits)


def current_totp(secret_b32: str, step: int = 30, digits: int = 6,
                 now: float | None = None) -> str:
    now = now if now is not None else time.time()
    return _hotp(secret_b32, int(now // step), digits)


def verify_totp_code(secret_b32: str, code: str, *, window: int = 1,
                     step: int = 30, digits: int = 6,
                     now: float | None = None) -> bool:
    if not code or not secret_b32:
        return False
    code = code.strip().replace(" ", "")
    if len(code) != digits or not code.isdigit():
        return False
    now = now if now is not None else time.time()
    counter = int(now // step)
    for drift in range(-window, window + 1):
        if hmac.compare_digest(_hotp(secret_b32, counter + drift, digits), code):
            return True
    return False


def generate_totp_uri(secret_b32: str, account_name: str,
                      issuer: str = "MedPharm ERP") -> str:
    label = urllib.parse.quote(f"{issuer}:{account_name}")
    params = urllib.parse.urlencode({
        "secret": secret_b32,
        "issuer": issuer,
        "algorithm": "SHA1",
        "digits": 6,
        "period": 30,
    })
    return f"otpauth://totp/{label}?{params}"
