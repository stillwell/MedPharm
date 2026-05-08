# MedPharm ERP - Copyright (C) 2026 Enlightec Ltd.
# Licensed under the GNU General Public License v3.0 or later.
"""
Logging filter that scrubs likely-PHI patterns from log records.

The HIPAA audit log is the *intentional* record of access; the
application log is supposed to be operational telemetry, not a PHI
sink. Secondary log destinations (stdout, journald, a SIEM) routinely
violate this — a developer prints a request body to debug, a stack
trace includes a SQL parameter, a message body lands in a metrics
aggregator. This filter is the last line of defence: it rewrites
log records to redact common PHI patterns before they leave the
process.

Install once, at application start:

    import logging
    from security.log_redaction import install_phi_redaction_filter
    install_phi_redaction_filter(logging.getLogger())

Patterns covered: SSN, US phone number, email address, IPv4 address,
URL, common date forms, MRN-prefixed numbers, ages > 89.

This is a **defence-in-depth** control. The primary control is to
not log PHI in the first place; this filter exists to catch the
ones we miss. See ``docs/MINIMUM_NECESSARY.md`` and
``docs/WORKFORCE_TRAINING.md`` §3.2.
"""

from __future__ import annotations

import logging
import re
from typing import Iterable

from security.deidentify import (
    _RE_SSN,
    _RE_PHONE,
    _RE_EMAIL,
    _RE_URL,
    _RE_IPV4,
    _RE_MRN,
    _RE_AGE_OVER_89,
    _RE_DATE,
)


# Order matters: longer / more specific patterns first so a phone
# inside a URL is caught as a URL, not split between matches.
_PATTERNS = (
    _RE_URL,
    _RE_EMAIL,
    _RE_SSN,
    _RE_PHONE,
    _RE_IPV4,
    _RE_MRN,
    _RE_AGE_OVER_89,
    _RE_DATE,
)


# Optional: a regex for JWT-shaped tokens. JWTs aren't PHI per se,
# but bearer tokens leaked into logs are an authentication-control
# breach (§ 164.312(d)) and warrant the same redaction.
_RE_JWT = re.compile(r"\beyJ[A-Za-z0-9_\-]+?\.[A-Za-z0-9_\-]+?\.[A-Za-z0-9_\-]+\b")


_REPLACEMENT = "[redacted]"


def _scrub(value: str) -> str:
    """Apply every pattern. Cheap because regexes precompile once."""
    out = value
    for pat in _PATTERNS:
        out = pat.sub(_REPLACEMENT, out)
    out = _RE_JWT.sub(_REPLACEMENT, out)
    return out


class PHIRedactionFilter(logging.Filter):
    """
    Drop-in logging.Filter that rewrites the log record's message
    and string-typed args. Non-string args are passed through
    untouched (logging applies %-formatting later, after our scrub).
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = _scrub(record.msg)
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {
                        k: (_scrub(v) if isinstance(v, str) else v)
                        for k, v in record.args.items()
                    }
                elif isinstance(record.args, tuple):
                    record.args = tuple(
                        _scrub(a) if isinstance(a, str) else a
                        for a in record.args
                    )
            # If the record has been formatted already, scrub the result too.
            if hasattr(record, "message") and isinstance(record.message, str):
                record.message = _scrub(record.message)
        except Exception:
            # A log filter that raises can take the process down; swallow.
            pass
        return True


def install_phi_redaction_filter(
    logger: logging.Logger | None = None,
    *,
    also_handlers: Iterable[logging.Handler] | None = None,
) -> PHIRedactionFilter:
    """
    Attach the filter to the supplied logger (root if None) and
    optionally to a sequence of handlers (so filters don't get
    bypassed by handlers that don't propagate to the logger).
    Returns the filter instance for callers that want to remove it
    later.
    """
    flt = PHIRedactionFilter()
    target = logger if logger is not None else logging.getLogger()
    target.addFilter(flt)
    for h in (also_handlers or ()):
        h.addFilter(flt)
    return flt


__all__ = [
    "PHIRedactionFilter",
    "install_phi_redaction_filter",
]
