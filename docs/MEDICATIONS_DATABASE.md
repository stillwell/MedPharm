# MedPharm — Loading the Medications Catalogue

MedPharm ships with a small hand-curated set of demonstration medications in
[`database/seed_data.py`](../database/seed_data.py) and
[`database/seed_expanded.py`](../database/seed_expanded.py). For real
deployments, the `medications` table can be bulk-loaded from public US
government data — three loaders, three orthogonal sources, all idempotent
and re-runnable.

| Loader | Source | What it gives you | Disk impact |
|---|---|---|---|
| [`database/load_fda_data.py`](../database/load_fda_data.py) | FDA NDC Directory + NIH DSLD | name, manufacturer, NDC, dose form, route, marketing category, DEA schedule for ~360k Rx + OTC + supplements | ~+400 MB |
| [`database/load_dailymed_spl.py`](../database/load_dailymed_spl.py) | NIH/NLM DailyMed SPL labels | indications, contraindications, side effects, drug interactions, dosage, warnings (extracted from HL7 V3 SPL XML) | depends on how much you ingest; ~50 GB if you load everything |

The loaders are designed to compose: run the FDA loader first to populate
names/codes for the entire catalogue, then run the DailyMed loader to
enrich the rows with prescribing information. Run order matters — the
SPL loader matches by NDC, so the row has to exist first.

---

## Phase 1: FDA NDC Directory + NIH DSLD

```bash
# All three FDA / NIH sources, full pull (~5 min, +400 MB to the SQLite DB)
python3 database/load_fda_data.py all

# Load into a shared PostgreSQL instead of SQLite (catalogue lands in the
# same database every component reads). Honours $MEDPHARM_DATABASE_URL too.
python3 database/load_fda_data.py all \
  --database-url postgresql+psycopg://medpharm:PASS@host:5432/medpharm

# Just the FDA NDC Directory (~360k drug products)
python3 database/load_fda_data.py ndc

# Test the loader without committing to the full pull
python3 database/load_fda_data.py ndc --max-rows 1000
python3 database/load_fda_data.py ndc --dry-run
```

**Subcommands:** `ndc | orange-book | dsld | all | prune-stale`

**Common flags:**
| Flag | Effect |
|---|---|
| `--database-url URL` | Load into a shared database via a full SQLAlchemy URL, e.g. `postgresql+psycopg://medpharm:PASS@host:5432/medpharm` (default: `$MEDPHARM_DATABASE_URL` if set). Takes precedence over `--db-path`. |
| `--db-path PATH` | Override the SQLite path (default: `$MEDPHARM_DB_PATH` or `medpharm_erp.db`); used only when no `--database-url` / `$MEDPHARM_DATABASE_URL` is given |
| `--cache-dir PATH` | Where to cache the downloaded ZIP files (default: `data/fda-cache/`) |
| `--refresh` | Re-download even if a cached copy exists |
| `--max-rows N` | Stop after N input rows — useful for testing |
| `--dry-run` | Parse and report; do not write to the DB |

**Idempotency.** Every row is keyed on the FDA NDC code (column
`ndc_code` is `UNIQUE`). Re-running updates existing rows in place;
never duplicates. The loader **never overwrites** rows whose
`data_source` is not in `{'fda_ndc','orange_book','dsld'}`, so the
original hand-curated seed data is preserved indefinitely.

**Verifying the load.** Use whichever client matches your backend — `sqlite3`
for the default single-file database, or `psql` when the catalogue was loaded
into a shared PostgreSQL via `MEDPHARM_DATABASE_URL` / `--database-url`:

```bash
# SQLite (default)
sqlite3 medpharm_erp.db <<'SQL'
SELECT data_source, COUNT(*) FROM medications GROUP BY data_source;
SELECT product_type, COUNT(*) FROM medications GROUP BY product_type
       ORDER BY 2 DESC LIMIT 5;
SQL

# Shared PostgreSQL (same queries, psql client)
psql "$MEDPHARM_DATABASE_URL" <<'SQL'
SELECT data_source, COUNT(*) FROM medications GROUP BY data_source;
SELECT product_type, COUNT(*) FROM medications GROUP BY product_type
       ORDER BY 2 DESC LIMIT 5;
SQL
```

---

## Phase 3: DailyMed SPL labels (prescribing information)

Two operating modes:

### `fetch` — pull individual SPLs over the NLM REST API

