# IT Support Portal — MThree Production Support Project

A cloud-deployed IT incident management system. Employees report technical problems; IT staff and admins track them through to resolution.

**Example incident:**

> **Customer Portal Unavailable** | Category: Application | Severity: Critical | Status: Open  
> _"Users are receiving HTTP 503 errors on the main customer-facing portal."_

---

## Tech Stack

| Layer      | Technology                                             |
| ---------- | ------------------------------------------------------ |
| Backend    | Python 3.11, Flask 3.0 (MVC)                           |
| Auth       | Flask-Login + Google OAuth 2.0 (Authlib)               |
| Database   | SQLAlchemy ORM — SQLite (dev/test), MySQL 8 (prod)     |
| Migrations | Flask-Migrate (Alembic)                                |
| Forms      | Flask-WTF + WTForms                                    |
| Frontend   | Jinja2 templates + Bootstrap 5                         |
| REST API   | JSON API under `/api/`                                 |
| Testing    | pytest + pytest-flask                                  |
| Monitoring | Prometheus (`/metrics`) + Grafana dashboard + alerting |
| Deployment | Docker Compose + AWS EC2                               |

---

## Project Structure

```
Mthree_ProdSupport_Project/
├── app/
│   ├── __init__.py              # Application factory
│   ├── config.py                # Dev / Test / Prod config classes
│   ├── extensions.py            # Extension instances (db, login, csrf, oauth)
│   ├── models/                  # SQLAlchemy models  ← M in MVC
│   │   ├── user.py
│   │   ├── category.py
│   │   ├── incident.py
│   │   ├── incident_comment.py
│   │   ├── audit_log.py
│   │   └── user_session.py
│   ├── controllers/             # Flask blueprints   ← C in MVC
│   │   ├── main.py              # Landing page, /health
│   │   ├── auth.py              # Login, register, logout, Google OAuth
│   │   ├── incidents.py         # CRUD for incidents + comments
│   │   ├── admin.py             # Admin-only: dashboard, users, audit log
│   │   └── api.py               # REST API (CSRF-exempt)
│   ├── services/                # Business logic layer
│   │   ├── incident_service.py
│   │   └── audit_service.py
│   ├── forms/                   # Flask-WTF form classes
│   │   ├── auth_forms.py
│   │   └── incident_forms.py
│   ├── templates/               # Jinja2 HTML templates  ← V in MVC
│   └── static/                  # CSS + JS
├── tests/                       # pytest test suite
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_incidents.py
│   ├── test_audit.py
│   └── test_api.py
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
│       ├── provisioning/
│       └── dashboards/it-support.json
├── docker-compose.yml           # App + MySQL + Prometheus + Grafana
├── Dockerfile
├── requirements.txt
├── run.py                       # Dev server
├── wsgi.py                      # Gunicorn entry point
└── setup.cfg                    # pytest config
```

---

## Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- Git

### 1. Set up virtual environment

```bash
cd Mthree_ProdSupport_Project
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
# Windows:
copy .env.example .env
# macOS/Linux:
cp .env.example .env
```

Edit `.env` — at minimum set `SECRET_KEY`. Google OAuth keys are only needed if you want to use the "Continue with Google" button.

### 4. Run the development server

```bash
flask run
# or
python run.py
```

The app starts at **http://localhost:5000**. The database (`dev.db`) and default categories are created automatically on first run.

### 5. Create an admin user

```bash
flask create-admin
```

---

## Running with Docker Compose

Starts Flask app + MySQL 8 + Prometheus + Grafana in one command:

```bash
docker-compose up --build
```

| Service    | URL                   | Credentials   |
| ---------- | --------------------- | ------------- |
| Flask App  | http://localhost:5000 | —             |
| Prometheus | http://localhost:9090 | —             |
| Grafana    | http://localhost:3000 | admin / admin |

---

## Running Tests

```bash
pytest
```

With coverage report:

```bash
pytest --cov=app --cov-report=html
# Then open htmlcov/index.html
```

---

## Database Migrations (Flask-Migrate)

