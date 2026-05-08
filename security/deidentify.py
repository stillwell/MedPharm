# MedPharm ERP - Copyright (C) 2026 Enlightec Ltd.
# Licensed under the GNU General Public License v3.0 or later.
"""
HIPAA Safe Harbor de-identification helpers (45 CFR § 164.514(b)(2)).

Safe Harbor de-identifies a record by removing 18 specific identifiers
of the individual and of the individual's relatives, employers, and
household members, **and** the covered entity must have no actual
knowledge that the residual data could be used to re-identify the
individual.

This module provides ``safe_harbor(record)`` to scrub a dict-shaped
record per the 18 identifiers, and ``redact_text(text)`` to scrub
free-text fields with regex patterns for the most common
identifiers (SSN, phone, email, dates, ages > 89). For the rare
"expert determination" path (§ 164.514(b)(1)) the entity must engage
a qualified statistician — that is out of scope for this module.

Usage:

    from security.deidentify import safe_harbor, redact_text

    de_id = safe_harbor(patient_record)
    de_id_note = redact_text(clinical_note_body)

The returned record carries no PHI per Safe Harbor and may be
retained indefinitely under ``docs/DATA_RETENTION_POLICY.md`` §6.
The caller must still confirm "no actual knowledge of
re-identifiability" — typically a Privacy-Officer sign-off — before
publishing or sharing the dataset.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


# The 18 Safe Harbor identifiers, by index per § 164.514(b)(2)(i).
# We keep the list explicit so a code reviewer can map each rule to
# the regulation. Field names below are MedPharm's; map to your
# schema when adapting this helper.
_SAFE_HARBOR_FIELDS = (
    # (1) Names — patient + relatives + employers + household members.
    "first_name", "middle_name", "last_name", "preferred_name", "full_name",
    "spouse_name", "guardian_name", "emergency_contact_name", "next_of_kin",
    "employer_name",
    # (2) Geographic subdivisions smaller than a state — street, city, county,
    # zip (zip is partial-allowed: see _truncate_zip below).
    "address_line_1", "address_line_2", "street", "city", "county",
    # (3) All elements of dates (except year) directly related to the individual,
    # including birth date, admission/discharge dates, date of death, and all
    # ages over 89 (see _coarsen_age below).
    "dob", "date_of_birth", "admission_date", "discharge_date",
    "death_date", "appointment_datetime", "scheduled_datetime",
    "encounter_date", "specimen_collection_date", "result_date",
    # (4) Telephone numbers.
    "phone", "phone_home", "phone_work", "phone_mobile", "fax",
    # (5) Email addresses.
    "email", "email_personal", "email_work",
    # (6) Social Security numbers (full or partial).
    "ssn", "ssn_full", "ssn_last4",
    # (7) Medical record numbers.
    "mrn", "medical_record_number",
    # (8) Health plan beneficiary numbers.
    "insurance_member_id", "subscriber_id",
    # (9) Account numbers.
    "account_number", "patient_account_number", "invoice_account",
    # (10) Certificate / licence numbers.
    "license_number", "dl_number", "passport_number",
    # (11) Vehicle identifiers and serial numbers including licence plates.
    "vehicle_id", "license_plate",
    # (12) Device identifiers and serial numbers.
    "device_serial", "device_udi",
    # (13) Web URLs (only those that identify the individual; we strip
    # all to be safe).
    "url", "personal_url", "social_handle",
    # (14) IP addresses.
    "ip", "ip_address",
    # (15) Biometric identifiers (fingerprints, voice prints, etc.).
    "biometric_fingerprint", "biometric_voice", "biometric_iris",
    # (16) Full-face photographs and any comparable images.
    "photo", "photo_url", "face_image",
    # (17) Any other unique identifying number, characteristic, or code
    # (caller is responsible for adding theirs to this list before
    # invoking).
    "external_record_id",
    # (18) Geographic information not covered by (2): the geocodes paired
    # with the address.
    "lat", "lng", "geocode",
)


_RE_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b")
_RE_PHONE = re.compile(
    r"\b(?:\+?\d{1,3}[\s.-]?)?(?:\(\d{3}\)\s?|\d{3}[\s.-])\d{3}[\s.-]\d{4}\b"
)
_RE_EMAIL = re.compile(r"\b[\w.+%-]+@[\w.-]+\.[A-Za-z]{2,}\b")
# A date pattern broad enough to catch yyyy-mm-dd, mm/dd/yyyy, dd-mmm-yyyy.
_RE_DATE = re.compile(
    r"\b("
    r"\d{4}-\d{2}-\d{2}"          # 2026-05-07
    r"|\d{1,2}/\d{1,2}/\d{2,4}"   # 5/7/2026 or 05/07/26
    r"|\d{1,2}\s[A-Za-z]{3,9}\s\d{2,4}"  # 7 May 2026
    r"|[A-Za-z]{3,9}\s\d{1,2},?\s\d{2,4}" # May 7, 2026
    r")\b"
)
_RE_URL = re.compile(r"https?://\S+", re.IGNORECASE)
_RE_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_RE_MRN = re.compile(r"\bMRN[:\s-]?\d+\b", re.IGNORECASE)
# Ages: a literal integer >= 90, written as a year-old phrase.
_RE_AGE_OVER_89 = re.compile(
    r"\b(?:9[0-9]|1[0-9]{2})[\s-]?(?:year[s]?[-\s]old|y[/.]?o\.?)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SafeHarborOptions:
    """Knobs for the Safe Harbor scrub."""
    # Keep the year of date fields (Safe Harbor permits the year alone for
    # subjects ≤ 89; for subjects > 89 even the year is stripped).
    keep_year_of_dates: bool = True
    # Truncate zip codes to 3 digits when the population covered by the
    # 3-digit prefix is > 20,000 (Safe Harbor § 164.514(b)(2)(i)(B)).
    # The list of restricted prefixes below is the HHS-published set.
    truncate_zip: bool = True
    # Replace removed values with this sentinel; None means delete the key.
    sentinel: Any = None
    # Extra field names to scrub (the entity-specific (17) catch-all).
    extra_fields: tuple = ()
    # Subject's age — when > 89, dates are fully stripped (year too) per
    # Safe Harbor § 164.514(b)(2)(i)(C).
    subject_age: int | None = None


# HHS-published 3-digit ZIP prefixes whose covered population is < 20 000.
# Safe Harbor requires changing these prefixes to ``000``.
_RESTRICTED_ZIP3 = frozenset({
    "036", "059", "063", "102", "203", "556", "692", "790", "821", "823",
    "830", "831", "878", "879", "884", "890", "893",
})


def _truncate_zip(zip_code: str | int | None) -> str | None:
    if zip_code is None:
        return None
    z = str(zip_code).strip().replace("-", "")[:5]
    if len(z) < 3 or not z[:3].isdigit():
        return None
    prefix = z[:3]
    if prefix in _RESTRICTED_ZIP3:
        return "000"
    return prefix


def _coarsen_date(value, *, keep_year: bool) -> Any:
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.year if keep_year else None
    if isinstance(value, str):
        # Try to parse and re-emit as year only.
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                    "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%d %B %Y"):
            try:
                d = datetime.strptime(value[:len(fmt)], fmt)
                return d.year if keep_year else None
            except ValueError:
                continue
    return None


def safe_harbor(record: dict, options: SafeHarborOptions | None = None) -> dict:
    """
    Return a copy of ``record`` with the 18 Safe Harbor identifiers removed
    or coarsened. The original record is **not** modified.
    """
    opts = options or SafeHarborOptions()
    if opts.subject_age is not None and opts.subject_age > 89:
        keep_year = False
    else:
        keep_year = opts.keep_year_of_dates

    fields = set(_SAFE_HARBOR_FIELDS) | set(opts.extra_fields)
    out = dict(record)
    for k in list(out.keys()):
        v = out[k]
        if k in {"dob", "date_of_birth", "admission_date", "discharge_date",
                 "death_date", "appointment_datetime", "scheduled_datetime",
                 "encounter_date", "specimen_collection_date", "result_date"}:
            coarsened = _coarsen_date(v, keep_year=keep_year)
            if coarsened is None:
                if opts.sentinel is None:
                    del out[k]
                else:
                    out[k] = opts.sentinel
            else:
                out[k.replace("dob", "birth_year").replace("date_of_birth", "birth_year")
                    if k in {"dob", "date_of_birth"} else k + "_year"] = coarsened
                if k in out and k not in {"dob", "date_of_birth"}:
                    del out[k]
                else:
                    out.pop(k, None)
        elif k in {"zip_code", "zip", "postal_code"}:
            if opts.truncate_zip:
                truncated = _truncate_zip(v)
                if truncated is None:
                    if opts.sentinel is None:
                        del out[k]
                    else:
                        out[k] = opts.sentinel
                else:
                    out[k] = truncated
            else:
                if opts.sentinel is None:
                    del out[k]
                else:
                    out[k] = opts.sentinel
        elif k in fields:
            if opts.sentinel is None:
                del out[k]
            else:
                out[k] = opts.sentinel
        elif k == "age" and isinstance(v, int) and v > 89:
            out[k] = 90  # "90 or older" lower bound per Safe Harbor.
    return out


def redact_text(text: str | None, *, replacement: str = "[redacted]") -> str | None:
    """
    Scrub free-text fields with regex patterns for the most common
    Safe Harbor identifiers. Use this on clinical notes before
    de-identification publication. **Does not** catch every
    identifier — the caller must still ensure the residual text has
    no other PHI (named individuals, rare diagnoses, etc.).
    """
    if text is None:
        return None
    out = text
    out = _RE_SSN.sub(replacement, out)
    out = _RE_PHONE.sub(replacement, out)
    out = _RE_EMAIL.sub(replacement, out)
    out = _RE_URL.sub(replacement, out)
    out = _RE_IPV4.sub(replacement, out)
    out = _RE_MRN.sub(replacement, out)
    out = _RE_AGE_OVER_89.sub("90+ years old", out)
    out = _RE_DATE.sub(replacement, out)
    return out


__all__ = [
    "SafeHarborOptions",
    "safe_harbor",
    "redact_text",
]
