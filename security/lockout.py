# MedPharm ERP - Copyright (C) 2026 Enlightec Ltd.
# Licensed under the GNU General Public License v3.0 or later.
"""
Account lockout tracker.

Tracks failed login attempts per account in a small in-process cache plus a
persistent `failed_logins` table. After N failures within the lockout window,
subsequent logins are refused until the lockout duration elapses. This maps
to § 164.308(a)(5)(ii)(C) "Log-in monitoring".
"""

import threading
import time
from dataclasses import dataclass, field


class AccountLockedError(RuntimeError):
    def __init__(self, retry_after_seconds: int):
        super().__init__(f"Account locked. Retry after {retry_after_seconds}s.")
        self.retry_after = retry_after_seconds


@dataclass
class _State:
    failures: list[float] = field(default_factory=list)
    locked_until: float = 0.0


class LockoutTracker:
    """
    Thread-safe in-process lockout bookkeeping. For multi-process deployments,
    back this with the database (see security/audit.py for an example).
    """

    def __init__(self, threshold: int = 5, window_seconds: int = 900,
                 lockout_seconds: int = 1800):
        self.threshold = threshold
        self.window = window_seconds
        self.duration = lockout_seconds
        self._lock = threading.Lock()
        self._state: dict[str, _State] = {}

    def _now(self) -> float:
        return time.time()

    def _prune(self, state: _State, now: float) -> None:
        cutoff = now - self.window
        state.failures = [t for t in state.failures if t >= cutoff]

    def assert_not_locked(self, key: str) -> None:
        now = self._now()
        with self._lock:
            state = self._state.get(key)
            if state and state.locked_until > now:
                raise AccountLockedError(int(state.locked_until - now))

    def record_failure(self, key: str) -> int:
        """Return remaining attempts before lockout (0 = now locked)."""
        now = self._now()
        with self._lock:
            state = self._state.setdefault(key, _State())
            self._prune(state, now)
            state.failures.append(now)
            remaining = self.threshold - len(state.failures)
            if remaining <= 0:
                state.locked_until = now + self.duration
                state.failures.clear()
                return 0
            return remaining

    def record_success(self, key: str) -> None:
        with self._lock:
            self._state.pop(key, None)

    def is_locked(self, key: str) -> bool:
        now = self._now()
        with self._lock:
            state = self._state.get(key)
            return bool(state and state.locked_until > now)

    def clear(self) -> None:
        with self._lock:
            self._state.clear()