```bash
flask db init          # first time only
flask db migrate -m "description"
flask db upgrade
```

---

## API Reference

All endpoints require an authenticated session. Base path: `/api`

| Method   | Endpoint              | Description                                                                    |
| -------- | --------------------- | ------------------------------------------------------------------------------ |
| `GET`    | `/api/incidents`      | List incidents. Supports `?status=`, `?severity=`, `?category_id=`, `?search=` |
| `POST`   | `/api/incidents`      | Create incident (JSON body)                                                    |
| `GET`    | `/api/incidents/<id>` | Get single incident                                                            |
| `PUT`    | `/api/incidents/<id>` | Update incident                                                                |
| `DELETE` | `/api/incidents/<id>` | Delete incident                                                                |
| `GET`    | `/api/stats`          | Incident counts by status/severity                                             |
| `GET`    | `/api/categories`     | List active categories                                                         |

### Example: Create an incident

```bash
curl -X POST http://localhost:5000/api/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Customer Portal Unavailable",
    "severity": "critical",
    "description": "Users receiving HTTP 503 errors."
  }'
```

---

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. **APIs & Services → Credentials → Create OAuth 2.0 Client ID**
3. Application type: **Web application**
4. Add **Authorized redirect URIs**:
   - `http://localhost:5000/auth/google/callback` (development)
   - `https://your-domain.com/auth/google/callback` (production)
5. Copy **Client ID** and **Client Secret** into your `.env`
6. For local HTTP development, keep `OAUTHLIB_INSECURE_TRANSPORT=1` in `.env`

---

## Monitoring

The app exposes Prometheus metrics at **`/metrics`** (auto-generated by `prometheus-flask-exporter`).

When running via Docker Compose:

- Prometheus scrapes every 15 seconds
- Grafana auto-provisions the **"IT Support Portal"** dashboard

**To add a Grafana alert:**

1. Open Grafana at http://localhost:3000
2. Navigate to the dashboard → click a panel → **Edit**
3. Go to the **Alert** tab
4. Set a condition (e.g., Error Rate > 5% for 5 minutes)
5. Add a notification channel (email, Slack, PagerDuty, etc.)

---

## Database Schema

Matches the ERD in project documentation:

| Table               | Purpose                                                                        |
| ------------------- | ------------------------------------------------------------------------------ |
| `users`             | Registered users with `role` (user/admin) and optional OAuth linkage           |
| `categories`        | Incident categories (seeded on first run)                                      |
| `incidents`         | Core incident records — full lifecycle tracking                                |
| `incident_comments` | Comments/updates on incidents                                                  |
| `audit_log`         | **Immutable** — every CREATE/UPDATE/DELETE with actor + JSON before/after diff |
| `user_sessions`     | Server-side session tokens                                                     |

---

## AWS EC2 Deployment

1. Launch EC2 instance (Ubuntu 22.04 LTS, t3.small or larger)
2. Install Docker & Docker Compose
3. Clone the repo and `cd` into it
4. Create `.env` with production values (`FLASK_ENV=production`, MySQL `DATABASE_URL`, real `SECRET_KEY`, Google OAuth keys)
5. `docker-compose up -d`
6. Configure Security Group: open ports 80, 443, 3000 (Grafana), 9090 (Prometheus)
7. Optional: set up Nginx as reverse proxy for SSL termination

---

## Environment Variables

| Variable                      | Required  | Description                                          |
| ----------------------------- | --------- | ---------------------------------------------------- |
| `SECRET_KEY`                  | **Yes**   | Flask session signing key — use a long random string |
| `DATABASE_URL`                | No        | SQLAlchemy URI (defaults to `sqlite:///dev.db`)      |
| `GOOGLE_CLIENT_ID`            | For OAuth | From Google Cloud Console                            |
| `GOOGLE_CLIENT_SECRET`        | For OAuth | From Google Cloud Console                            |
| `OAUTHLIB_INSECURE_TRANSPORT` | Dev only  | Set `1` to allow HTTP for OAuth locally              |
| `FLASK_ENV`                   | No        | `development` / `testing` / `production`             |