Best for incremental enrichment. Polls
[`dailymed.nlm.nih.gov/dailymed/services/v2`](https://dailymed.nlm.nih.gov/dailymed/services/v2/),
rate-limited to 1 request/sec to be polite.

```bash
# Enrich the next 50 rows in your medications table that lack indications
python3 database/load_dailymed_spl.py fetch --top 50

# Enrich a specific list of NDCs
echo "0002-1152" > /tmp/ndcs.txt
echo "0002-7510" >> /tmp/ndcs.txt
python3 database/load_dailymed_spl.py fetch --ndc-list /tmp/ndcs.txt

# One-off
python3 database/load_dailymed_spl.py fetch --ndc 0002-1152
```

### `parse` — process a directory or ZIP of SPL XML files

Best for the operator who downloads one of the FDA bulk-release ZIPs
([dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm](https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm))
and wants to ingest them offline. No network use.

```bash
# Unzip and point at the directory
unzip -d /tmp/dm-rx prescription_drug_labels_part1.zip
python3 database/load_dailymed_spl.py parse --from-dir /tmp/dm-rx

# Or read directly out of the ZIP without extracting
python3 database/load_dailymed_spl.py parse --from-zip prescription_drug_labels_part1.zip
```

### `show` — inspect the ingest log

```bash
python3 database/load_dailymed_spl.py show
```

**What it extracts.** SPL sections are tagged with LOINC codes; the
loader extracts these and folds them into the existing `Medication`
text fields:

| LOINC | Section | Goes into |
|---|---|---|
| `34067-9` | INDICATIONS & USAGE | `indications` |
| `34070-3` | CONTRAINDICATIONS | `contraindications` |
| `34073-7` | DRUG INTERACTIONS | (concatenated into `side_effects`) |
| `34084-4` | ADVERSE REACTIONS | `side_effects` |
| `34068-7` | DOSAGE & ADMINISTRATION | `description` |
| `34071-1` | WARNINGS | `side_effects` |
| `50742-6` | BOXED WARNING | `side_effects` |

**Resumability.** A `dailymed_ingest_log` table tracks per-setid SHA-256
+ timestamp. A crashed run picks up where it left off; re-running the
same SPLs is a no-op (`skipped`).

---

## How much data should I load?

| Scenario | Suggested loaders | Rows | Disk | Time |
|---|---|---|---|---|
| Demo / dev | (skip — keep the seed data) | ~80 | <1 MB | 0 |
| Realistic catalogue, no clinical text | `load_fda_data.py all` | ~360k | +400 MB | ~5 min |
| Above + top-500 enriched with prescribing info | `+ load_dailymed_spl.py fetch --top 500` | same | +500 MB | ~10 min |
| Full catalogue, all clinical text | `+ load_dailymed_spl.py parse --from-dir <bulk-extract>` | ~360k | +50 GB raw + 1-2 GB DB | hours |

The `--top` strategy lets you grow the enriched subset over time —
re-run weekly with `--top 500` and the catalogue gets richer without
ever needing a multi-hour bulk download.

---

## Performance notes

The FDA load grows the `medications` table from a few hundred rows to
several hundred thousand. The 1.7.6-E schema migration adds three
indexes specifically for this scale:

- `ix_medications_data_source` — for filtering by provenance
- `ix_medications_brand_name_lower` — for case-insensitive prefix search
- `ix_medications_generic_name_lower` — same, on the generic name

The Qt desktop's medication widget and the API
`/medications/search` route both paginate by default (page size 200
and 50 respectively); querying with `limit=None` clamps at 5000 rows
and emits a warning so a stray unbounded query doesn't OOM the
process.

If you need to roll back a bad load, the original seed rows are
preserved (their `data_source = 'seed'`); you can drop the bulk-loaded
ones with:

```sql
DELETE FROM medications WHERE data_source IN ('fda_ndc','orange_book','dsld');
DELETE FROM dailymed_ingest_log;
```

---

## What's NOT in these loaders

| Field | Why not |
|---|---|
| Drug interactions (relational) | DailyMed publishes them as plain text in the SPL DRUG INTERACTIONS section; we ingest that into `side_effects`. The pairwise `medication_interactions` table is populated only by the original seed data; commercial DDI databases (Lexi-Comp, Micromedex) would be needed for comprehensive interaction graphs. |
| Retail / wholesale prices | Not in any free public US source. Operators with pricing-feed contracts can populate `retail_price` / `avg_wholesale_price` separately. |
| Drug images | Not in scope. The DailyMed SPLs do reference images by URL, but we don't download them. |
| RxNorm normalisation | Future work; would help match generic-name variants. The FDA NDC loader already gives a clean canonical generic name in the `generic_name` column. |
