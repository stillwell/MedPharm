#!/usr/bin/env python3
# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
# Email: Andrew.Stillwell@enlightec.com
# License: GNU General Public License v3.0
#
# ─────────────────────────────────────────────────────────────────────────────
# Enrich the MedPharm `medications` table with prescribing information
# (indications, contraindications, side effects, drug interactions, warnings,
# dosage) from the NIH/NLM DailyMed Structured Product Labeling (SPL) corpus.
#
# Why this script exists separately from load_fda_data.py:
#   The FDA NDC Directory has names, codes, and forms — but not the clinical
#   knowledge fields (indications/side-effects/interactions). DailyMed has
#   those, but encoded in HL7 V3 SPL XML files — one file per drug label,
#   with section content tagged by LOINC codes. This script parses those
#   XML files (or fetches them on demand from NLM) and folds the extracted
#   plain-text into the existing Medication rows.
#
# Two operating modes:
#
#   fetch — given a list of NDCs (or a --top=N query against the local table),
#           call the DailyMed REST API to discover the SPL setid for each NDC
#           and pull the XML, rate-limited to be polite to NLM. Caches each
#           SPL to disk so re-runs are free.
#
#   parse — given a directory of SPL XML files (typically extracted from
#           one of the FDA bulk-release ZIPs), parse each and upsert.
#           No network use; suitable for air-gapped operators.
#
# Resumability: an `dailymed_ingest_log` table tracks SHA-256 + last-modified
# per setid so a crashed run picks up where it left off.
#
# Scale: a full DailyMed download is ~50 GB across hundreds of monthly ZIPs.
# That is intentionally NOT downloaded by this script — the operator picks
# what they want to ingest:
#   - For a focused load (50–500 most-prescribed drugs):  fetch --top=500
#   - For everything ever approved:                       parse on the
#                                                         downloaded bulk
#
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import argparse
import hashlib
import io
import os
import re
import sys
import time
import urllib.request
import urllib.error
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Optional

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from database.db_manager import DatabaseManager
from database.models import Medication

try:
    from lxml import etree
except ImportError:
    print("ERROR: lxml is required. Install with:  pip install lxml")
    sys.exit(2)


SPL_NAMESPACE = "urn:hl7-org:v3"
NS = {"hl7": SPL_NAMESPACE}

# DailyMed REST API endpoints (no auth required for read).
DM_SEARCH_BY_NDC = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json"
DM_SPL_XML = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/{setid}.xml"
DM_RATE_LIMIT_SECONDS = 1.0   # polite default; NLM doesn't publish a hard limit

# LOINC codes for the SPL sections we care about.
# Source: DailyMed SPL Implementation Guide.
LOINC_SECTIONS = {
    "34067-9": "indications",        # INDICATIONS & USAGE
    "34070-3": "contraindications",  # CONTRAINDICATIONS
    "34073-7": "drug_interactions",  # DRUG INTERACTIONS
    "34084-4": "adverse_reactions",  # ADVERSE REACTIONS
    "34068-7": "dosage",             # DOSAGE & ADMINISTRATION
    "34071-1": "warnings",           # WARNINGS
    "50742-6": "boxed_warning",      # BOXED WARNING — highest severity
    "43685-7": "warnings_precautions",
    "42229-5": "precautions",
}

CACHE_DIR_DEFAULT = _ROOT / "data" / "dailymed-cache"


# ── Ingest log table ──────────────────────────────────────────────────────────
# Created lazily so we don't add a SQLAlchemy model to models.py for what is
# really a side-table for the loader's resume bookkeeping. Plain SQL.

_INGEST_LOG_DDL = """
CREATE TABLE IF NOT EXISTS dailymed_ingest_log (
    setid       TEXT PRIMARY KEY,
    ndc_code    TEXT,
    sha256      TEXT NOT NULL,
    parsed_at   TEXT NOT NULL,
    sections    INTEGER NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'ok'
)
"""


def _ensure_log_table(db: DatabaseManager) -> None:
    from sqlalchemy import text
    with db.engine.begin() as conn:
        conn.execute(text(_INGEST_LOG_DDL))


def _already_ingested(db: DatabaseManager, setid: str, sha: str) -> bool:
    from sqlalchemy import text
    with db.engine.begin() as conn:
        row = conn.execute(text(
            "SELECT sha256 FROM dailymed_ingest_log WHERE setid=:s"
        ), {"s": setid}).first()
    return bool(row and row[0] == sha)


