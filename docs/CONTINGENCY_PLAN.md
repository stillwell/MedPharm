# Contingency Plan — Backup, Disaster Recovery, Emergency Mode

**Regulatory basis:** 45 CFR § 164.308(a)(7) (Contingency Plan).
**Required specifications:** Data Backup Plan, Disaster Recovery Plan,
Emergency Mode Operation Plan. **Addressable specifications:** Testing
& Revision Procedures, Applications & Data Criticality Analysis.

This document is the operator-facing playbook. It pairs with the
runbooks in the **Service Manual (Volume II)** of the printed
documentation set and with the templates in `docs/BREACH_NOTIFICATION.md`
and `docs/RISK_ANALYSIS_TEMPLATE.md`.

---

## 1. Applications & Data Criticality Analysis

A loss of any of the following functions is, in clinical or financial
terms, intolerable. They are listed in priority order; recovery
sequencing follows this order.

| Tier | Function | Recovery objective | Why |
|-----:|----------|--------------------|-----|
| **0** | Read-only access to active prescriptions and allergies | **RTO 1 h**, **RPO 24 h** | A patient at the pharmacy with a chronic-disease prescription cannot wait. Allergy data is patient-safety critical. |
| **1** | Patient demographics + active appointment list | **RTO 4 h**, **RPO 24 h** | Front desk needs to verify identity and triage walk-ins. |
| **2** | Full prescribing + records edit | **RTO 24 h**, **RPO 24 h** | Treatment continuity. |
| **3** | Billing + payments + insurance claims | **RTO 72 h**, **RPO 7 d** | Revenue cycle can absorb a few-day delay; cash flow can not. |
| **4** | Analytics, reporting, audit-log query UI | **RTO 1 wk**, **RPO 7 d** | Useful but not patient-safety critical. |

**RTO** = Recovery Time Objective (how soon the function must be
back). **RPO** = Recovery Point Objective (how much data loss is
tolerable).

## 2. Data Backup Plan (§ 164.308(a)(7)(ii)(A))

### Required cadence

- **Daily**, automated, encrypted **full backup** of the database.
- **Hourly** transaction-log backup if the deployment uses
  PostgreSQL/MySQL with WAL/binlog.
- **Weekly** off-site copy (different geographic region for cloud
  deployments; air-gapped storage for on-prem).
- **Monthly** verified-restore exercise on a clean staging instance.
- **Annual** full-stack restore exercise (database + application +
  configuration + TLS material) to a brand-new host.

### What to back up

| Artifact | Where | How |
|----------|-------|-----|
| Database (`medpharm_erp.db` or Postgres dump) | `/data/medpharm_erp.db` (Docker volume `medpharm-data`) | `update.sh` writes a dated copy before each pull; cron job ships off-site |
| Field-encryption keys | Secret manager (Vault, AWS Secrets Manager, GCP Secret Manager) | Replicated by the secret manager — never bundled with the database backup |
| TLS material | `/etc/ssl/medpharm/` | Synchronised separately; rotation cadence per certificate authority |
| Audit-log archive | Database + cold storage | The hash chain is part of the database backup; cold-storage immutable retention is in addition |
| Configuration | `/etc/medpharm/`, env vars | Snapshot to a versioned config repository |
| Container images | Docker Hub registry | Tag immutability; pulled-on-demand for restore |

### Encryption at rest

Backups are encrypted **end-to-end at the producer** before they
leave the application host. The receiving storage tier may add
its own at-rest encryption; that is in addition to, not a substitute
for, producer-side encryption. Key management for the backup
encryption keys is documented in the deployment's key-management
runbook.

### Retention

Database backups are retained on a sliding window:

- 30 days of **daily** backups.
- 12 months of **weekly** backups.
- 7 years of **annual** backups (matches the audit-log retention
  required by § 164.316(b)(2)).

