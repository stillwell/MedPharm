# MedPharm — Server Package (Nginx + API + Web Portal)

Docker definition for the **full-stack** MedPharm server image [`enlightec/medpharm-server`](https://hub.docker.com/r/enlightec/medpharm-server). Base: **Ubuntu 24.04 LTS**.

For operator docs see [`docs/SERVER.md`](../docs/SERVER.md). For installation see [`docs/INSTALLATION.md`](../docs/INSTALLATION.md).

---

## What's inside

| Component | Port | Managed by |
|-----------|-----:|------------|
| Nginx reverse proxy | 80 | supervisord |
| Gunicorn — Cloud API (`api.app:create_app`) | 8080 | supervisord |
| Gunicorn — Web Portal (`web.app:create_app`) | 5000 | supervisord |
| PostgreSQL database (`db` service) | 5432 | volume `medpharm-pgdata` |
| SQLite database (fallback) | — | volume `/data` (used only when `MEDPHARM_DATABASE_URL` is unset) |

---

## File inventory

| File | Purpose |
|------|---------|
| `Dockerfile` | Ubuntu 24.04 image build |
| `docker-compose.yml` | Build-from-source compose |
| `docker-compose.hub.yml` | Pull-from-Hub compose |
| `entrypoint.sh` | DB init + supervisord bootstrap |
| `healthcheck.sh` | `HEALTHCHECK` script |
| `supervisord.conf` | Process definitions |
| `requirements-server.txt` | Combined Python deps |
| `.env.example` | Environment template — **copy to `.env` and edit** |
| `nginx/medpharm.conf` | Reverse proxy routing |

---

## Quick start

### Pre-built image (recommended)

```bash
cp .env.example .env
docker compose -f docker-compose.hub.yml up -d
curl http://localhost/api/v1/health
```

### Build from source

```bash
cp .env.example .env
docker compose up -d --build
```

Stop and destroy (keeps `medpharm-data` volume):

```bash
docker compose down
```

Destroy everything (⚠ data loss):

```bash
docker compose down -v
```

---

## Endpoints (full stack)

| URL | Serves |
|-----|--------|
| `http://localhost/` | Redirects to `/portal/` |
| `http://localhost/api/v1/health` | API health check |
| `http://localhost/api/v1/*` | Cloud REST API |
| `http://localhost/portal/*` | Patient Web Portal |
| `http://localhost:8080/` | API direct (bypasses Nginx) |
| `http://localhost:5000/` | Web portal direct |

---

## Environment

All variables are read from `.env` (Compose loads it automatically). See [`docs/SERVER.md § Environment Variables`](../docs/SERVER.md#environment-variables) for the full list. Critical:

```ini
MEDPHARM_JWT_SECRET=change-me-to-64-random-bytes
MEDPHARM_SECRET_KEY=change-me-to-64-random-bytes
MEDPHARM_CORS_ORIGINS=https://app.example.com
# Shared PostgreSQL backend (default). Comment out MEDPHARM_DATABASE_URL to
# fall back to a private SQLite file.
MEDPHARM_DB_PASSWORD=change-me-to-a-strong-db-password
MEDPHARM_DATABASE_URL=postgresql+psycopg://medpharm:change-me-to-a-strong-db-password@db:5432/medpharm
```

---

## Operations

```bash
docker exec medpharm-server supervisorctl status
docker exec medpharm-server supervisorctl restart medpharm-api
docker exec -it medpharm-db psql -U medpharm -d medpharm          # shared Postgres (default)
docker exec -it medpharm-server sqlite3 /data/medpharm_erp.db     # SQLite fallback (MEDPHARM_DATABASE_URL unset)
docker logs -f medpharm-server
```

For backup, TLS, and hardening, see [`docs/SERVER.md`](../docs/SERVER.md).
