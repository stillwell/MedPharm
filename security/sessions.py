# MedPharm ERP - Copyright (C) 2026 Enlightec Ltd.
# Licensed under the GNU General Public License v3.0 or later.
"""Session hardening and security headers for Flask apps."""

import time
from datetime import timedelta
from flask import Flask, session, g, redirect, url_for, flash, request


def apply_session_hardening(app: Flask, cfg) -> None:
    """
    Set HIPAA-appropriate session cookie flags and timeout.

    - Secure:  cookies only go over TLS (disable for local-dev over HTTP)
    - HttpOnly: JavaScript cannot read the session cookie
    - SameSite=Lax: reduces CSRF attack surface while keeping normal nav
    - PERMANENT_SESSION_LIFETIME: hard ceiling on session lifetime
    """
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=cfg.require_tls,
        PERMANENT_SESSION_LIFETIME=timedelta(seconds=cfg.idle_timeout_seconds * 8),
        SESSION_REFRESH_EACH_REQUEST=True,
    )
    app.permanent_session_lifetime = timedelta(seconds=cfg.idle_timeout_seconds * 8)

    @app.after_request
    def _set_headers(resp):
        for k, v in security_headers(cfg).items():
            resp.headers.setdefault(k, v)
        return resp


def security_headers(cfg) -> dict[str, str]:
    """
    Return a headers dict tailored to a PHI-handling app.
    Callers splat into response.headers or an Nginx config.
    """
    headers = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-origin",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        ),
    }
    if cfg.require_tls:
        headers["Strict-Transport-Security"] = (
            f"max-age={cfg.hsts_max_age}; includeSubDomains; preload"
        )
    return headers


def enforce_idle_timeout(cfg, *, redirect_endpoint: str = "portal.login"):
    """
    before_request handler factory — logs the user out after N seconds of
    inactivity. Attach via `app.before_request(enforce_idle_timeout(cfg))`.
    """
    idle = cfg.idle_timeout_seconds

    def _handler():
        if "user_id" not in session and "patient_id" not in session:
            return None
        now = int(time.time())
        last = session.get("_last_seen", now)
        if now - last > idle:
            session.clear()
            flash("Your session has timed out. Please log in again.", "warning")
            if request.endpoint == redirect_endpoint:
                return None
            return redirect(url_for(redirect_endpoint))
        session["_last_seen"] = now
        session.permanent = True
        return None

    return _handler
