# MedPharm ERP — REST API Reference

Base URL: `http://<host>:8080/api/v1` (or `https://<host>/api/v1` behind TLS).

All endpoints return JSON. All authenticated endpoints require an `Authorization: Bearer <token>` header.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Conventions](#conventions)
3. [Endpoint Reference](#endpoint-reference)
4. [Error Format](#error-format)
5. [Rate Limiting & CORS](#rate-limiting--cors)
6. [Versioning](#versioning)
7. [Worked Examples](#worked-examples)

---

## Authentication

MedPharm uses **JWT (HMAC-SHA256)** access + refresh tokens.

| Endpoint | Returns |
|----------|---------|
| `POST /auth/login/patient` | `{ access_token, refresh_token, patient }` |
| `POST /auth/login/staff`   | `{ access_token, refresh_token, user }` |
| `POST /auth/refresh`       | `{ access_token }` |
| `POST /auth/register`      | `{ patient_id }` (patient self-registration, 4-factor verification) |

Default lifetimes (override via env): access = **24h**, refresh = **7 days**. Signing secret is `MEDPHARM_JWT_SECRET`.

Attach the access token to every subsequent request:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Conventions

| Aspect | Value |
|--------|-------|
| Content type | `application/json; charset=utf-8` |
| Timestamps | ISO-8601, UTC (`2026-04-18T12:34:56Z`) |
| IDs | Integer, monotonically assigned |
| Pagination | `?limit=<n>&offset=<m>` where supported |
| Search | `?search=<term>` case-insensitive |
| Filtering | Query params per endpoint (`?status=active`) |

HTTP method semantics:

| Method | Meaning |
|--------|---------|
| `GET` | Read |
| `POST` | Create / action |
| `PUT` | Replace / update |
| `DELETE` | Remove |

---

## Endpoint Reference

### Public

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/health` | Liveness probe — returns `{"status":"ok"}` |
| `POST` | `/auth/login/patient` | Patient login (username + password) |
| `POST` | `/auth/login/staff` | Staff login (username + password) |
| `POST` | `/auth/refresh` | Exchange a refresh token for a new access token |
| `POST` | `/auth/register` | Patient registration (4-factor verification) |

### Patient (`role = patient`)

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/patient/dashboard` | KPI summary: active Rx, upcoming appts, open invoices |
| `GET`  | `/patient/profile` | Demographics, insurance, allergies |
| `PUT`  | `/patient/profile` | Update contact info |
| `GET`  | `/patient/prescriptions` | All prescriptions (filter via `?status=`) |
| `GET`  | `/patient/prescriptions/<id>` | Prescription detail + line items |
| `POST` | `/patient/prescriptions/<id>/refill` | Request refill |
| `GET`  | `/patient/billing` | Invoice list |
| `GET`  | `/patient/billing/<id>` | Invoice detail |
| `POST` | `/patient/billing/<id>/pay` | Submit payment (`method`, `amount`, card/ACH fields) |
| `GET`  | `/patient/records` | Records (filter via `?type=`) |
| `GET`  | `/patient/appointments` | Upcoming + past appointments |
| `GET`  | `/patient/medications` | Current medications |
| `GET`  | `/patient/notifications` | Unread portal notifications |
| `GET`  | `/patient/insurance` | Patient's insurance records |
| `GET`  | `/patient/insurance/claims` | Claim list |
| `POST` | `/patient/insurance/claims` | File a new claim (`invoice_id`, `insurance_id`) |

### Staff (`role in {doctor, psychiatrist, pharmacist, admin}`)

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/staff/dashboard` | KPIs + today's appointments |
| `GET`  | `/staff/patients` | Patient list (search, pagination) |
| `GET`  | `/staff/patients/<id>` | Patient detail |
| `GET`  | `/staff/appointments` | Filter by date, status |
| `GET`  | `/staff/prescriptions` | All prescriptions |
| `GET`  | `/staff/analytics/revenue` | Monthly revenue series |
| `GET`  | `/staff/analytics/top-medications` | Top prescribed meds |
| `GET`  | `/staff/analytics/demographics` | Patient age / gender breakdown |
| `GET`  | `/staff/insurance/claims` | All insurance claims |
| `POST` | `/staff/insurance/claims/<id>/process` | Approve / deny / pay claim |

### Reference (authenticated, any role)

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/medications/search?q=<term>` | Search catalog (name / class / schedule) |
| `GET`  | `/medications/<id>` | Medication detail |
| `GET`  | `/reference/symptoms` | Symptom list (filter `?body_system=`) |
| `GET`  | `/reference/symptoms/body-systems` | List body systems |
| `GET`  | `/reference/conditions` | Condition list (filter `?category=`) |
| `GET`  | `/reference/conditions/categories` | List condition categories |

---

## Error Format

```json
{
  "error": "invalid_credentials",
  "message": "Username or password is incorrect."
}
```

| HTTP | Error code | Meaning |
|------|-----------|---------|
| 400 | `bad_request` | Malformed JSON or missing field |
| 401 | `unauthorized` | Missing / invalid token |
| 401 | `invalid_credentials` | Login failed |
| 403 | `forbidden` | Wrong role for endpoint |
| 404 | `not_found` | Resource does not exist |
| 409 | `conflict` | Duplicate (e.g. username taken) |
| 422 | `validation_error` | Field-level validation failed |
| 500 | `server_error` | Unhandled exception |

---

## Rate Limiting & CORS

* **Rate limiting** is not enforced at the application layer — apply it at the reverse proxy (see [SERVER.md](SERVER.md#nginx-reverse-proxy)).
* **CORS** is controlled by `MEDPHARM_CORS_ORIGINS`. Set a comma-separated list of exact origins in production (`https://app.example.com`).

---

## Versioning

The API is mounted at `/api/v1`. Breaking changes will increment the path segment to `/api/v2`. Non-breaking additions (new fields, new endpoints) are made in place. Clients should ignore unknown fields.

---

## Worked Examples

### Patient login + dashboard

```bash
TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/login/patient \
  -H 'Content-Type: application/json' \
  -d '{"username":"jsmith_portal","password":"patient123"}' | jq -r .access_token)

curl -s http://localhost:8080/api/v1/patient/dashboard \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Submit an invoice payment

```bash
curl -s -X POST http://localhost:8080/api/v1/patient/billing/42/pay \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"method":"credit_card","amount":120.50,"card_last4":"4242"}' | jq .
```

### File an insurance claim

```bash
curl -s -X POST http://localhost:8080/api/v1/patient/insurance/claims \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"invoice_id":42,"insurance_id":7}' | jq .
```

### Staff — approve a claim

```bash
STAFF_TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/login/staff \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | jq -r .access_token)

curl -s -X POST http://localhost:8080/api/v1/staff/insurance/claims/15/process \
  -H "Authorization: Bearer $STAFF_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"action":"approve","approved_amount":120.50,"notes":"Within policy limit"}' | jq .
```

### Search medications

```bash
curl -s "http://localhost:8080/api/v1/medications/search?q=lisinopril" \
  -H "Authorization: Bearer $TOKEN" | jq '.medications[:3]'
```

### Refresh an expired access token

```bash
curl -s -X POST http://localhost:8080/api/v1/auth/refresh \
  -H 'Content-Type: application/json' \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}" | jq .
```
