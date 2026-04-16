# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
# Email: Andrew.Stillwell@enlightec.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
MedPharm ERP - JWT Authentication for REST API
Provides token-based authentication for mobile/cloud clients.
"""

import os
import time
import hmac
import hashlib
import base64
import json
from functools import wraps

from flask import request, jsonify, g


# ── JWT-like Token Implementation ─────────────────────────────────────────────
# Uses HMAC-SHA256 for signing. Tokens are base64url-encoded JSON payloads.

_SECRET_KEY = os.environ.get("MEDPHARM_JWT_SECRET", "medpharm-dev-secret-change-in-production")
_TOKEN_EXPIRY_SECONDS = int(os.environ.get("MEDPHARM_TOKEN_EXPIRY", 86400))  # 24 hours
_REFRESH_EXPIRY_SECONDS = int(os.environ.get("MEDPHARM_REFRESH_EXPIRY", 604800))  # 7 days


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _sign(payload_b64: str) -> str:
    signature = hmac.new(
        _SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256
    ).digest()
    return _b64url_encode(signature)


def create_token(user_type: str, user_id: int, patient_id: int = None,
                 username: str = "", role: str = "", name: str = "",
                 is_refresh: bool = False) -> str:
    expiry = _REFRESH_EXPIRY_SECONDS if is_refresh else _TOKEN_EXPIRY_SECONDS
    payload = {
        "user_type": user_type,  # "staff" or "patient"
        "user_id": user_id,
        "patient_id": patient_id,
        "username": username,
        "role": role,
        "name": name,
        "iat": int(time.time()),
        "exp": int(time.time()) + expiry,
        "typ": "refresh" if is_refresh else "access",
    }
    payload_json = json.dumps(payload, separators=(",", ":"))
    payload_b64 = _b64url_encode(payload_json.encode("utf-8"))
    sig = _sign(payload_b64)
    return f"{payload_b64}.{sig}"


def decode_token(token: str) -> dict | None:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig = parts
        expected_sig = _sign(payload_b64)
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload_json = _b64url_decode(payload_b64).decode("utf-8")
        payload = json.loads(payload_json)
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


# ── Flask Decorators ──────────────────────────────────────────────────────────

def token_required(f):
    """Require a valid access token (staff or patient)."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header[7:]
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        if payload.get("typ") != "access":
            return jsonify({"error": "Access token required"}), 401
        g.token_payload = payload
        g.current_user_type = payload["user_type"]
        g.current_user_id = payload["user_id"]
        g.current_patient_id = payload.get("patient_id")
        g.current_role = payload.get("role", "")
        return f(*args, **kwargs)
    return wrapper


def patient_required(f):
    """Require a valid patient access token."""
    @wraps(f)
    @token_required
    def wrapper(*args, **kwargs):
        if g.current_user_type != "patient":
            return jsonify({"error": "Patient access required"}), 403
        return f(*args, **kwargs)
    return wrapper


def staff_required(f):
    """Require a valid staff access token."""
    @wraps(f)
    @token_required
    def wrapper(*args, **kwargs):
        if g.current_user_type != "staff":
            return jsonify({"error": "Staff access required"}), 403
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    """Require a valid admin staff access token."""
    @wraps(f)
    @token_required
    def wrapper(*args, **kwargs):
        if g.current_user_type != "staff" or g.current_role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return wrapper
