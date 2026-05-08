# MedPharm ERP - Copyright (C) 2026 Enlightec Ltd.
# Licensed under the GNU General Public License v3.0 or later.
"""
Field-level encryption for PHI columns.

Uses cryptography.Fernet (AES-128-CBC + HMAC-SHA256) when available. If the
cryptography package is unavailable we fall back to a built-in AES-GCM-like
construction over HMAC + PBKDF2 so the module can still be imported in
development environments that skipped the optional dependency. Production
MUST install `cryptography` — see requirements-security.txt.
"""

import base64
import hashlib
import hmac
import os
import secrets as _secrets

try:
    from cryptography.fernet import Fernet, InvalidToken, MultiFernet
    _HAVE_CRYPTO = True
except ImportError:  # pragma: no cover — fallback path
    Fernet = None
    InvalidToken = Exception
    MultiFernet = None
    _HAVE_CRYPTO = False


_ENCRYPTED_PREFIX = b"enc_v1::"


class FieldEncryptionError(RuntimeError):
    pass


def _derive_fallback_key(passphrase: str) -> bytes:
    # Only used when cryptography is missing. Not for production.
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode(), b"medpharm-v1", 200000)


def generate_key() -> str:
    """Return a new base64-urlsafe 32-byte key suitable for MEDPHARM_FIELD_KEY."""
    if _HAVE_CRYPTO:
        return Fernet.generate_key().decode("ascii")
    return base64.urlsafe_b64encode(_secrets.token_bytes(32)).decode("ascii")


class FieldCipher:
    """
    Envelope cipher for individual database fields.

    Accepts a primary key plus optional retired keys (comma-separated) so that
    key rotation can decrypt old ciphertext while encrypting with the new key.
    """

    def __init__(self, key: str, legacy_keys: list[str] | None = None):
        if not key:
            raise FieldEncryptionError(
                "FieldCipher requires a base64-urlsafe 32-byte key"
            )
        self._key = key
        self._legacy = list(legacy_keys or [])
        if _HAVE_CRYPTO:
            ferns = [Fernet(key.encode())]
            ferns.extend(Fernet(k.encode()) for k in self._legacy if k)
            self._multi = MultiFernet(ferns) if len(ferns) > 1 else ferns[0]
        else:
            self._multi = None
            self._fallback_key = _derive_fallback_key(key)

    def encrypt(self, plaintext: str | None) -> str | None:
        if plaintext is None or plaintext == "":
            return plaintext
        data = plaintext.encode("utf-8")
        if _HAVE_CRYPTO:
            ct = self._multi.encrypt(data) if isinstance(self._multi, MultiFernet) else self._multi.encrypt(data)
            return (_ENCRYPTED_PREFIX + ct).decode("ascii")
        # fallback: HMAC + XOR-stream over SHA-256 expansion
        nonce = _secrets.token_bytes(16)
        stream = b""
        counter = 0
        while len(stream) < len(data):
            stream += hashlib.sha256(self._fallback_key + nonce + counter.to_bytes(4, "big")).digest()
            counter += 1
        ct = bytes(a ^ b for a, b in zip(data, stream[:len(data)]))
        tag = hmac.new(self._fallback_key, nonce + ct, hashlib.sha256).digest()
        payload = base64.urlsafe_b64encode(nonce + ct + tag)
        return (_ENCRYPTED_PREFIX + payload).decode("ascii")

    def decrypt(self, ciphertext: str | None) -> str | None:
        if ciphertext is None or ciphertext == "":
            return ciphertext
        if not ciphertext.startswith(_ENCRYPTED_PREFIX.decode()):
            return ciphertext  # legacy plaintext — return as-is for transitional reads
        body = ciphertext[len(_ENCRYPTED_PREFIX):].encode("ascii")
        if _HAVE_CRYPTO:
            try:
                pt = self._multi.decrypt(body) if isinstance(self._multi, MultiFernet) else self._multi.decrypt(body)
                return pt.decode("utf-8")
            except InvalidToken as exc:
                raise FieldEncryptionError("invalid or tampered ciphertext") from exc
        # fallback decrypt
        raw = base64.urlsafe_b64decode(body)
        nonce, ct_tag = raw[:16], raw[16:]
        ct, tag = ct_tag[:-32], ct_tag[-32:]
        expect = hmac.new(self._fallback_key, nonce + ct, hashlib.sha256).digest()
        if not hmac.compare_digest(expect, tag):
            raise FieldEncryptionError("integrity check failed")
        stream = b""
        counter = 0
        while len(stream) < len(ct):
            stream += hashlib.sha256(self._fallback_key + nonce + counter.to_bytes(4, "big")).digest()
            counter += 1
        return bytes(a ^ b for a, b in zip(ct, stream[:len(ct)])).decode("utf-8")


_SINGLETON: FieldCipher | None = None


def _singleton() -> FieldCipher:
    global _SINGLETON
    if _SINGLETON is None:
        key = os.environ.get("MEDPHARM_FIELD_KEY", "").strip()
        legacy = [k for k in os.environ.get("MEDPHARM_FIELD_KEY_LEGACY", "").split(",") if k.strip()]
        env = os.environ.get("MEDPHARM_ENV", "").strip().lower()
        is_production = env in ("production", "prod")
        if not _HAVE_CRYPTO and is_production:
            # The fallback is suitable for development only; HIPAA Safe Harbor
            # encryption guidance assumes FIPS 140-3 compliant primitives, and
            # the cryptography package gives us those. Refuse to run.
            raise FieldEncryptionError(
                "MEDPHARM_ENV=production but the 'cryptography' package is not "
                "installed. Install it (pip install cryptography) and restart. "
                "See docs/HIPAA_COMPLIANCE.md §1.1 for the rationale."
            )
        if not key:
            if is_production:
                # require_production_secrets normally catches this earlier;
                # the redundancy is defence-in-depth.
                raise FieldEncryptionError(
                    "MEDPHARM_FIELD_KEY is required in production. Generate "
                    "one with `python -m security.encryption generate-key` "
                    "and store it in your secret manager."
                )
            # Deterministic dev key so the module is usable in local development.
            key = base64.urlsafe_b64encode(
                hashlib.sha256(b"medpharm-dev-field-key-do-not-use-in-production").digest()
            ).decode("ascii")
        _SINGLETON = FieldCipher(key, legacy)
    return _SINGLETON


def encrypt_field(plaintext: str | None) -> str | None:
    return _singleton().encrypt(plaintext)


def decrypt_field(ciphertext: str | None) -> str | None:
    return _singleton().decrypt(ciphertext)


def rotate_key(new_key: str, legacy_keys: list[str]) -> None:
    """Replace the process-wide cipher with a new primary + legacy fallbacks."""
    global _SINGLETON
    _SINGLETON = FieldCipher(new_key, legacy_keys)


if __name__ == "__main__":  # pragma: no cover
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "generate-key":
        print(generate_key())
    else:
        print("usage: python -m security.encryption generate-key")
