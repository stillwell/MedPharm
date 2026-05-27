# MedPharm ERP — Server Guide

Operator documentation for the MedPharm server stack: Cloud REST API, Flask Web Portal, Nginx reverse proxy, Supervisor process manager, and the datastore (shared PostgreSQL by default, single-file SQLite when `MEDPHARM_DATABASE_URL` is unset).

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
                              ┌────┴─────┐
                              │ Database │  PostgreSQL  (MEDPHARM_DATABASE_URL, default)
                              └──────────┘  or SQLite   /data/medpharm_erp.db (URL unset)
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

One host, one container. Compose brings up a bundled PostgreSQL `db` service by default (the `medpharm-pgdata` volume); comment out `MEDPHARM_DATABASE_URL` to fall back to a single SQLite volume. Suitable for small practices (< 50 concurrent users).

### 2. API + Portal behind an external reverse proxy

Use `enlightec/medpharm-api` and run the Web Portal separately:

```bash
docker run -d --name api -p 8080:8080 -v medpharm-data:/data enlightec/medpharm-api:latest
python3 run_web.py                 # on the same host, different port
```

Point your existing Nginx / Caddy / Traefik at `http://127.0.0.1:8080` and `http://127.0.0.1:5000`.

### 3. Horizontal scale (shared database)

SQLite is single-writer. For larger installations point every component at a shared PostgreSQL by setting the `MEDPHARM_DATABASE_URL` env var (e.g. `postgresql+psycopg://medpharm:PASS@host:5432/medpharm`) — no code change; `DatabaseManager` reads it at startup and SQLAlchemy handles the driver. With the database shared, run the API behind a load balancer with `N` workers (or, on k8s, multiple replicas).

### 4. Kubernetes (GKE, EKS, Linode, bare-metal)

```bash
kubectl create namespace medpharm
kubectl -n medpharm create secret generic medpharm-secrets \
  --from-literal=MEDPHARM_JWT_SECRET="$(openssl rand -base64 48)" \
  --from-literal=MEDPHARM_SECRET_KEY="$(openssl rand -base64 48)"
kubectl apply -k k8s/overlays/gcp        # or aws / generic
```

Kustomize bases + cloud overlays live in `k8s/`. Full walkthrough, including
GKE ManagedCertificate and EKS ALB setup, is in [KUBERNETES.md](KUBERNETES.md).

### 5. Bare-metal systemd (no Docker)

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

The server image ships two Nginx configs:

* [`server/nginx/medpharm-tls.conf`](../server/nginx/medpharm-tls.conf) — **default.** Listens on 443 with TLSv1.2+, redirects port 80 to 443, applies HSTS, login rate-limiting, and structured JSON access logs.
* [`server/nginx/medpharm.conf`](../server/nginx/medpharm.conf) — plaintext fallback on port 80 (enabled only when `MEDPHARM_TLS_MODE=disable`).

Key routes (TLS config):

```nginx
location /api/    { proxy_pass http://medpharm_api; }     # 127.0.0.1:8080
location /portal/ { proxy_pass http://medpharm_web/; }    # 127.0.0.1:5000
location = /      { proxy_pass http://medpharm_api; }
```

Customisations:

* **Cert override** — mount a CA-issued `fullchain.pem` + `privkey.pem` at `/etc/ssl/medpharm/` (Docker volume `medpharm-tls`) and set `MEDPHARM_TLS_MODE=require` to fail fast if the mount is missing.
* **Client max body size** — already set to 25M (document uploads). Override per `location` if needed.
* **Rate limiting** — `limit_req_zone ... zone=login:10m rate=5r/m` is pre-wired at the `http{}` context; apply with `limit_req zone=login burst=10 nodelay;` in any new `location` block.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MEDPHARM_DATABASE_URL` | _(unset)_ | Full SQLAlchemy URL for the shared database (e.g. `postgresql+psycopg://medpharm:PASS@host:5432/medpharm`). Set = every component shares one DB; unset = private SQLite at `MEDPHARM_DB_PATH`. |
| `MEDPHARM_DB_PASSWORD` | `change-this-in-production` | Postgres superuser password for the Compose `db` service (embedded in `MEDPHARM_DATABASE_URL`). |
| `MEDPHARM_DB_PATH` | `medpharm_erp.db` | SQLite path (used only when `MEDPHARM_DATABASE_URL` is unset) |
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
| `MEDPHARM_HTTPS_PORT` | `443` | Nginx TLS listen port |
| `MEDPHARM_TLS_MODE` | `auto` | `auto` \| `require` \| `disable` |
| `MEDPHARM_TLS_DIR` | `/etc/ssl/medpharm` | Cert directory (`fullchain.pem`, `privkey.pem`) |
| `MEDPHARM_TLS_HOSTNAME` | `localhost` | CN/SAN for self-signed generation |
| `MEDPHARM_TLS_DAYS` | `825` | Validity for auto-generated certs |

