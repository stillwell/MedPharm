# MedPharm ERP - Copyright (C) 2026 Enlightec Ltd.
# Licensed under the GNU General Public License v3.0 or later.
"""Smoke tests for the security package."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class PasswordPolicyTests(unittest.TestCase):
    def test_rejects_short(self):
        from security.passwords import validate_password, PasswordPolicy, PasswordPolicyError
        with self.assertRaises(PasswordPolicyError):
            validate_password("Aa1!aa", PasswordPolicy(min_length=12))

    def test_rejects_no_digit(self):
        from security.passwords import validate_password, PasswordPolicy, PasswordPolicyError
        with self.assertRaises(PasswordPolicyError):
            validate_password("Abcdefghijkl!", PasswordPolicy())

    def test_rejects_common(self):
        from security.passwords import validate_password, PasswordPolicy, PasswordPolicyError
        # min_length=6 so the common-password check runs before length/complexity
        with self.assertRaises(PasswordPolicyError):
            validate_password("password", PasswordPolicy(
                min_length=6, require_uppercase=False, require_lowercase=False,
                require_digit=False, require_symbol=False
            ))

    def test_rejects_username_inside(self):
        from security.passwords import validate_password, PasswordPolicy, PasswordPolicyError
        with self.assertRaises(PasswordPolicyError):
            validate_password("Aa1!jsmith-rocks", PasswordPolicy(), username="jsmith")

    def test_accepts_strong(self):
        from security.passwords import validate_password, PasswordPolicy
        # Should not raise
        validate_password("TurtleBridge7$long", PasswordPolicy())


class LockoutTests(unittest.TestCase):
    def test_locks_after_threshold(self):
        from security.lockout import LockoutTracker, AccountLockedError
        tracker = LockoutTracker(threshold=3, window_seconds=60, lockout_seconds=60)
        tracker.record_failure("u1")
        tracker.record_failure("u1")
        remaining = tracker.record_failure("u1")
        self.assertEqual(remaining, 0)
        with self.assertRaises(AccountLockedError):
            tracker.assert_not_locked("u1")

    def test_record_success_clears(self):
        from security.lockout import LockoutTracker
        tracker = LockoutTracker(threshold=3)
        tracker.record_failure("u1")
        tracker.record_success("u1")
        self.assertFalse(tracker.is_locked("u1"))


class TOTPTests(unittest.TestCase):
    def test_verify_roundtrip(self):
        from security.totp import generate_totp_secret, current_totp, verify_totp_code
        secret = generate_totp_secret()
        code = current_totp(secret)
        self.assertTrue(verify_totp_code(secret, code))

    def test_reject_bogus_code(self):
        from security.totp import generate_totp_secret, verify_totp_code
        secret = generate_totp_secret()
        self.assertFalse(verify_totp_code(secret, "000000"))


class EncryptionTests(unittest.TestCase):
    def test_encrypt_decrypt(self):
        from security.encryption import FieldCipher, generate_key
        cipher = FieldCipher(key=generate_key())
        ct = cipher.encrypt("hello PHI")
        self.assertNotEqual(ct, "hello PHI")
        self.assertEqual(cipher.decrypt(ct), "hello PHI")

    def test_passthrough_unencrypted(self):
        from security.encryption import FieldCipher, generate_key
        cipher = FieldCipher(key=generate_key())
        # Non-encrypted input should pass through
        self.assertEqual(cipher.decrypt("plain text"), "plain text")


class AuditChainHashTests(unittest.TestCase):
    def test_hash_is_stable(self):
        from security.audit import compute_row_hash
        payload = {"a": 1, "b": "two"}
        h1 = compute_row_hash("prev", payload)
        h2 = compute_row_hash("prev", payload)
        self.assertEqual(h1, h2)

    def test_hash_changes_with_prev(self):
        from security.audit import compute_row_hash
        payload = {"a": 1}
        self.assertNotEqual(
            compute_row_hash("prev1", payload),
            compute_row_hash("prev2", payload),
        )


class CSRFTests(unittest.TestCase):
    def test_validate_csrf(self):
        from flask import Flask
        from security.csrf import generate_csrf_token, validate_csrf_token
        app = Flask(__name__)
        app.secret_key = "test"
        with app.test_request_context():
            tok = generate_csrf_token()
            self.assertTrue(validate_csrf_token(tok))
            self.assertFalse(validate_csrf_token("wrong"))


if __name__ == "__main__":
    unittest.main()
