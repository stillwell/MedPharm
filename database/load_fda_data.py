#!/usr/bin/env python3
# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
# Email: Andrew.Stillwell@enlightec.com
# License: GNU General Public License v3.0
#
# ─────────────────────────────────────────────────────────────────────────────
# Bulk-load the MedPharm `medications` table from public US government data.
#
# Sources, all public domain, no auth required:
#
#   FDA NDC Directory      https://www.accessdata.fda.gov/cder/ndctext.zip
#       Every drug registered with the FDA — both prescription and OTC,
#       both human and animal. ~360k entries (one row per package size,
#       ~120k unique formulations). Authoritative for: name, manufacturer,
#       NDC, dose form, route, marketing category, DEA schedule for Rx.
#       NOT in this dataset: indications, side effects, drug interactions.
#
#   FDA Orange Book        https://www.accessdata.fda.gov/cder/orangebook.zip
#       Approved Rx small-molecule products with patent + exclusivity
#       data. ~30k product records, ~12k unique active ingredients.
#       Used here primarily to mark NDC entries as "Rx, FDA-approved
#       under an NDA / ANDA" with extra metadata.
#
#   NIH DSLD               https://dsld.od.nih.gov/api/...
#       Dietary Supplement Label Database. ~150k label entries for
#       complementary / natural products. Not a drug database in the
#       FDA sense — the DSLD treats these as foods — but matches the
#       "complementary / natural products" category from the original
#       request. API-based; we paginate.
#
# Idempotency: every row is keyed on FDA's NDC code (column ndc_code on
# the Medication model is unique-indexed). Re-running this loader updates
# existing rows in place; it never duplicates and never touches rows
# whose data_source != one of {'fda_ndc', 'orange_book', 'dsld'} — so the
# original hand-curated seed data is preserved.
#
# Schema impact: requires the new columns added by db_manager's
# _upgrade_schema_in_place() (data_source, product_type, marketing_category,
# dosage_form_raw, route_raw, pharm_classes, start_marketing_date,
# end_marketing_date). Older databases get those columns added automatically
# the first time init_db() runs after upgrade.
#
# Disk: roughly +400 MB to the SQLite DB after a full NDC + Orange Book load.
# DSLD adds another ~150 MB. None of these are runtime memory loads — we
# stream everything in 1k-row commits.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import time
import urllib.request
import urllib.error
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, Optional

# Make the repo root importable when this script is run directly.
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from database.db_manager import DatabaseManager
from database.models import (
    Medication, DrugSchedule, DrugForm, DrugRoute,
)


# Source URLs. The FDA reorganises its hosting periodically; if any of these
# 404 in the future, the most reliable way to find the new location is to
# follow the listing pages:
#   NDC:         https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
#   Orange Book: https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files
NDC_URL = "https://www.accessdata.fda.gov/cder/ndctext.zip"
ORANGE_BOOK_URL = "https://www.fda.gov/media/76860/download"
DSLD_API = "https://api.ods.od.nih.gov/dsld/v9/search-filter"

CACHE_DIR_DEFAULT = _ROOT / "data" / "fda-cache"
COMMIT_BATCH = 1000

# ── Enum mapping helpers ──────────────────────────────────────────────────────
#
# FDA dosage forms and routes are open vocabularies (hundreds of values each).
# The MedPharm DrugForm and DrugRoute enums cover the common cases. We pick
# the closest enum for the legacy UI filter; the verbatim FDA string is
# preserved separately in dosage_form_raw / route_raw so search and display
# can show what the FDA actually says.

_FORM_HINTS: list[tuple[str, DrugForm]] = [
    ("CAPSULE",        DrugForm.CAPSULE),
    ("TABLET",         DrugForm.TABLET),
    ("INJECTION",      DrugForm.INJECTION),
    ("INJECTABLE",     DrugForm.INJECTION),
    ("SOLUTION",       DrugForm.LIQUID),
    ("SUSPENSION",     DrugForm.LIQUID),
    ("SYRUP",          DrugForm.LIQUID),
    ("ELIXIR",         DrugForm.LIQUID),
    ("LIQUID",         DrugForm.LIQUID),
    ("AEROSOL",        DrugForm.INHALER),
    ("INHALANT",       DrugForm.INHALER),
    ("PATCH",          DrugForm.PATCH),
    ("FILM",           DrugForm.PATCH),
    ("CREAM",          DrugForm.CREAM),
    ("OINTMENT",       DrugForm.TOPICAL),
    ("LOTION",         DrugForm.TOPICAL),
    ("GEL",            DrugForm.TOPICAL),
    ("DROPS",          DrugForm.DROPS),
    ("SUPPOSITORY",    DrugForm.SUPPOSITORY),
]