Copy `server/.env.example` → `server/.env` and edit for production. Never commit `.env`.

---

## TLS / HTTPS

**TLS is on by default** in every install path. On first boot the container auto-generates a self-signed RSA-4096 cert into `/etc/ssl/medpharm/` (persisted via the `medpharm-tls` Docker volume) and serves HTTPS on port 443. HTTP on port 80 returns 301 to HTTPS.

### Self-signed (development / staging)

Nothing to do — just `docker compose up -d`. The log banner announces `TLS ... port 443`. Verify with:

```bash
curl -sk https://localhost/api/v1/health | jq .
curl -sI http://localhost/api/v1/health | head -1   # expect: HTTP/1.1 301 Moved Permanently
```

### CA-issued certs (production)

Drop `fullchain.pem` and `privkey.pem` onto the host and mount them into the container:

```bash
docker compose -f server/docker-compose.hub.yml down
docker volume rm medpharm_medpharm-tls            # or edit the mount
docker run --rm -v "$PWD/tls:/src" -v medpharm-tls:/dst alpine \
    sh -c 'cp /src/fullchain.pem /src/privkey.pem /dst/ && chmod 600 /dst/privkey.pem'
MEDPHARM_TLS_MODE=require docker compose -f server/docker-compose.hub.yml up -d
```

### Let's Encrypt

Use `certbot` with the `/var/www/certbot` webroot (already wired in `medpharm-tls.conf`):

```bash
docker run --rm -v medpharm-tls:/etc/letsencrypt \
    -v /var/www/certbot:/var/www/certbot certbot/certbot certonly \
    --webroot -w /var/www/certbot -d medpharm.example.com
```

### Caddy alternative

Terminate TLS at Caddy in front of a container running with `MEDPHARM_TLS_MODE=disable`:

```caddyfile
medpharm.example.com {
  reverse_proxy 127.0.0.1:80
}
```

Caddy auto-provisions and renews certificates. Acceptable only if the hop from Caddy to MedPharm is on a trusted network segment (same host loopback, private VPC, etc.) — otherwise keep TLS on at both legs.

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
curl -fsSk https://localhost/api/v1/health
```

Health endpoint returns `{"status":"ok"}` with HTTP 200. Docker's `HEALTHCHECK` invokes [`server/healthcheck.sh`](../server/healthcheck.sh), which tries HTTPS first (`-k` for self-signed) and falls back to HTTP for the `MEDPHARM_TLS_MODE=disable` variant.

---

## Backup & Restore

Back up whichever backend is live. With the default Compose stack the authoritative store is the PostgreSQL `db` service; only use the SQLite commands when `MEDPHARM_DATABASE_URL` is unset.

### PostgreSQL backup (default stack)

```bash
docker exec medpharm-db pg_dump -U medpharm -Fc medpharm > "./backups/medpharm-$(date +%F).dump"
```

Schedule via cron:

```cron
15 2 * * * docker exec medpharm-db pg_dump -U medpharm -Fc medpharm > "/srv/medpharm/backups/medpharm-$(date +\%F).dump"
```

Restore into a running `db` service:

```bash
docker exec -i medpharm-db pg_restore -U medpharm -d medpharm --clean --if-exists < ./backups/medpharm-2026-04-10.dump
```

### SQLite hot backup (when `MEDPHARM_DATABASE_URL` is unset)

```bash
docker exec medpharm-server sqlite3 /data/medpharm_erp.db ".backup '/data/backup-$(date +%F).db'"
docker cp medpharm-server:/data/backup-$(date +%F).db ./backups/
```

Schedule via cron:

```cron
15 2 * * * docker exec medpharm-server sqlite3 /data/medpharm_erp.db ".backup '/data/backup-$(date +\%F).db'"
```

SQLite restore:

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

Schema changes are applied automatically by `DatabaseManager.init_db()` on container start via `CREATE TABLE IF NOT EXISTS` (against whichever backend `MEDPHARM_DATABASE_URL` selects — PostgreSQL or SQLite). Destructive migrations (column drops) will require manual SQL — check the `CHANGELOG` before upgrading between major versions.

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
| Open SQL shell (Postgres) | `docker exec -it medpharm-db psql -U medpharm -d medpharm` |
| Open SQL shell (SQLite) | `docker exec -it medpharm-server sqlite3 /data/medpharm_erp.db` (only when `MEDPHARM_DATABASE_URL` is unset) |
| Reset admin password | `UPDATE users SET password_hash = '<werkzeug_hash>' WHERE username='admin';` |
| Force token rotation | Change `MEDPHARM_JWT_SECRET`, restart API — all existing tokens invalidate. |
| Enable debug temporarily | `MEDPHARM_DEBUG=true docker compose up -d`, then revert. |
| Drain & stop | `docker compose -f docker-compose.hub.yml stop` |
| Full wipe (danger) | `docker compose down -v` (destroys `medpharm-data`). |
