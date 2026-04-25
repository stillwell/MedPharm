# MedPharm — Cloud REST API

Flask application factory exposing the `/api/v1/*` endpoints consumed by the mobile (Android, iOS) and desktop (macOS, Windows) clients.

For the full endpoint reference see [`docs/API.md`](../docs/API.md).

---

## Module layout

| File | Responsibility |
|------|----------------|
| `app.py` | Flask application factory (`create_app()`), CORS, blueprint registration, JSON error handlers |
| `auth.py` | JWT encode/decode (HMAC-SHA256), `@token_required`, `@patient_required`, `@staff_required`, `@admin_required` decorators |
| `fhir.py` | Read-only FHIR R4 façade exposing `Patient`, `MedicationRequest`, `Observation`, etc. for interop |
| `routes.py` | All REST handlers under the `api_bp` blueprint |

`create_app()` consumes the environment variables listed in [`docs/SERVER.md`](../docs/SERVER.md#environment-variables).

---

## Run locally

```bash
source ../venv/bin/activate
python3 ../run_cloud.py                   # dev mode (Flask's built-in server)
```

Or with Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:8080 'api.app:create_app()'
```

Health check:

```bash
curl -fsS http://localhost:8080/api/v1/health
```

---

## Dependencies

Defined in [`../requirements-cloud.txt`](../requirements-cloud.txt):

* Flask ≥ 3.0
* flask-cors ≥ 4.0
* SQLAlchemy ≥ 2.0
* Werkzeug ≥ 3.0
* gunicorn ≥ 21.2

---

## Testing an endpoint

```bash
TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/login/staff \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | jq -r .access_token)

curl -s http://localhost:8080/api/v1/staff/dashboard \
  -H "Authorization: Bearer $TOKEN" | jq .
```

---

## Adding a new endpoint

1. Add the handler to `api/routes.py` under the `api_bp` blueprint.
2. Decorate it with `@token_required` (any authenticated user), `@patient_required`, `@staff_required`, or `@admin_required` as appropriate. Within the handler, identity is read from `g.current_user_type`, `g.current_user_id`, `g.current_patient_id`, and `g.current_role`.
3. Use `DatabaseManager` (from `database/db_manager.py`) for all data access via `g.db_manager` — never hit SQLAlchemy directly inside a handler.
4. Return `jsonify(...)` with explicit HTTP status codes.
5. Document it in `docs/API.md`.
