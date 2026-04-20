# MedPharm ERP — Server Guide

Operator documentation for the MedPharm server stack: Cloud REST API, Flask Web Portal, Nginx reverse proxy, Supervisor process manager, and the SQLite datastore.

---

## Table of Contents

1. [Stack Overview](#stack-overview)
2. [Deployment Topologies](#deployment-topologies)
3. [Process Manager (Supervisor)](#process-manager-supervisor)
4. [Nginx Reverse Proxy](#nginx-reverse-proxy)
5. [Environment Variables](#environment-variables)
6. [TLS / HTTPS](#tls--https)
7. [Logging & Observability](#logging--observability)
8. [Backup & Restore](#backup--restore)
9. [Upgrades](#upgrades)
10. [Hardening Checklist](#hardening-checklist)
11. [Operational Runbook](#operational-runbook)

---

## Stack Overview

```
                 ┌─────────────────── Nginx ────────────────────┐
Internet ──►    │  :80 / :443                                   │
                │  ├── /api/v1/*  ──► Gunicorn : 8080 (API)    │
                │  └── /portal/*  ──► Gunicorn : 5000 (Web)    │
                └───────────────────────────────────────────────┘
                                   │
                              ┌────┴────┐
                              │ SQLite  │ /data/medpharm_erp.db
                              └─────────┘
```

All three processes (Nginx, Gunicorn API, Gunicorn Web) are supervised by **supervisord** inside the `enlightec/medpharm-server` container. Logs stream to stdout and to `/var/log/medpharm/`.

---

## Deployment Topologies

### 1. Single-node Docker (recommended)

```bash
cd server
cp .env.example .env          # edit secrets
docker compose -f docker-compose.hub.yml up -d
```

One host, one container, one SQLite volume. Suitable for small practices (< 50 concurrent users).

### 2. API + Portal behind an external reverse proxy

Use `enlightec/medpharm-api` and run the Web Portal separately:

```bash
docker run -d --name api -p 8080:8080 -v medpharm-data:/data enlightec/medpharm-api:latest
python3 run_web.py                 # on the same host, different port
```

Point your existing Nginx / Caddy / Traefik at `http://127.0.0.1:8080` and `http://127.0.0.1:5000`.

### 3. Horizontal scale (read-replicas)

SQLite is single-writer. For larger installations migrate the DB to PostgreSQL by changing the `DATABASE_URL` in `DatabaseManager.__init__` (SQLAlchemy handles the driver swap) and run the API behind a load balancer with `N` workers.

### 4. Bare-metal systemd (no Docker)

```ini
# /etc/systemd/system/medpharm-api.service
[Unit]
Description=MedPharm Cloud API
After=network.target

[Service]
User=medpharm
WorkingDirectory=/opt/medpharm
EnvironmentFile=/etc/medpharm/api.env
ExecStart=/opt/medpharm/venv/bin/gunicorn -w 4 -b 0.0.0.0:8080 'api.app:create_app()'
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now medpharm-api
```

---

## Process Manager (Supervisor)

Configuration: [`server/supervisord.conf`](../server/supervisord.conf).

| Program | Command | Auto-restart | Log |
|---------|---------|--------------|-----|
| `nginx` | `nginx -g 'daemon off;'` | yes | `/var/log/medpharm/nginx.log` |
| `medpharm-api` | `gunicorn -w 4 -b 0.0.0.0:8080 'api.app:create_app()'` | yes | `/var/log/medpharm/api.log` |
| `medpharm-web` | `gunicorn -w 2 -b 0.0.0.0:5000 'web.app:create_app()'` | yes | `/var/log/medpharm/web.log` |

Manage from outside the container:

```bash
docker exec medpharm-server supervisorctl status
docker exec medpharm-server supervisorctl restart medpharm-api
```

---

## Nginx Reverse Proxy

The bundled config is at [`server/nginx/medpharm.conf`](../server/nginx/medpharm.conf). Key routes:

```nginx
location /api/v1/   { proxy_pass http://127.0.0.1:8080; }
location /portal/   { proxy_pass http://127.0.0.1:5000; }
location /          { return 301 /portal/; }
```

Customisations:

* **TLS termination** — mount certs into `/etc/nginx/certs` and uncomment the TLS `server` block.
* **Client max body size** — add `client_max_body_size 25m;` if uploading scan attachments.
* **Rate limiting** — add `limit_req_zone $binary_remote_addr zone=medpharm:10m rate=20r/s;` at the `http` block.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MEDPHARM_DB_PATH` | `medpharm_erp.db` | SQLite path |
| `MEDPHARM_SECRET_KEY` | auto-generated | Flask session secret |
| `MEDPHARM_JWT_SECRET` | dev default | **Override in production** |
| `MEDPHARM_TOKEN_EXPIRY` | `86400` | Access token seconds |
| `MEDPHARM_REFRESH_EXPIRY` | `604800` | Refresh token seconds |
| `MEDPHARM_CORS_ORIGINS` | `*` | Comma-separated list |
| `MEDPHARM_HOST` | `0.0.0.0` | Bind host |
| `MEDPHARM_PORT` | `8080` | API port |
| `MEDPHARM_DEBUG` | `false` | Flask debug |
| `MEDPHARM_HTTP_PORT` | `80` | Nginx port |
| `MEDPHARM_API_PORT` | `8080` | Gunicorn API port |
| `MEDPHARM_WEB_PORT` | `5000` | Gunicorn Web port |
| `MEDPHARM_WORKERS` | `4` | Gunicorn workers |
| `MEDPHARM_THREADS` | `2` | Gunicorn threads/worker |

Copy `server/.env.example` → `server/.env` and edit for production. Never commit `.env`.

---

## TLS / HTTPS

Use Let's Encrypt via the `certbot` sidecar pattern or Caddy in front of the container.

**Caddy one-liner front end:**

```caddyfile
medpharm.example.com {
  reverse_proxy /api/v1/* 127.0.0.1:8080
  reverse_proxy /portal/* 127.0.0.1:5000
}
```

Caddy auto-provisions and renews certificates.

---

## Logging & Observability

| Stream | Location |
|--------|----------|
| Gunicorn access log | stdout (container) / `/var/log/medpharm/api.log` |
| Gunicorn error log | stderr (container) |
| Nginx access log | `/var/log/medpharm/nginx-access.log` |
| Audit log (DB) | `audit_logs` table — queryable via SQL |

Structured log forwarding: add a `logging` sidecar (Vector, Filebeat, Fluent Bit) or set Docker's `--log-driver=json-file` and scrape via Loki / ELK.

Health check:

```bash
curl -fsS http://localhost:8080/api/v1/health
```

Health endpoint returns `{"status":"ok"}` with HTTP 200. Docker's `HEALTHCHECK` invokes [`server/healthcheck.sh`](../server/healthcheck.sh).

---

## Backup & Restore

### SQLite hot backup

```bash
docker exec medpharm-server sqlite3 /data/medpharm_erp.db ".backup '/data/backup-$(date +%F).db'"
docker cp medpharm-server:/data/backup-$(date +%F).db ./backups/
```

Schedule via cron:

```cron
15 2 * * * docker exec medpharm-server sqlite3 /data/medpharm_erp.db ".backup '/data/backup-$(date +\%F).db'"
```

### Restore

```bash
docker compose down
docker run --rm -v medpharm-data:/data -v $PWD/backups:/backup alpine \
  cp /backup/backup-2026-04-10.db /data/medpharm_erp.db
docker compose up -d
```

Retain at least **7 daily** and **4 weekly** backups. Encrypt off-site copies with `age` or GPG.

---

## Upgrades

```bash
docker compose -f docker-compose.hub.yml pull
docker compose -f docker-compose.hub.yml up -d
docker image prune -f
```

Schema changes are applied automatically by `DatabaseManager.init_db()` on container start via `CREATE TABLE IF NOT EXISTS`. Destructive migrations (column drops) will require manual SQL — check the `CHANGELOG` before upgrading between major versions.

**Rollback:**

```bash
docker pull enlightec/medpharm-server:1.5.1     # previous tag
MEDPHARM_TAG=1.5.1 docker compose up -d
```

---

## Hardening Checklist

* [ ] Set `MEDPHARM_JWT_SECRET` and `MEDPHARM_SECRET_KEY` to random 64-byte values (`openssl rand -base64 48`).
* [ ] Change all default passwords listed in [README.md](../README.md#default-credentials).
* [ ] Restrict `MEDPHARM_CORS_ORIGINS` to known client origins — do not leave `*` in production.
* [ ] Terminate TLS at Nginx or an external proxy.
* [ ] Run the container as a non-root user (default: `medpharm` UID 1000).
* [ ] Mount `/data` with restricted permissions (`0700`, owned by the `medpharm` user).
* [ ] Enable automatic security updates on the host.
* [ ] Forward audit logs off-host (ship `audit_logs` table entries to SIEM).
* [ ] Review role-based access: Doctor, Psychiatrist, Pharmacist, Admin, Patient.
* [ ] Rotate staff passwords at least every 90 days.

---

## Operational Runbook

| Event | Command |
|-------|---------|
| Check services | `docker exec medpharm-server supervisorctl status` |
| Tail API logs | `docker logs -f medpharm-server` |
| Restart API only | `docker exec medpharm-server supervisorctl restart medpharm-api` |
| Open SQL shell | `docker exec -it medpharm-server sqlite3 /data/medpharm_erp.db` |
| Reset admin password | `UPDATE users SET password_hash = '<werkzeug_hash>' WHERE username='admin';` |
| Force token rotation | Change `MEDPHARM_JWT_SECRET`, restart API — all existing tokens invalidate. |
| Enable debug temporarily | `MEDPHARM_DEBUG=true docker compose up -d`, then revert. |
| Drain & stop | `docker compose -f docker-compose.hub.yml stop` |
| Full wipe (danger) | `docker compose down -v` (destroys `medpharm-data`). |
