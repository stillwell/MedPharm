# MedPharm ERP - Copyright (C) 2026 Enlightec Ltd.
# Licensed under the GNU General Public License v3.0 or later.
"""Security configuration loader. Validates HIPAA-relevant env vars at boot."""

import os
import secrets
from dataclasses import dataclass, field


DEFAULT_JWT_SECRET = "medpharm-dev-secret-change-in-production"


class SecurityConfigError(RuntimeError):
    pass


@dataclass
class SecurityConfig:
    jwt_secret: str
    flask_secret: str
    field_encryption_key: str
    token_expiry_seconds: int = 86400
    refresh_expiry_seconds: int = 604800
    idle_timeout_seconds: int = 900            # 15 min, per HIPAA auto-logoff guidance
    lockout_threshold: int = 5
    lockout_window_seconds: int = 900          # count failures in a 15-min window
    lockout_duration_seconds: int = 1800       # 30-min lockout after threshold
    password_min_length: int = 12
    password_history: int = 5
    password_max_age_days: int = 90
    require_mfa_for_staff: bool = False
    require_tls: bool = True
    hsts_max_age: int = 31536000
    cors_origins: str = ""
    environment: str = "development"
    allowed_hosts: list = field(default_factory=list)
    # Hard ceiling on a single session's lifetime, regardless of activity.
    # 0 means "8 × idle_timeout_seconds" — the historical default.
    absolute_session_lifetime_seconds: int = 0
    # Strict CSP drops 'unsafe-inline' for scripts; opt-in because it
    # requires every inline <script> in the templates to be moved out.
    strict_csp: bool = False
    # Default per-IP rate limit for unauthenticated endpoints.
    rate_limit_per_minute: int = 60

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in ("production", "prod")


def _env(name: str, default: str | None = None) -> str | None:
    val = os.environ.get(name, default)
    if val is None:
        return None
    return val.strip() or None


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def load_security_config() -> SecurityConfig:
    env = (_env("MEDPHARM_ENV") or _env("FLASK_ENV") or "development").lower()

    jwt_secret = _env("MEDPHARM_JWT_SECRET") or DEFAULT_JWT_SECRET
    flask_secret = _env("MEDPHARM_SECRET_KEY") or secrets.token_hex(32)
    field_key = _env("MEDPHARM_FIELD_KEY") or ""

    cfg = SecurityConfig(
        jwt_secret=jwt_secret,
        flask_secret=flask_secret,
        field_encryption_key=field_key,
        token_expiry_seconds=_env_int("MEDPHARM_TOKEN_EXPIRY", 86400),
        refresh_expiry_seconds=_env_int("MEDPHARM_REFRESH_EXPIRY", 604800),
        idle_timeout_seconds=_env_int("MEDPHARM_IDLE_TIMEOUT", 900),
        lockout_threshold=_env_int("MEDPHARM_LOCKOUT_THRESHOLD", 5),
        lockout_window_seconds=_env_int("MEDPHARM_LOCKOUT_WINDOW", 900),
        lockout_duration_seconds=_env_int("MEDPHARM_LOCKOUT_DURATION", 1800),
        password_min_length=_env_int("MEDPHARM_PWD_MIN_LEN", 12),
        password_history=_env_int("MEDPHARM_PWD_HISTORY", 5),
        password_max_age_days=_env_int("MEDPHARM_PWD_MAX_AGE_DAYS", 90),
        require_mfa_for_staff=_env_bool("MEDPHARM_REQUIRE_MFA", False),
        require_tls=_env_bool("MEDPHARM_REQUIRE_TLS", True),
        hsts_max_age=_env_int("MEDPHARM_HSTS_MAX_AGE", 31536000),
        cors_origins=_env("MEDPHARM_CORS_ORIGINS") or "",
        environment=env,
        allowed_hosts=(_env("MEDPHARM_ALLOWED_HOSTS") or "").split(","),
        absolute_session_lifetime_seconds=_env_int(
            "MEDPHARM_ABSOLUTE_SESSION_LIFETIME", 0),
        strict_csp=_env_bool("MEDPHARM_STRICT_CSP", False),
        rate_limit_per_minute=_env_int("MEDPHARM_RATE_LIMIT_PER_MIN", 60),
    )
    return cfg


def require_production_secrets(cfg: SecurityConfig) -> list[str]:
    """
    Return a list of validation errors when running in production mode without
    proper secrets configured. Callers decide whether to abort or warn.
    """
    errors: list[str] = []
    if cfg.jwt_secret == DEFAULT_JWT_SECRET:
        errors.append(
            "MEDPHARM_JWT_SECRET is using the built-in default. Set a "
            "cryptographically random 32+ byte secret before production."
        )
    if not cfg.field_encryption_key:
        errors.append(
            "MEDPHARM_FIELD_KEY is not set. Generate one with "
            "`python -m security.encryption generate-key` and store it "
            "in your secret manager."
        )
    if cfg.cors_origins.strip() == "*":
        errors.append(
            "MEDPHARM_CORS_ORIGINS=* is not safe for production. Pin to "
            "your patient-portal and client origins."
        )
    if not cfg.require_tls:
        errors.append(
            "MEDPHARM_REQUIRE_TLS is disabled. PHI transmission security "
            "requires TLS in production."
        )
    return errors