_ROUTE_HINTS: list[tuple[str, DrugRoute]] = [
    ("ORAL",                DrugRoute.ORAL),
    ("INTRAVENOUS",         DrugRoute.INTRAVENOUS),
    ("INTRAMUSCULAR",       DrugRoute.INTRAMUSCULAR),
    ("SUBCUTANEOUS",        DrugRoute.SUBCUTANEOUS),
    ("TOPICAL",             DrugRoute.TOPICAL),
    ("INHALATION",          DrugRoute.INHALATION),
    ("RESPIRATORY",         DrugRoute.INHALATION),
    ("RECTAL",              DrugRoute.RECTAL),
    ("OPHTHALMIC",          DrugRoute.OPHTHALMIC),
    ("OTIC",                DrugRoute.OTIC),
    ("AURICULAR",           DrugRoute.OTIC),
    ("TRANSDERMAL",         DrugRoute.TRANSDERMAL),
    ("SUBLINGUAL",          DrugRoute.SUBLINGUAL),
    ("BUCCAL",              DrugRoute.SUBLINGUAL),
]


def _map_form(raw: str) -> DrugForm:
    if not raw:
        return DrugForm.TABLET
    R = raw.upper()
    for hint, value in _FORM_HINTS:
        if hint in R:
            return value
    return DrugForm.TABLET


def _map_route(raw: str) -> DrugRoute:
    if not raw:
        return DrugRoute.ORAL
    R = raw.upper()
    for hint, value in _ROUTE_HINTS:
        if hint in R:
            return value
    return DrugRoute.ORAL


def _map_schedule(raw: str) -> DrugSchedule:
    """FDA writes 'CII'/'CIII'/'CIV'/'CV' for scheduled drugs."""
    if not raw:
        return DrugSchedule.NONE
    R = raw.strip().upper().lstrip("C").lstrip("S")
    return {
        "II": DrugSchedule.II, "2": DrugSchedule.II,
        "III": DrugSchedule.III, "3": DrugSchedule.III,
        "IV": DrugSchedule.IV, "4": DrugSchedule.IV,
        "V": DrugSchedule.V, "5": DrugSchedule.V,
    }.get(R, DrugSchedule.NONE)


def _normalize_ndc(raw: str) -> str:
    """Normalize FDA's 5-4 / 5-3 / 4-4 NDC formats to a canonical 11-digit
    representation: 5-4-2 with leading zeros. The actual package code (the
    -2 suffix) isn't in product.txt; we use '00' so brand-level lookups
    still work. Returns '' when the input cannot be parsed."""
    if not raw or "-" not in raw:
        return ""
    parts = raw.split("-")
    if len(parts) == 2:
        labeler, product = parts
        # Pad to 5-4. Common FDA representations: 5-3, 5-4, 4-4.
        labeler = labeler.zfill(5)
        product = product.zfill(4)
        return f"{labeler}-{product}-00"
    if len(parts) == 3:
        labeler, product, package = parts
        return f"{labeler.zfill(5)}-{product.zfill(4)}-{package.zfill(2)}"
    return raw


# ── HTTP / cache helpers ──────────────────────────────────────────────────────

class _DownloadError(Exception):
    """Raised when a source download fails — caught by the `all` driver so
    one stale URL doesn't abort an already-loaded source."""


