# MedPharm — Flask Web Portal (Patients)

Server-rendered Flask + Jinja2 portal for patient self-service. Distributed both as a standalone Python app (`run_web.py`) and inside the full-stack Docker image.

Feature inventory: [`docs/CLIENTS.md § Flask Web Portal`](../docs/CLIENTS.md#flask-web-portal-patients).

---

## Module layout

```
web/
├── app.py              # Flask application factory, session config, blueprint mount
├── routes.py           # All route handlers — login, register, dashboard, billing, ...
├── static/
│   ├── css/style.css   # Dark theme portal stylesheet
│   └── js/app.js       # Client-side interactions
└── templates/          # 14 Jinja2 templates
```

---

## Run

Development:

```bash
../start_web.sh              # port 5000
../start_web.sh 8000         # custom port
# or
source ../venv/bin/activate
python3 ../run_web.py
```

Production (Gunicorn):

```bash
gunicorn -w 2 -b 0.0.0.0:5000 'web.app:create_app()'
```

Served behind Nginx in the full-stack Docker image at `http://<host>/portal/`.

---

## Route index

| Route | Purpose |
|-------|---------|
| `GET /login` / `POST /login` | Session login |
| `GET /register` / `POST /register` | 4-factor identity verification + account creation |
| `GET /logout` | Destroy session |
| `GET /dashboard` | Summary (active Rx, upcoming appts, invoices) |
| `GET /prescriptions[/<id>]` | Rx list / detail |
| `POST /prescriptions/<id>/refill` | Refill request |
| `GET /billing[/<id>]` | Invoice list / detail |
| `POST /billing/<id>/pay` | Submit payment |
| `GET /records` | Records list |
| `GET /appointments` | Appointment history |
| `GET /medications` | Current medications |
| `GET /profile` / `POST /profile` | Update contact + insurance |

---

## Authentication model

* Server-side Flask sessions signed with `MEDPHARM_SECRET_KEY`
* CSRF tokens on every POST form
* PBKDF2-SHA256 password hashing via Werkzeug

---

## 4-factor patient registration

A patient record must already exist in the database. The registration flow matches:

1. First name
2. Last name
3. Date of birth
4. Last 4 digits of SSN

Only on an exact match is the patient allowed to pick a username and password. This mirrors the security posture of external patient portals (e.g. Athena, Epic MyChart) at small practices.

---

## Requirements

From [`../requirements.txt`](../requirements.txt):

* Flask ≥ 3.0
* SQLAlchemy ≥ 2.0
* Werkzeug ≥ 3.0
