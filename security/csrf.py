# MedPharm ERP - Copyright (C) 2026 Enlightec Ltd.
# Licensed under the GNU General Public License v3.0 or later.
"""
Minimal CSRF protection for Flask form POSTs.

We do not take a Flask-WTF dependency; the patient-portal forms only need a
per-session token in a hidden field validated on POST.
"""

import hmac
import secrets
from functools import wraps
from flask import session, request, abort, current_app


_SESSION_KEY = "_csrf_token"


def generate_csrf_token() -> str:
    tok = session.get(_SESSION_KEY)
    if not tok:
        tok = secrets.token_urlsafe(32)
        session[_SESSION_KEY] = tok
    return tok


def validate_csrf_token(submitted: str | None) -> bool:
    expected = session.get(_SESSION_KEY, "")
    if not expected or not submitted:
        return False
    return hmac.compare_digest(expected, submitted)


def csrf_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            token = (
                request.form.get("csrf_token")
                or request.headers.get("X-CSRF-Token")
            )
            if not validate_csrf_token(token):
                current_app.logger.warning(
                    "CSRF validation failed for %s %s from %s",
                    request.method, request.path, request.remote_addr
                )
                abort(400, description="CSRF token missing or invalid")
        return f(*args, **kwargs)
    return wrapper