def _record_ingest(db: DatabaseManager, setid: str, ndc: Optional[str],
                    sha: str, sections: int, status: str = "ok") -> None:
    from sqlalchemy import text
    with db.engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO dailymed_ingest_log (setid, ndc_code, sha256, parsed_at, sections, status) "
            "VALUES (:s, :n, :h, :t, :sec, :st) "
            "ON CONFLICT(setid) DO UPDATE SET "
            "ndc_code=excluded.ndc_code, sha256=excluded.sha256, "
            "parsed_at=excluded.parsed_at, sections=excluded.sections, "
            "status=excluded.status"
        ), {"s": setid, "n": ndc, "h": sha,
            "t": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "sec": sections, "st": status})


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _http_get(url: str, *, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": "MedPharm-ERP/1.7.6 (load_dailymed_spl.py; +https://github.com/stillwell/MedPharm)",
        "Accept": "application/xml, application/json",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _ratelimit_sleep(last_call: dict, key: str = "default",
                      delay: float = DM_RATE_LIMIT_SECONDS) -> None:
    now = time.time()
    elapsed = now - last_call.get(key, 0.0)
    if elapsed < delay:
        time.sleep(delay - elapsed)
    last_call[key] = time.time()


def _ndc_variants(ndc: str) -> list[str]:
    """Return NDC formats DailyMed will accept.

    FDA registers labelers with 4-, 5-, or 6-digit codes. The FDA NDC
    Directory exports the "11-digit normalized" form (5-4-2 with leading
    zeros) — but DailyMed's search wants the labeler in its native
    registered form. So '00002-1152' from FDA is '0002-1152' to DailyMed.
    Try multiple variants so the lookup works regardless of how the NDC
    was registered.
    """
    parts = ndc.split("-")
    if len(parts) < 2:
        return [ndc]
    labeler, product = parts[0], parts[1]
    package = parts[2] if len(parts) > 2 else None
    variants = [labeler + "-" + product]
    # Strip one leading zero from a 5-digit labeler.
    if len(labeler) >= 5 and labeler.startswith("0"):
        variants.append(labeler[1:] + "-" + product)
        if labeler.startswith("00"):
            variants.append(labeler[2:] + "-" + product)
    # Pad a 4-digit labeler up to 5.
    if len(labeler) == 4:
        variants.append("0" + labeler + "-" + product)
    # Trim/pad product to 3 or 4 digits.
    if len(product) >= 4 and product.startswith("0"):
        variants.append(labeler + "-" + product[1:])
    if package and len(package) == 2 and package == "00":
        # The FDA loader synthesises -00 when only the product code is known.
        # Drop it for DailyMed lookups; it would be rejected.
        pass
    # Dedup, preserve order.
    seen = set()
    out = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _spl_setid_for_ndc(ndc: str, last_call: dict) -> Optional[str]:
    """Look up the DailyMed setid for an NDC via the v2 search API.
    Returns None if no SPL is published for that NDC. Tries the NDC in
    several common format variants since FDA and DailyMed disagree on
    leading-zero conventions for the labeler."""
    import json as _json
    for variant in _ndc_variants(ndc):
        _ratelimit_sleep(last_call, key="search")
        url = f"{DM_SEARCH_BY_NDC}?ndc={variant}"
        try:
            data = _json.loads(_http_get(url))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                continue
            raise
        items = data.get("data") or []
        for item in items:
            setid = item.get("setid") or item.get("set_id")
            if setid:
                return setid
    return None


def _fetch_spl_xml(setid: str, cache_dir: Path, last_call: dict,
                    *, force: bool = False) -> Optional[bytes]:
    """Fetch the SPL XML for a given setid, with on-disk cache. Returns the
    raw bytes (or None on permanent error)."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / f"{setid}.xml"
    if cached.exists() and cached.stat().st_size > 0 and not force:
        return cached.read_bytes()
    _ratelimit_sleep(last_call, key="spl")
    url = DM_SPL_XML.format(setid=setid)
    try:
        body = _http_get(url, timeout=120)
    except urllib.error.HTTPError as exc:
        print(f"  [spl] HTTP {exc.code} for setid {setid}; skipping")
        return None
    cached.write_bytes(body)
    return body


# ── SPL parsing ───────────────────────────────────────────────────────────────

_WS_RE = re.compile(r"\s+")


def _section_text(section_el) -> str:
    r"""Extract plain text from an SPL <section><text> tree.

    SPL bodies are nested HL7 paragraphs / lists / tables. We don't care
    about the exact markup — we just want readable text suitable for a UI
    label. Itertext gathers descendant text in document order; a single
    \s+→space normalize keeps it tractable.
    """
    text_el = section_el.find("hl7:text", NS)
    if text_el is None:
        return ""
    raw = "".join(text_el.itertext())
    return _WS_RE.sub(" ", raw).strip()


def _section_loinc(section_el) -> Optional[str]:
    code_el = section_el.find("hl7:code", NS)
    if code_el is None:
        return None
    return code_el.get("code")


def _extract_setid(root) -> Optional[str]:
    sid = root.find("hl7:setId", NS)
    return sid.get("root") if sid is not None else None


def _extract_ndcs(root) -> list[str]:
    """Walk the SPL product structure to find every NDC the label covers.

    SPL: <component><structuredBody><component><section><subject><manufacturedProduct>
         <manufacturedProduct><asEntityWithGeneric>... NDC codes appear as
         <code code="..." codeSystem="2.16.840.1.113883.6.69"/> (NDC OID).

    We are tolerant of structure variation across SPL versions — just
    iterate every <code> element and keep ones with the NDC codeSystem.
    """
    NDC_OID = "2.16.840.1.113883.6.69"
    ndcs = []
    for code in root.iter(f"{{{SPL_NAMESPACE}}}code"):
        if code.get("codeSystem") == NDC_OID:
            ndc = code.get("code")
            if ndc:
                ndcs.append(ndc)
    # De-dup, preserve order.
    seen = set()
    out = []
    for n in ndcs:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def _normalize_ndc(raw: str) -> str:
    """Match the canonicalisation used by load_fda_data.py so the join works."""
    if not raw:
        return ""
    parts = raw.split("-")
    if len(parts) == 2:
        return f"{parts[0].zfill(5)}-{parts[1].zfill(4)}-00"
    if len(parts) == 3:
        return f"{parts[0].zfill(5)}-{parts[1].zfill(4)}-{parts[2].zfill(2)}"
    return raw


def parse_spl_xml(xml_bytes: bytes) -> dict:
    """Parse SPL XML and return a dict suitable for upsert.

    Returns:
        {
            "setid": str | None,
            "ndcs": [str],
            "sections": {logical_name: text}     # only the LOINC codes we map
        }
    """
    parser = etree.XMLParser(huge_tree=True, recover=True, resolve_entities=False)
    root = etree.fromstring(xml_bytes, parser=parser)
    sections = {}
    for sec in root.iter(f"{{{SPL_NAMESPACE}}}section"):
        loinc = _section_loinc(sec)
        if loinc and loinc in LOINC_SECTIONS:
            text = _section_text(sec)
            if text:
                logical = LOINC_SECTIONS[loinc]
                # Some labels split a section into multiple <section> elements
                # (e.g. multi-page warnings). Concatenate.
                if logical in sections:
                    sections[logical] += "\n\n" + text
                else:
                    sections[logical] = text
    return {
        "setid": _extract_setid(root),
        "ndcs": _extract_ndcs(root),
        "sections": sections,
    }


# ── Apply parsed sections to the medications table ────────────────────────────

def _apply_to_medications(db: DatabaseManager, parsed: dict) -> int:
    """Update Medication rows that match any NDC in `parsed["ndcs"]`.

    Returns the number of rows updated.
    """
    sections = parsed.get("sections") or {}
    if not sections:
        return 0
    indications = sections.get("indications") or None
    contraindications = sections.get("contraindications") or None
    # Combine adverse_reactions + warnings + boxed_warning into side_effects so
    # the existing schema slot reflects everything safety-relevant on the label.
    side_effects_parts = []
    for key in ("boxed_warning", "warnings", "adverse_reactions"):
        if sections.get(key):
            side_effects_parts.append(sections[key])
    side_effects = "\n\n".join(side_effects_parts) or None
    description = sections.get("dosage") or None

    updated = 0
    canonical = [_normalize_ndc(n) for n in parsed.get("ndcs", []) if n]
    if not canonical:
        return 0
    with db.get_session() as session:
        # Match on the leading NDC segment (labeler-product) too, since the
        # FDA NDC loader stores 11-digit '-2' suffix and SPL NDCs are usually
        # 9-digit. We canonicalise both sides in _normalize_ndc, so a direct
        # in_(...) match works for the common case.
        rows = session.query(Medication).filter(
            Medication.ndc_code.in_(canonical)
        ).all()
        if not rows:
            # Try prefix match on the labeler-product portion (first 10 chars).
            prefixes = sorted({n[:10] for n in canonical})
            for pfx in prefixes:
                like = pfx + "%"
                rows.extend(session.query(Medication).filter(
                    Medication.ndc_code.like(like)
                ).all())
        for m in rows:
            if indications:
                m.indications = indications
            if contraindications:
                m.contraindications = contraindications
            if side_effects:
                m.side_effects = side_effects
            if description:
                m.description = description
            updated += 1
    return updated


# ── Source iterators ──────────────────────────────────────────────────────────

def _iter_xmls_from_dir(path: Path) -> Iterator[tuple[str, bytes]]:
    for f in sorted(path.rglob("*.xml")):
        yield (str(f), f.read_bytes())


def _iter_xmls_from_zip(path: Path) -> Iterator[tuple[str, bytes]]:
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            if info.filename.lower().endswith(".xml") and not info.is_dir():
                with zf.open(info) as fh:
                    yield (info.filename, fh.read())


def _iter_xmls_from_ndc_list(ndcs: Iterable[str], cache_dir: Path,
                              last_call: dict, force: bool = False
                              ) -> Iterator[tuple[str, bytes]]:
    for ndc in ndcs:
        ndc = ndc.strip()
        if not ndc:
            continue
        setid = _spl_setid_for_ndc(ndc, last_call)
        if not setid:
            print(f"  [fetch] no SPL for NDC {ndc}")
            continue
        body = _fetch_spl_xml(setid, cache_dir, last_call, force=force)
        if body:
            yield (f"<api:{setid}>", body)


def _top_n_ndcs(db: DatabaseManager, n: int) -> list[str]:
    """Pick N NDCs from the local medications table to enrich.

    Strategy: prefer rows that don't yet have indications / side_effects
    populated (so each enrichment pass adds new content) and that have
    a non-pseudo NDC (skip DSLD-tagged synthetic codes). Order by ID
    for determinism.
    """
    with db.get_session() as session:
        q = session.query(Medication.ndc_code).filter(
            Medication.is_active == True,
            Medication.ndc_code.isnot(None),
            ~Medication.ndc_code.startswith("DSLD-"),
            Medication.indications.is_(None),
        ).order_by(Medication.id).limit(n)
        return [r[0] for r in q.all() if r[0]]


# ── Driver ────────────────────────────────────────────────────────────────────

def _run_ingest(db: DatabaseManager, source_iter: Iterable[tuple[str, bytes]],
                 *, max_files: Optional[int] = None,
                 dry_run: bool = False, force: bool = False) -> dict:
    _ensure_log_table(db)
    n_seen = n_skipped = n_parsed = n_updated_rows = n_errors = 0
    started = time.time()
    for label, xml_bytes in source_iter:
        n_seen += 1
        sha = hashlib.sha256(xml_bytes).hexdigest()
        try:
            parsed = parse_spl_xml(xml_bytes)
        except Exception as exc:
            n_errors += 1
            print(f"  [parse-error] {label}: {exc}")
            continue
        setid = parsed.get("setid") or label
        if not force and _already_ingested(db, setid, sha):
            n_skipped += 1
        else:
            if dry_run:
                pass   # parsed but not written
            else:
                rows = _apply_to_medications(db, parsed)
                _record_ingest(db, setid, (parsed["ndcs"] or [None])[0],
                               sha, len(parsed.get("sections") or {}))
                n_updated_rows += rows
            n_parsed += 1
        if n_seen % 50 == 0:
            elapsed = max(time.time() - started, 0.001)
            print(f"  [ingest] seen={n_seen} parsed={n_parsed} skipped={n_skipped} "
                  f"updated_rows={n_updated_rows} err={n_errors} "
                  f"rate={n_seen/elapsed:.1f} files/s")
        if max_files is not None and n_seen >= max_files:
            break
    elapsed = max(time.time() - started, 0.001)
    print(f"  [ingest] DONE seen={n_seen} parsed={n_parsed} skipped={n_skipped} "
          f"updated_rows={n_updated_rows} err={n_errors} "
          f"in {elapsed:.1f}s ({n_seen/elapsed:.1f} files/s)")
    return {
        "seen": n_seen, "parsed": n_parsed, "skipped": n_skipped,
        "updated_rows": n_updated_rows, "errors": n_errors,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Enrich the medications table with DailyMed SPL data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("mode", choices=["fetch", "parse", "show"],
                   help="fetch (use NLM REST API), parse (local files), "
                        "show (report ingest log)")
    src = p.add_argument_group("source selection (one of)")
    src.add_argument("--ndc", action="append", default=[],
                     help="(fetch) one NDC; repeatable")
    src.add_argument("--ndc-list", type=Path,
                     help="(fetch) file with one NDC per line")
    src.add_argument("--top", type=int, default=None,
                     help="(fetch) ingest top N NDCs from the local table that "
                          "lack indications. Useful for incremental enrichment.")
    src.add_argument("--from-dir", type=Path,
                     help="(parse) directory of *.xml SPL files")
    src.add_argument("--from-zip", type=Path,
                     help="(parse) ZIP file containing SPL *.xml entries")

    p.add_argument("--db-path", default=None,
                   help="SQLite DB path (default: $MEDPHARM_DB_PATH or "
                        "medpharm_erp.db)")
    p.add_argument("--cache-dir", default=str(CACHE_DIR_DEFAULT),
                   help=f"SPL download cache (default: {CACHE_DIR_DEFAULT})")
    p.add_argument("--max-files", type=int, default=None,
                   help="Cap files processed (testing)")
    p.add_argument("--dry-run", action="store_true",
                   help="Parse and report, do not update the medications table")
    p.add_argument("--force", action="store_true",
                   help="Re-ingest even when sha256 in dailymed_ingest_log matches")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    db_path = (args.db_path or os.environ.get("MEDPHARM_DB_PATH")
               or str(_ROOT / "medpharm_erp.db"))
    cache_dir = Path(args.cache_dir)
    db = DatabaseManager(db_path)
    db.init_db()

    print(f"DB:     {db_path}")
    print(f"Cache:  {cache_dir}")
    print(f"Mode:   {args.mode}{' (DRY RUN)' if args.dry_run else ''}")

    if args.mode == "show":
        from sqlalchemy import text
        _ensure_log_table(db)
        with db.engine.begin() as conn:
            n = conn.execute(text("SELECT COUNT(*) FROM dailymed_ingest_log")).scalar()
            print(f"\ndailymed_ingest_log: {n} rows")
            for row in conn.execute(text(
                "SELECT setid, ndc_code, sections, status, parsed_at "
                "FROM dailymed_ingest_log ORDER BY parsed_at DESC LIMIT 20"
            )):
                print(f"  {row[4]} | {row[3]:5s} | {row[2]:2d} sec | ndc={row[1] or '-'} | {row[0]}")
        return 0

    last_call: dict = {}
    if args.mode == "fetch":
        ndcs = list(args.ndc)
        if args.ndc_list:
            ndcs.extend(args.ndc_list.read_text().splitlines())
        if args.top is not None:
            top_ndcs = _top_n_ndcs(db, args.top)
            print(f"  [top] selected {len(top_ndcs)} NDCs from local table")
            ndcs.extend(top_ndcs)
        ndcs = [n.strip() for n in ndcs if n.strip()]
        if not ndcs:
            print("ERROR: fetch mode requires --ndc / --ndc-list / --top")
            return 2
        print(f"  [fetch] queueing {len(ndcs)} NDC(s); rate-limit "
              f"{DM_RATE_LIMIT_SECONDS}s/req")
        source = _iter_xmls_from_ndc_list(ndcs, cache_dir, last_call,
                                            force=args.force)
        _run_ingest(db, source, max_files=args.max_files,
                    dry_run=args.dry_run, force=args.force)
    elif args.mode == "parse":
        if args.from_dir:
            source = _iter_xmls_from_dir(args.from_dir)
        elif args.from_zip:
            source = _iter_xmls_from_zip(args.from_zip)
        else:
            print("ERROR: parse mode requires --from-dir or --from-zip")
            return 2
        _run_ingest(db, source, max_files=args.max_files,
                    dry_run=args.dry_run, force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
