# VIGILANT - AI CCTV Surveillance Intelligence Platform

![Surveillance](https://img.shields.io/badge/System-VIGILANT-15b89a)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite-61DAFB)
![Tailwind](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%2016-336791)
![Argon2id](https://img.shields.io/badge/Password%20Security-Argon2id-critical)
![Docker](https://img.shields.io/badge/Containers-Docker%20Compose-2496ED)

VIGILANT is an enterprise-grade AI-powered CCTV surveillance monitoring intelligence system. It features a security-hardened authentication module, role-based access control (RBAC), forensic audit logging, session management, and a surveillance-themed operations command dashboard.

---

## Architecture Overview

```
                      +----------------------------------+
                      |          React Frontend          |
                      |   (Vite + Tailwind Surveillance) |
                      +-----------------+----------------+
                                        |
                                 HTTPS / REST API
                                        |
                                        v
                      +----------------------------------+
                      |         FastAPI Service          |
                      | (Auth, RBAC, Sessions, Auditing) |
                      +-----------------+----------------+
                                        |
                        +---------------+---------------+
                        |                               |
                        v                               v
         +-----------------------------+ +-----------------------------+
         |          Argon2id           | |             JWT             |
         |     Password Verification   | |   Access & Refresh Tokens   |
         +--------------+--------------+ +--------------+--------------+
                        |                               |
                        +---------------+---------------+
                                        |
                                        v
                      +----------------------------------+
                      |       PostgreSQL Database        |
                      |   Users - Roles - Permissions    |
                      |      Sessions - Audit Logs       |
                      +----------------------------------+
```

---

## Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18 + Vite | Surveillance Login & Dashboard Interface |
| **Styling** | Tailwind CSS | Custom dark surveillance aesthetic matching reference |
| **Backend** | FastAPI | High-performance async REST APIs |
| **Database** | PostgreSQL 16 | Persistent relational database with Docker volume |
| **ORM** | SQLAlchemy 2.0 | Async database operations |
| **Migrations** | Alembic | Version-controlled schema migrations |
| **Validation** | Pydantic v2 | Strict request/response payload validation |
| **Password Security** | Argon2id (`argon2-cffi`) | State-of-the-art password hashing (OWASP standard) |
| **Authentication** | JWT (`PyJWT`) | Dual-token issuance (15m Access + 7d Refresh) |
| **Containerization** | Docker & Docker Compose | Isolated multi-container deployment |

---

## Quick Start with Docker Compose

To build and start all services (PostgreSQL, FastAPI Backend, and React Frontend) with persistent volume storage:

```bash
docker compose up --build
```

### Accessing the System
- **Surveillance Login Web UI:** [http://localhost:5173](http://localhost:5173)
- **FastAPI OpenAPI Interactive Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **System Health Endpoint:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## Initial Default Superadmin Credentials & First-Run Wipeout

On the very first startup:
1. PostgreSQL initializes with the persistent Docker volume (`vigilant_postgres_data`).
2. Alembic executes schema migrations to create all tables (`users`, `roles`, `permissions`, `sessions`, `audit_logs`).
3. The ephemeral bootstrap script (`backend/scripts/seed_first_user.py`) provisions the default administrator:
   - **Username / Email:** `cctv@gmail.com`
   - **Password:** `123456789`
   - **Assigned Role:** `SUPERADMIN`
4. **Self-Wipeout:** The seed script immediately overwrites and deletes itself (`rm -f /app/scripts/seed_first_user.py`).
5. On subsequent runs (`docker compose down` and `docker compose up`), the database volume retains the user without re-running or duplicating the seed process, and no plaintext credentials remain on disk.

---

## Standalone Development Setup (Without Docker)

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start ASGI Server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Running Backend Tests
```bash
$env:PYTHONPATH="backend"
pytest backend/tests
```

All 10 unit and integration tests covering password hashing, JWT expiration, authentication APIs, and seeding idempotency will run.

---

## Directory Structure

```
VIGILANT/
├── docs/
│   ├── vigilant-auth-design.md     # Approved technical architecture spec
│   ├── vigilant-auth-plan.md       # Implementation task plan
│   └── DECISIONS.md                # Architecture Decision Records (ADRs)
├── docker-compose.yml              # Multi-container orchestration
├── .env.example                    # Environment configuration template
├── backend/
│   ├── Dockerfile                  # Production Python 3.12 container
│   ├── entrypoint.sh               # Migration, seed execution & auto-wipeout
│   ├── requirements.txt            # Python dependencies
│   ├── alembic/                    # Schema migrations
│   ├── scripts/
│   │   └── seed_first_user.py      # Ephemeral bootstrap seed script
│   ├── app/
│   │   ├── core/                   # Security (Argon2id, JWT) & Config
│   │   ├── db/                     # Async session & Base
│   │   ├── models/                 # SQLAlchemy 2.0 ORM models
│   │   ├── schemas/                # Pydantic v2 schemas
│   │   ├── services/               # AuthService & AuditService
│   │   └── api/                    # REST routers & endpoints
│   └── tests/                      # Automated pytest suite
└── frontend/
    ├── Dockerfile                  # Production container
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    └── src/
        ├── assets/                 # CCTV Camera high-res assets
        ├── components/             # BrandLogo, ProtectedRoute
        ├── context/                # AuthContext & token management
        ├── services/               # Axios API client with refresh interceptor
        ├── pages/
        │   ├── Login.tsx           # Faithfully recreated from Reference 1
        │   └── Dashboard.tsx       # Surveillance Command Center (Empty State)
        ├── App.tsx
        └── main.tsx
```