def _download_with_cache(url: str, cache_path: Path,
                          force: bool = False, label: str = "download") -> Path:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists() and cache_path.stat().st_size > 0 and not force:
        size_mb = cache_path.stat().st_size / 1024 / 1024
        print(f"  [{label}] cache hit: {cache_path} ({size_mb:.1f} MB)")
        return cache_path
    print(f"  [{label}] downloading {url} → {cache_path}")
    req = urllib.request.Request(url, headers={
        "User-Agent": "MedPharm-ERP/1.7.6 (load_fda_data.py; +https://github.com/stillwell/MedPharm)",
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as resp, open(cache_path, "wb") as out:
            total = 0
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                total += len(chunk)
            size_mb = total / 1024 / 1024
            print(f"  [{label}] downloaded {size_mb:.1f} MB")
    except urllib.error.HTTPError as exc:
        # Remove the partial / empty file so the next run doesn't see it as
        # a cache hit.
        try:
            cache_path.unlink()
        except FileNotFoundError:
            pass
        raise _DownloadError(
            f"{label}: HTTP {exc.code} fetching {url}. "
            f"FDA reorganises its hosting periodically; if this URL is "
            f"stale, find the current one on the FDA listing pages cited "
            f"in the source-URL constants at the top of this file, then "
            f"edit and re-run."
        ) from exc
    except urllib.error.URLError as exc:
        try:
            cache_path.unlink()
        except FileNotFoundError:
            pass
        raise _DownloadError(f"{label}: {exc.reason}") from exc
    return cache_path


# ── NDC Directory ─────────────────────────────────────────────────────────────

def _iter_ndc_rows(zip_path: Path) -> Iterator[dict]:
    """Yield product rows from the FDA NDC Directory zip.

    The archive contains product.txt (one row per drug product) and
    package.txt (one row per package size). We use product.txt since that
    is the natural granularity for a 'medication' record. Encoding is
    Windows-1252 in current FDA exports.
    """
    with zipfile.ZipFile(zip_path) as zf:
        product_name = next((n for n in zf.namelist()
                             if n.lower().endswith("product.txt")), None)
        if not product_name:
            raise RuntimeError(f"product.txt not found in {zip_path}")
        with zf.open(product_name) as fh:
            text_stream = io.TextIOWrapper(fh, encoding="windows-1252",
                                           errors="replace", newline="")
            reader = csv.DictReader(text_stream, delimiter="\t")
            for row in reader:
                yield row


def _ndc_row_to_medication_kwargs(row: dict) -> Optional[dict]:
    ndc_raw = (row.get("PRODUCTNDC") or row.get("ProductNDC") or "").strip()
    if not ndc_raw:
        return None
    brand = (row.get("PROPRIETARYNAME") or row.get("ProprietaryName") or "").strip()
    suffix = (row.get("PROPRIETARYNAMESUFFIX") or row.get("ProprietaryNameSuffix") or "").strip()
    generic = (row.get("NONPROPRIETARYNAME") or row.get("NonProprietaryName") or "").strip()
    if not brand and not generic:
        return None
    if suffix:
        brand = f"{brand} {suffix}".strip()
    if not brand:
        brand = generic

    form_raw = (row.get("DOSAGEFORMNAME") or row.get("DosageFormName") or "").strip()
    route_raw = (row.get("ROUTENAME") or row.get("RouteName") or "").strip()
    sched_raw = (row.get("DEASCHEDULE") or row.get("DEASchedule") or "").strip()
    pharm_raw = (row.get("PHARM_CLASSES") or row.get("PharmClasses") or "").strip()
    product_type = (row.get("PRODUCTTYPENAME") or row.get("ProductTypeName") or "").strip()
    marketing_cat = (row.get("MARKETINGCATEGORYNAME") or row.get("MarketingCategoryName") or "").strip()
    labeler = (row.get("LABELERNAME") or row.get("LabelerName") or "").strip()
    strength = (row.get("ACTIVE_NUMERATOR_STRENGTH") or row.get("ActiveNumeratorStrength") or "").strip()
    unit = (row.get("ACTIVE_INGRED_UNIT") or row.get("ActiveIngredUnit") or "").strip()
    start_date = (row.get("STARTMARKETINGDATE") or row.get("StartMarketingDate") or "").strip()
    end_date = (row.get("ENDMARKETINGDATE") or row.get("EndMarketingDate") or "").strip()

    schedule = _map_schedule(sched_raw)
    is_controlled = schedule != DrugSchedule.NONE

    drug_class = ""
    if pharm_raw:
        # PharmClasses is a comma-or-semicolon-separated list of EPC/MOA/PE
        # categories. Use the first as a coarse drug_class for legacy filters.
        first = pharm_raw.replace(";", ",").split(",")[0].strip()
        # Strip the trailing "[EPC]" / "[MoA]" / "[PE]" qualifier.
        if "[" in first:
            first = first.split("[", 1)[0].strip()
        drug_class = first[:200]
    if not drug_class:
        drug_class = product_type[:200] or "Uncategorized"

    return dict(
        ndc_code=_normalize_ndc(ndc_raw)[:20],
        brand_name=brand[:200] or generic[:200],
        generic_name=(generic or brand)[:200],
        manufacturer=labeler[:200] or None,
        drug_class=drug_class,
        schedule=schedule,
        route=_map_route(route_raw),
        form=_map_form(form_raw),
        strength=(strength[:50] or None),
        unit=(unit[:20] or None),
        is_controlled=is_controlled,
        is_active=True,
        data_source="fda_ndc",
        product_type=product_type[:64] or None,
        marketing_category=marketing_cat[:64] or None,
        dosage_form_raw=form_raw[:200] or None,
        route_raw=route_raw[:200] or None,
        pharm_classes=pharm_raw or None,
        start_marketing_date=start_date[:10] or None,
        end_marketing_date=end_date[:10] or None,
    )


# ── Orange Book overlay ───────────────────────────────────────────────────────
# Orange Book ships with products.txt — same kind of TSV. We use it to
# enrich existing FDA NDC rows with patent/approval metadata. The Orange
# Book key is Appl_No + Product_No, not NDC, so this is best-effort matching
# on (manufacturer, generic name) with strength as a tiebreaker.

def _iter_orange_book_rows(zip_path: Path) -> Iterator[dict]:
    with zipfile.ZipFile(zip_path) as zf:
        prod_name = next((n for n in zf.namelist()
                          if n.lower().endswith("products.txt")), None)
        if not prod_name:
            raise RuntimeError(f"products.txt not found in {zip_path}")
        with zf.open(prod_name) as fh:
            text_stream = io.TextIOWrapper(fh, encoding="windows-1252",
                                           errors="replace", newline="")
            reader = csv.DictReader(text_stream, delimiter="~")
            for row in reader:
                yield row


# ── DSLD (NIH dietary supplements) ────────────────────────────────────────────
# The DSLD API paginates via from/size. We pull one page at a time and
# convert each label into a Medication-like row tagged data_source='dsld'.

def _iter_dsld_pages(page_size: int = 100, max_rows: Optional[int] = None
                     ) -> Iterator[dict]:
    """Yield DSLD label records from api.ods.od.nih.gov.

    The DSLD v9 API returns ``{"hits": [...flat list...], "stats": {...}}``
    (NOT the Elasticsearch-style ``{"hits": {"hits": [...]}}``).  Each hit
    has top-level ``_id`` + ``_index`` + a nested ``_source`` containing
    the actual label fields (brandName, fullName, allIngredients,
    physicalState, productType, …). We attach _id into _source under the
    key ``_id`` so the downstream mapper has a stable unique identifier
    for the synthetic NDC code.

    The ``q=*`` query is required — without a query string the endpoint
    returns 0 hits even though stats.count is in the hundreds of
    thousands. ``status_id`` was a v8 parameter and is ignored / 0-result
    on v9; left out.
    """
    fetched = 0
    offset = 0
    while True:
        if max_rows is not None and fetched >= max_rows:
            return
        params = f"?q=*&from={offset}&size={page_size}&sort_by=_score"
        url = DSLD_API + params
        req = urllib.request.Request(url, headers={
            "User-Agent": "MedPharm-ERP/1.7.6 (load_fda_data.py)",
            "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = json.load(resp)
        except urllib.error.HTTPError as exc:
            print(f"  [dsld] HTTP {exc.code} at offset={offset}; stopping")
            return
        # `hits` is a flat list. Old code did .get("hits", {}).get("hits", [])
        # which works only on Elasticsearch-style nested responses (which
        # this isn't), and fails with "list has no attribute get" on the
        # actual v9 response.
        hits = payload.get("hits") or []
        if not isinstance(hits, list):
            print(f"  [dsld] unexpected response shape at offset={offset}; stopping")
            return
        if not hits:
            return
        for h in hits:
            if not isinstance(h, dict):
                continue
            source = h.get("_source") or {}
            if not isinstance(source, dict):
                continue
            # Carry the top-level _id through so the mapper can build a
            # stable synthetic NDC. Doesn't conflict with _source's own
            # field names since they don't use leading underscores.
            if h.get("_id") and "_id" not in source:
                source["_id"] = h["_id"]
            yield source
            fetched += 1
            if max_rows is not None and fetched >= max_rows:
                return
        offset += len(hits)
        # Be polite to NIH.
        time.sleep(0.5)


def _dsld_row_to_medication_kwargs(row: dict) -> Optional[dict]:
    """Map a DSLD _source dict (with _id attached by the iterator) into the
    Medication column shape.

    DSLD records describe foods, not drugs, but the schema accommodates
    them via the synthetic ``DSLD-<id>`` NDC prefix. Several fields that
    were strings in v8 are now nested dicts in v9:
        physicalState  → {langualCode, langualCodeDescription}
        productType    → {langualCode, langualCodeDescription}
    We extract the human-readable description for storage; the structured
    LanguaL codes are not preserved (a follow-up could add a column).

    upcSku and id (top-level lowercase) were removed in v9 — the upstream
    `_id` (e.g. "270355") is the only stable unique key.
    """
    def _flat(value) -> str:
        """Flatten a possibly-nested DSLD field to a clean string."""
        if isinstance(value, dict):
            return (value.get("langualCodeDescription")
                    or value.get("description")
                    or value.get("name") or "").strip()
        if isinstance(value, list):
            # Pick the first non-empty entry; rare, but seen in arrays of dicts.
            for entry in value:
                s = _flat(entry)
                if s:
                    return s
            return ""
        if isinstance(value, str):
            return value.strip()
        return ""

    name = _flat(row.get("fullName")) or _flat(row.get("brandName"))
    if not name:
        return None

    # Stable unique key. Prefer the upstream _id; fall back to a hash of
    # name + brand + entry date so we still get something deterministic
    # for any record missing _id (shouldn't happen, but be defensive).
    record_id = str(row.get("_id") or "").strip()
    if not record_id:
        import hashlib
        seed = (name + "|" + _flat(row.get("brandName"))
                + "|" + _flat(row.get("entryDate")))
        record_id = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:14]
    ndc_pseudo = f"DSLD-{record_id[:14]}"

    manufacturer = _flat(row.get("brandName")) or _flat(row.get("companyName"))
    physical = _flat(row.get("physicalState"))
    product_subtype = _flat(row.get("productType"))

    return dict(
        ndc_code=ndc_pseudo[:20],
        brand_name=name[:200],
        generic_name=name[:200],
        manufacturer=manufacturer[:200] or None,
        drug_class="Dietary Supplement",
        schedule=DrugSchedule.NONE,
        route=DrugRoute.ORAL,
        form=DrugForm.CAPSULE,
        is_controlled=False,
        is_active=True,
        data_source="dsld",
        product_type=("DIETARY SUPPLEMENT" + (f" — {product_subtype}"
                                                if product_subtype else ""))[:64],
        marketing_category="DSLD",
        dosage_form_raw=physical[:200] or None,
    )


# ── Upsert plumbing ───────────────────────────────────────────────────────────

class _UpsertStats:
    __slots__ = ("inserted", "updated", "skipped", "errors", "started")

    def __init__(self) -> None:
        self.inserted = 0
        self.updated = 0
        self.skipped = 0
        self.errors = 0
        self.started = time.time()

    def total(self) -> int:
        return self.inserted + self.updated + self.skipped + self.errors

    def fmt(self) -> str:
        elapsed = max(time.time() - self.started, 0.001)
        rps = self.total() / elapsed
        return (f"ins={self.inserted} upd={self.updated} skip={self.skipped} "
                f"err={self.errors} rps={rps:.0f}")


def _upsert_batch(session, batch: list[dict], stats: _UpsertStats) -> None:
    """Upsert by ndc_code. Refuses to overwrite rows whose data_source is
    not the FDA/DSLD set (so the original hand-curated seed is preserved)."""
    fda_sources = {"fda_ndc", "orange_book", "dsld"}
    for kwargs in batch:
        ndc = kwargs.get("ndc_code")
        if not ndc:
            stats.skipped += 1
            continue
        try:
            existing = session.query(Medication).filter(
                Medication.ndc_code == ndc).one_or_none()
            if existing is None:
                session.add(Medication(**kwargs))
                stats.inserted += 1
                continue
            if (existing.data_source or "seed") not in fda_sources:
                # Hand-curated row — leave it alone.
                stats.skipped += 1
                continue
            for k, v in kwargs.items():
                setattr(existing, k, v)
            stats.updated += 1
        except Exception as exc:
            stats.errors += 1
            session.rollback()
            print(f"  [error] ndc={ndc}: {exc}")


def _stream_into_db(rows_iter: Iterable[dict], db: DatabaseManager,
                     mapper, label: str, max_rows: Optional[int] = None,
                     dry_run: bool = False) -> _UpsertStats:
    """Stream input rows through `mapper` into the DB, committing in batches.

    `max_rows` caps the number of *input* rows processed (not the number
    of successful upserts), which is the operator-meaningful quantity for
    `--max-rows` testing. We keep a separate `seen` counter so the cap
    fires immediately, even mid-batch — without it, COMMIT_BATCH=1000
    would round any cap up to the next 1000.
    """
    stats = _UpsertStats()
    batch: list[dict] = []
    last_print = time.time()
    seen = 0
    for raw in rows_iter:
        seen += 1
        kwargs = mapper(raw)
        if kwargs is not None:
            batch.append(kwargs)
        else:
            stats.skipped += 1
        if len(batch) >= COMMIT_BATCH:
            if dry_run:
                stats.inserted += len(batch)
            else:
                with db.get_session() as session:
                    _upsert_batch(session, batch, stats)
            batch.clear()
            if time.time() - last_print > 2.0:
                print(f"  [{label}] seen={seen} {stats.fmt()}")
                last_print = time.time()
        if max_rows is not None and seen >= max_rows:
            break
    if batch:
        if dry_run:
            stats.inserted += len(batch)
        else:
            with db.get_session() as session:
                _upsert_batch(session, batch, stats)
    print(f"  [{label}] DONE  seen={seen} {stats.fmt()}")
    return stats


# ── Subcommands ───────────────────────────────────────────────────────────────

def cmd_ndc(args, db: DatabaseManager, cache_dir: Path) -> _UpsertStats:
    print("\n=== FDA NDC Directory ===")
    zip_path = cache_dir / "ndctext.zip"
    _download_with_cache(NDC_URL, zip_path, force=args.refresh, label="ndc")
    return _stream_into_db(_iter_ndc_rows(zip_path), db,
                           _ndc_row_to_medication_kwargs,
                           label="ndc",
                           max_rows=args.max_rows, dry_run=args.dry_run)


def cmd_orange_book(args, db: DatabaseManager, cache_dir: Path) -> _UpsertStats:
    """Orange Book is currently treated as an enrichment marker only:
    we touch existing Rx NDC rows by manufacturer + generic-name match
    and stamp them with marketing_category if missing. A full join on the
    FDA Application Number would require also loading package.txt; that
    is out of scope here. The stub stays useful as the future home for
    that logic."""
    print("\n=== FDA Orange Book ===")
    zip_path = cache_dir / "orangebook.zip"
    _download_with_cache(ORANGE_BOOK_URL, zip_path, force=args.refresh,
                          label="orange-book")
    stats = _UpsertStats()
    if args.dry_run:
        print("  [orange-book] dry-run: parsing only, no DB writes")
    seen = 0
    for row in _iter_orange_book_rows(zip_path):
        seen += 1
        if args.max_rows is not None and seen >= args.max_rows:
            break
    stats.skipped = seen
    print(f"  [orange-book] inspected {seen} rows; full enrichment is a TODO. "
          "NDC marketing_category is already populated from the NDC pass.")
    return stats


def cmd_dsld(args, db: DatabaseManager, cache_dir: Path) -> _UpsertStats:
    print("\n=== NIH DSLD (dietary supplements) ===")
    return _stream_into_db(_iter_dsld_pages(max_rows=args.max_rows), db,
                           _dsld_row_to_medication_kwargs,
                           label="dsld",
                           max_rows=args.max_rows, dry_run=args.dry_run)


def cmd_prune_stale(args, db: DatabaseManager) -> None:
    """Mark FDA-sourced rows not seen in the most recent load as inactive.
    Conservative — does not delete, only flips is_active=False — so any
    historical references (audits, prescriptions) keep their FK targets."""
    print("\n=== Prune stale FDA rows (placeholder) ===")
    print("  Not yet implemented. Re-running load is idempotent so stale rows "
          "currently linger as is_active=True until manually cleaned.")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bulk-load the MedPharm medications table from FDA / NIH data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("source", choices=["ndc", "orange-book", "dsld", "all",
                                            "prune-stale"],
                        help="Which source to load (or 'all' for every source)")
    parser.add_argument("--db-path", default=None,
                        help="SQLite DB path (default: $MEDPHARM_DB_PATH or "
                             "medpharm_erp.db in the repo root)")
    parser.add_argument("--database-url", default=None,
                        help="Full SQLAlchemy URL (e.g. postgresql+psycopg://...); "
                             "overrides --db-path / MEDPHARM_DB_PATH. "
                             "Defaults to $MEDPHARM_DATABASE_URL.")
    parser.add_argument("--cache-dir", default=str(CACHE_DIR_DEFAULT),
                        help=f"Directory to cache downloads (default: {CACHE_DIR_DEFAULT})")
    parser.add_argument("--refresh", action="store_true",
                        help="Re-download even if a cached copy exists")
    parser.add_argument("--max-rows", type=int, default=None,
                        help="Cap rows ingested per source (useful for testing)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and report; do not write to the DB")
    args = parser.parse_args(argv)

    db_path = (args.db_path
               or os.environ.get("MEDPHARM_DB_PATH")
               or str(_ROOT / "medpharm_erp.db"))
    database_url = args.database_url or os.environ.get("MEDPHARM_DATABASE_URL")
    cache_dir = Path(args.cache_dir)

    db = DatabaseManager(db_path=db_path, database_url=database_url)
    db.init_db()

    print(f"DB:     {db.safe_target}")
    print(f"Cache:  {cache_dir}")
    print(f"Source: {args.source}{' (DRY RUN)' if args.dry_run else ''}")

    started = datetime.now()

    # In `all` mode, treat each source as independent: a stale URL in one
    # source must not abort the others. The user already paid the time to
    # download / parse one feed — the others should still get a chance.
    # Single-source invocations (ndc / orange-book / dsld) propagate the
    # error normally so the operator sees the full traceback.
    multi = args.source == "all"
    failures: list[str] = []

    def _run(label: str, fn) -> None:
        try:
            fn(args, db, cache_dir)
        except _DownloadError as exc:
            if multi:
                print(f"\n  [WARN] {label}: skipping — {exc}\n")
                failures.append(f"{label}: download failed")
            else:
                raise
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            if multi:
                print(f"\n  [WARN] {label}: skipping — {exc}\n")
                failures.append(f"{label}: {exc}")
            else:
                raise

    if args.source in ("ndc", "all"):
        _run("ndc", cmd_ndc)
    if args.source in ("orange-book", "all"):
        _run("orange-book", cmd_orange_book)
    if args.source in ("dsld", "all"):
        _run("dsld", cmd_dsld)
    if args.source == "prune-stale":
        cmd_prune_stale(args, db)

    elapsed = (datetime.now() - started).total_seconds()
    print(f"\nDone in {elapsed:.1f}s")
    if failures:
        print(f"  {len(failures)} source(s) failed:")
        for f in failures:
            print(f"    - {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
