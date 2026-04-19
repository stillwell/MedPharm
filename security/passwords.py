# MedPharm ERP - Copyright (C) 2026 Enlightec Ltd.
# Licensed under the GNU General Public License v3.0 or later.
"""Password policy enforcement: complexity, history, and rotation."""

import re
from dataclasses import dataclass
from werkzeug.security import check_password_hash, generate_password_hash


class PasswordPolicyError(ValueError):
    pass


@dataclass
class PasswordPolicy:
    min_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_symbol: bool = True
    max_repeated: int = 3        # reject "aaaa..."
    history_size: int = 5        # reuse protection
    max_age_days: int = 90       # must rotate after N days


_COMMON_PASSWORDS = frozenset({
    "password", "password1", "password123", "123456", "123456789", "qwerty",
    "letmein", "welcome", "monkey", "dragon", "master", "admin", "admin123",
    "iloveyou", "football", "patient123", "doctor123", "medpharm", "sunshine",
})


def validate_password(password: str, policy: PasswordPolicy,
                      username: str = "",
                      history_hashes: list[str] | None = None) -> None:
    """Raise PasswordPolicyError on any violation."""
    if not isinstance(password, str):
        raise PasswordPolicyError("Password must be a string.")
    if len(password) < policy.min_length:
        raise PasswordPolicyError(
            f"Password must be at least {policy.min_length} characters."
        )
    if policy.require_uppercase and not re.search(r"[A-Z]", password):
        raise PasswordPolicyError("Password must contain an uppercase letter.")
    if policy.require_lowercase and not re.search(r"[a-z]", password):
        raise PasswordPolicyError("Password must contain a lowercase letter.")
    if policy.require_digit and not re.search(r"\d", password):
        raise PasswordPolicyError("Password must contain a digit.")
    if policy.require_symbol and not re.search(r"[^A-Za-z0-9]", password):
        raise PasswordPolicyError("Password must contain a symbol.")

    # repetition check: no 4+ identical consecutive characters
    if re.search(r"(.)\1{%d,}" % policy.max_repeated, password):
        raise PasswordPolicyError(
            f"Password cannot contain more than {policy.max_repeated} "
            "identical consecutive characters."
        )

    if password.lower() in _COMMON_PASSWORDS:
        raise PasswordPolicyError("Password is too common.")

    if username and username.lower() in password.lower():
        raise PasswordPolicyError("Password cannot contain your username.")

    for old in (history_hashes or [])[:policy.history_size]:
        if old and check_password_hash(old, password):
            raise PasswordPolicyError(
                "Password was used recently — choose a new one."
            )


def hash_password(password: str) -> str:
    # pbkdf2 rounds bumped beyond werkzeug default for HIPAA posture.
    return generate_password_hash(password, method="pbkdf2:sha256:600000")
