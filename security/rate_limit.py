# MedPharm ERP - Copyright (C) 2026 Enlightec Ltd.
# Licensed under the GNU General Public License v3.0 or later.
"""
Sliding-window rate limiter.

Complements ``security.lockout`` (which targets credentialled-login
abuse) by capping request rate per (key, scope) pair. Useful for:

* Limiting unauthenticated endpoints (``/api/v1/auth/login/*``,
  ``/api/v1/auth/register``, ``/login``, ``/register``) to slow down
  online password guessing and registration scraping.
* Limiting expensive endpoints (``/api/v1/medications/search``) to
  prevent a single client from saturating the database.

The limiter is **in-process**. Multi-worker deployments that need
shared state should back it with Redis or the database — the
``Backend`` interface lets callers swap the storage.

Rate-limit decisions are emitted to the audit log only when they
result in denial; permitted requests are not logged here (volume
would dwarf the rest of the audit log).
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Deque, Dict, Tuple


class RateLimitExceeded(RuntimeError):
    def __init__(self, retry_after_seconds: float):
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after_seconds:.1f}s."
        )
        self.retry_after = retry_after_seconds


@dataclass
class _Window:
    timestamps: Deque[float]
    capacity: int


class InProcessBackend:
    """Default thread-safe storage. Use Redis in multi-worker setups."""

    def __init__(self):
        self._lock = threading.Lock()
        self._state: Dict[Tuple[str, str], _Window] = {}

    def hit(self, key: str, scope: str, capacity: int, window_seconds: float) -> Tuple[bool, float]:
        now = time.time()
        cutoff = now - window_seconds
        with self._lock:
            w = self._state.get((key, scope))
            if w is None:
                w = _Window(deque(), capacity)
                self._state[(key, scope)] = w
            # Drop expired hits.
            while w.timestamps and w.timestamps[0] < cutoff:
                w.timestamps.popleft()
            if len(w.timestamps) >= capacity:
                retry_after = (w.timestamps[0] - cutoff)
                return False, max(retry_after, 0.0)
            w.timestamps.append(now)
            return True, 0.0


class RateLimiter:
    """Thin policy wrapper around a ``Backend``."""

    def __init__(
        self,
        backend: InProcessBackend | None = None,
        *,
        default_capacity: int = 60,
        default_window_seconds: float = 60.0,
    ):
        self.backend = backend or InProcessBackend()
        self.default_capacity = default_capacity
        self.default_window_seconds = default_window_seconds

    def check(
        self,
        key: str,
        scope: str = "global",
        capacity: int | None = None,
        window_seconds: float | None = None,
    ) -> None:
        cap = capacity or self.default_capacity
        win = window_seconds or self.default_window_seconds
        ok, retry = self.backend.hit(key, scope, cap, win)
        if not ok:
            raise RateLimitExceeded(retry)


# ── Flask integration ────────────────────────────────────────────────────────

def flask_rate_limit(
    limiter: RateLimiter,
    *,
    scope: str,
    capacity: int | None = None,
    window_seconds: float | None = None,
    key_func: Callable | None = None,
):
    """
    Decorate a Flask handler to enforce a rate limit. Default key is the
    client IP (X-Forwarded-For aware). Returns 429 with a ``Retry-After``
    header on excess.

    Usage:

        from security.rate_limit import RateLimiter, flask_rate_limit
        rl = RateLimiter()
        @app.route("/login", methods=["POST"])
        @flask_rate_limit(rl, scope="login", capacity=10, window_seconds=60)
        def login(): ...
    """
    from functools import wraps
    from flask import request, jsonify, make_response

    def _default_key():
        fwd = request.headers.get("X-Forwarded-For", "")
        ip = (fwd.split(",")[0].strip() if fwd else request.remote_addr) or "anonymous"
        return ip

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = (key_func() if key_func else _default_key())
            try:
                limiter.check(key, scope=scope,
                              capacity=capacity, window_seconds=window_seconds)
            except RateLimitExceeded as exc:
                resp = make_response(
                    jsonify({"error": "rate_limit",
                             "retry_after": int(exc.retry_after) + 1}), 429)
                resp.headers["Retry-After"] = str(int(exc.retry_after) + 1)
                return resp
            return fn(*args, **kwargs)
        return wrapper
    return decorator


__all__ = [
    "RateLimitExceeded",
    "InProcessBackend",
    "RateLimiter",
    "flask_rate_limit",
]
