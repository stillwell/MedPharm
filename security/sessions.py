# MedPharm ERP - Copyright (C) 2026 Enlightec Ltd.
# Licensed under the GNU General Public License v3.0 or later.
"""Session hardening and security headers for Flask apps."""

import time
from datetime import timedelta
from flask import Flask, session, g, redirect, url_for, flash, request


def _absolute_lifetime(cfg) -> int:
    """
    Resolve the absolute session-lifetime cap. 0 means
    "8 × idle_timeout_seconds" — historical default — for backwards
    compatibility with existing deployments.
    """
    if getattr(cfg, "absolute_session_lifetime_seconds", 0) > 0:
        return cfg.absolute_session_lifetime_seconds
    return cfg.idle_timeout_seconds * 8


def apply_session_hardening(app: Flask, cfg) -> None:
    """
    Set HIPAA-appropriate session cookie flags and timeout.

    - Secure:  cookies only go over TLS (disable for local-dev over HTTP)
    - HttpOnly: JavaScript cannot read the session cookie
    - SameSite=Lax: reduces CSRF attack surface while keeping normal nav
    - PERMANENT_SESSION_LIFETIME: hard ceiling on session lifetime
      (configurable via MEDPHARM_ABSOLUTE_SESSION_LIFETIME)
    """
    absolute = _absolute_lifetime(cfg)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=cfg.require_tls,
        PERMANENT_SESSION_LIFETIME=timedelta(seconds=absolute),
        SESSION_REFRESH_EACH_REQUEST=True,
    )
    app.permanent_session_lifetime = timedelta(seconds=absolute)

    @app.after_request
    def _set_headers(resp):
        for k, v in security_headers(cfg).items():
            resp.headers.setdefault(k, v)
        return resp


def security_headers(cfg) -> dict[str, str]:
    """
    Return a headers dict tailored to a PHI-handling app.
    Callers splat into response.headers or an Nginx config.

    The CSP is permissive by default (allows inline <script> and inline
    style="…") because the bundled templates rely on both. Set
    MEDPHARM_STRICT_CSP=1 once every inline <script> has been moved
    out of the templates — this gives a much stronger XSS posture.
    """
    if getattr(cfg, "strict_csp", False):
        csp = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
    else:
        csp = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
    headers = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-origin",
        "Content-Security-Policy": csp,
    }
    if cfg.require_tls:
        headers["Strict-Transport-Security"] = (
            f"max-age={cfg.hsts_max_age}; includeSubDomains; preload"
        )
    return headers


def enforce_idle_timeout(cfg, *, redirect_endpoint: str = "portal.login"):
    """
    before_request handler factory — logs the user out after N seconds of
    inactivity, OR after the absolute session lifetime cap, whichever
    comes first. Attach via `app.before_request(enforce_idle_timeout(cfg))`.

    The idle timeout maps to § 164.312(a)(2)(iii) (Automatic Logoff,
    addressable). The absolute cap is a defence-in-depth control for
    workforce sessions left open at end of shift.
    """
    idle = cfg.idle_timeout_seconds
    absolute = _absolute_lifetime(cfg)

    def _handler():
        if "user_id" not in session and "patient_id" not in session:
            return None
        now = int(time.time())
        last = session.get("_last_seen", now)
        started = session.get("_signed_in_at", now)
        idle_expired = (now - last) > idle
        absolute_expired = (now - started) > absolute
        if idle_expired or absolute_expired:
            reason = "absolute_lifetime_reached" if absolute_expired else "idle_timeout"
            session.clear()
            flash("Your session has timed out. Please log in again.", "warning")
            if request.endpoint == redirect_endpoint:
                return None
            resp = redirect(url_for(redirect_endpoint))
            try:
                resp.headers["X-Session-Expired"] = reason
            except Exception:
                pass
            return resp
        session["_last_seen"] = now
        session.setdefault("_signed_in_at", now)
        session.permanent = True
        return None

    return _handler