Backups older than the retention window are cryptographically
destroyed (key destruction; the ciphertext is then unreadable and may
be deleted via the storage provider's standard delete).

### Testing

A restore is tested at least monthly. The test must:

1. Pull a recent backup to a clean host.
2. Restore the database.
3. Boot the API and Web Portal containers.
4. Run `python -c "from security.audit import verify_audit_chain; ..."`
   to confirm the audit chain is intact.
5. Run a smoke-test sign-in for one staff and one patient account.
6. Document the test in the contingency-plan log.

A failed restore is a Tier 0 incident: the deployment cannot
operate without a usable backup, by definition.

## 3. Disaster Recovery Plan (§ 164.308(a)(7)(ii)(B))

A *disaster* is any event that renders the primary deployment
unable to meet the RTO of any Tier 0–1 function.

### Activation

The Privacy Officer or Security Officer (or designated alternate)
declares a disaster. Activation is documented in the incident
register with timestamp.

### Sequence

1. **Stand up the recovery deployment** in the secondary region.
   The container image (`enlightec/medpharm-server:{tag}`) is pulled
   from Docker Hub; configuration comes from the version-controlled
   config repository; TLS material from the secret manager.
2. **Restore the most recent verified backup** to the new host.
3. **Pivot DNS** to the new host. (DNS TTL on the production record
   is kept short — 300 s — to make this fast.)
4. **Confirm patient identity** for the first 50 portal sign-ins by
   calling each patient back at their on-file phone number, before
   re-enabling self-serve transactions, in case the recovery
   instance is being targeted.
5. **Run the audit-chain verification.**
6. **Notify the workforce** of the new URL (or that the URL is
   unchanged but the back end has moved).

### Documentation

Every activation is documented in the disaster-recovery log:

- Time the primary failed.
- Time activation declared.
- Time the recovery instance started serving traffic.
- Tier 0–4 functions recovered, in order.
- Total RTO achieved, total RPO achieved.
- Discrepancies vs. plan.
- Action items for the post-mortem.

## 4. Emergency Mode Operation Plan (§ 164.308(a)(7)(ii)(C))

Emergency mode is the posture the clinic adopts when MedPharm is
unavailable but patients still need care. The objective is to keep
delivering care in a way that protects PHI and preserves an audit
trail that can be reconciled when systems return.

### Trigger

- Any Tier 0–1 function is unavailable for > 30 minutes.
- The Privacy Officer or attending physician declares emergency mode.

### Procedures

| Function | Emergency procedure |
|----------|---------------------|
| **Patient identity** | Photo ID + DOB confirmation; record the verification on the paper intake form. |
| **Allergies** | Ask the patient and any accompanying caregiver. Document on the paper form in red ink. |
| **Active prescriptions** | Patient brings their bottle or pharmacy printout; verify drug name, dose, and prescriber phone-number. |
| **New prescriptions** | Paper Rx pad. Each Rx written is photographed and the photograph filed in the recovery binder. |
| **Allergy & interaction checks** | UpToDate, Lexicomp, or another vetted reference; document the source on the Rx. |
| **Billing** | Paper superbills; reconciled with MedPharm at recovery. |
| **PHI access logging** | Sign-in / sign-out sheet at the chart room; one row per access. |

### Post-recovery reconciliation

When MedPharm is back:

1. Every paper Rx is re-entered into the system, marked as
   "Emergency mode — paper original {date_time}".
2. Every paper superbill is keyed in.
3. The chart-room sign-in sheet is **transcribed into
   `phi_access_log`** with `reason=EMERGENCY` and a note pointing at
   the paper original. This is required to reconstruct an
   accounting of disclosures (§ 164.528).
4. The paper originals are scanned and attached to the patient
   record; the paper goes to long-term storage.
5. A post-mortem documents what worked, what failed, and what
   action items are required.

## 5. Testing & Revision Procedures (§ 164.308(a)(7)(ii)(D))

Cadence:

- **Backup restore** — monthly (see §2).
- **Tabletop disaster-recovery exercise** — quarterly.
- **Full disaster-recovery exercise** — annually, on a non-production
  copy.
- **Emergency-mode drill** — annually, in coordination with clinical
  staff.

Each test is documented with date, participants, what was tested,
what worked, what didn't, and follow-up actions.

## 6. Roles & responsibilities

| Role | Responsibility |
|------|----------------|
| Privacy Officer | Declares disaster / emergency mode; signs off on the post-mortem. |
| Security Officer | Owns the technical recovery procedure; signs off on backup-test results. |
| IT operator | Executes the recovery procedure; maintains the runbook. |
| Office Manager | Coordinates clinical staff during emergency mode. |
| Clinicians | Follow the emergency-mode procedures; provide care continuity. |

## 7. Vendor dependencies

A list of every vendor whose unavailability would block recovery,
with the contact path for the on-call escalation:

| Vendor | Service | Contact (24×7) | BAA in force? |
|--------|---------|----------------|----------------|
| {hosting_provider} | API + Portal hosting | | Yes |
| {dns_provider} | DNS | | Yes / N/A |
| {secret_mgr} | Key management | | Yes |
| {ca} | TLS certificates | | N/A (no PHI) |
| {backup_storage} | Off-site backups | | Yes |
| Docker Hub | Container registry | (community SLA) | N/A (no PHI) |

A vendor failure that blocks recovery is itself a contingency event.
The risk register in `docs/RISK_ANALYSIS_TEMPLATE.md` documents the
control posture against vendor failure.
