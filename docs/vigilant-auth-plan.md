# VIGILANT Authentication & Initial Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete authentication system, PostgreSQL database with RBAC/sessions/audit logs, self-wiping first-run seed mechanism, Docker Compose orchestration, and surveillance-themed login page matching Reference 1 with an empty command dashboard.

**Architecture:** A containerized multi-tier architecture with React + Vite + Tailwind CSS frontend communicating via REST with a FastAPI authentication service. Passwords secured using Argon2id, tokens issued as dual JWTs (Access + sliding Refresh), and data persisted in PostgreSQL 16 with persistent volume and ephemeral startup seeding that deletes its own script after initial provision.

**Tech Stack:** React 19, Vite, Tailwind CSS, Lucide React, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, Argon2id (`argon2-cffi`), PyJWT, PostgreSQL 16, Docker & Docker Compose.

**Spec:** [docs/vigilant-auth-design.md](file:///c:/Users/logit/Downloads/VIGILANT/docs/vigilant-auth-design.md)

## Global Constraints
- Target platform: Windows host with Docker Desktop / WSL2 containerization.
- Default Super Admin credentials: `cctv@gmail.com` / `123456789`.
- Seeding idempotency: If user exists, do not recreate or throw error.
- Credential wipeout: Seed script `seed_first_user.py` must be permanently deleted from disk immediately after initial creation.
- Login UI fidelity: Camera hero visual on left, dark teal ambiance, floating rounded glassmorphic card on right, "Sign in" header, Username and Password inputs with show/hide toggle, "Forgot Password?", "Login" button, and "Don't have an Account? Sign up" toggle. No social logins.
- Surveillance Dashboard: Real-time telemetry badges, empty camera feed grid placeholder, user badge, and logout.

## Review Focus
1. Password hashing failure with legacy formats or weak inputs: Verify Argon2id validates correct password and rejects invalid passwords with 401.
2. Token expiration and refresh handling: Verify access token expiration returns 401 and refresh token can issue new access token.
3. Seeding idempotency: Verify repeated runs of seed logic do not throw unique constraint violations or duplicate users.
4. Ephemeral script self-wipeout: Verify the seed script is absent from disk after container startup.
5. Responsive login card and camera layout: Verify UI renders seamlessly without horizontal scroll or broken layout.

---

### Task 1: Project Scaffolding & Root Configuration
**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `.agent/progress.md`

- [ ] Create root `.gitignore` ignoring `node_modules`, `dist`, `__pycache__`, `.venv`, `.env`, `*.pyc`, `postgres_data`.
- [ ] Create `.env.example` defining database credentials, JWT secret, and ports.
- [ ] Initialize `.agent/progress.md` tracking development progress.
- [ ] Commit changes to git.

---

### Task 2: Backend Dependencies & Database Engine Setup
**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/core/config.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/db/base.py`

- [ ] Define dependencies in `backend/requirements.txt` (`fastapi`, `uvicorn`, `sqlalchemy>=2.0`, `asyncpg`, `psycopg[binary]`, `alembic`, `pydantic>=2.0`, `pydantic-settings`, `argon2-cffi`, `pyjwt`, `python-multipart`, `pytest`, `pytest-asyncio`, `httpx`).
- [ ] Implement `app/core/config.py` with `Settings` class loading environment variables for `DATABASE_URL`, `JWT_SECRET`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, etc.
- [ ] Implement `app/db/session.py` with async engine and `async_sessionmaker`.
- [ ] Implement `app/db/base.py` with declarative Base.
- [ ] Commit changes to git.

---

### Task 3: Security & Cryptographic Primitives (Argon2id & JWT)
**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/tests/test_security.py`

- [ ] Write tests in `backend/tests/test_security.py` for password hashing, verification, token creation, and token decoding.
- [ ] Implement `app/core/security.py`:
  - `hash_password(password: str) -> str` using Argon2id (`argon2-cffi`).
  - `verify_password(password: str, hashed: str) -> bool`.
  - `create_access_token(data: dict, expires_delta: timedelta | None) -> str`.
  - `create_refresh_token(data: dict, expires_delta: timedelta | None) -> str`.
  - `decode_token(token: str) -> dict`.
- [ ] Run pytest to verify all tests pass.
- [ ] Commit changes to git.

---

### Task 4: Database Models & Alembic Schema Migrations
**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/session.py`
- Create: `backend/app/models/audit.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/001_initial_auth_schema.py`

- [ ] Define SQLAlchemy 2.0 mapped models:
  - `User`: id (UUID), email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at.
  - `Role`: id, name (`SUPERADMIN`, `OPERATOR`, `VIEWER`), description.
  - `Permission`: id, name, resource, action.
  - `UserRole`, `RolePermission` association tables.
  - `UserSession`: id (UUID), user_id, refresh_token_hash, ip_address, user_agent, expires_at, is_revoked.
  - `AuditLog`: id (UUID), user_id, event, ip_address, user_agent, details, created_at.
- [ ] Configure Alembic `env.py` referencing models Base.
- [ ] Create initial migration `001_initial_auth_schema.py`.
- [ ] Verify migration syntax.
- [ ] Commit changes to git.

---

### Task 5: Schemas, Services & Authentication REST Endpoints
**Files:**
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/services/auth_service.py`
- Create: `backend/app/services/audit_service.py`
- Create: `backend/app/api/deps.py`
- Create: `backend/app/api/v1/auth.py`
- Create: `backend/app/api/v1/router.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/test_auth_api.py`

- [ ] Implement Pydantic request & response schemas (`LoginRequest`, `RegisterRequest`, `TokenResponse`, `UserResponse`, `RefreshRequest`).
- [ ] Implement `AuditService.log_event(...)` recording client IP, user agent, event type, and details.
- [ ] Implement `AuthService` handling password verification, session record generation, and token issuance.
- [ ] Implement dependency injection in `deps.py` for DB session and `get_current_user`.
- [ ] Implement REST endpoints:
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/refresh`
  - `POST /api/v1/auth/logout`
  - `GET /api/v1/auth/me`
  - `POST /api/v1/auth/register`
- [ ] Configure CORS, logging, and router inclusion in `backend/app/main.py`.
- [ ] Write integration test `tests/test_auth_api.py` verifying login with Argon2id and audit logging.
- [ ] Run pytest to verify all tests pass.
- [ ] Commit changes to git.

---

### Task 6: Ephemeral First-Run Seeding Script with Self-Wipeout
**Files:**
- Create: `backend/scripts/seed_first_user.py`
- Create: `backend/entrypoint.sh`
- Create: `backend/tests/test_seeding.py`

- [ ] Implement `backend/scripts/seed_first_user.py`:
  - Connects to database.
  - Checks if `cctv@gmail.com` exists.
  - If absent: generates `SUPERADMIN` role, hashes `123456789` with Argon2id, inserts user, logs `SEED_PROVISION` audit event.
  - If present: logs that admin already exists and exits cleanly.
  - Performs self-destruction: `os.remove(__file__)` on execution finish.
- [ ] Implement `backend/entrypoint.sh`:
  - Runs `alembic upgrade head`.
  - Executes `seed_first_user.py` if file exists, then ensures `rm -f /app/scripts/seed_first_user.py`.
  - Executes `exec uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- [ ] Write test `tests/test_seeding.py` verifying idempotency and wipeout behavior.
- [ ] Commit changes to git.

---

### Task 7: Containerization & Docker Compose Topology
**Files:**
- Create: `backend/Dockerfile`
- Create: `docker-compose.yml`

- [ ] Create `backend/Dockerfile` using Python 3.12 slim, installing dependencies and configuring `entrypoint.sh`.
- [ ] Create `docker-compose.yml` configuring:
  - `db`: PostgreSQL 16 Alpine with persistent named volume `postgres_data` and healthcheck.
  - `backend`: FastAPI app with port 8000, depends on healthy `db`.
  - `frontend`: React app with port 5173.
- [ ] Commit changes to git.

---

### Task 8: Frontend Scaffolding, Tailwind CSS & Assets Setup
**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/index.css`
- Create: `frontend/src/assets/cctv-camera.png`
- Create: `frontend/Dockerfile`

- [ ] Scaffold React + Vite + Tailwind CSS in `frontend/`.
- [ ] Configure Tailwind theme with custom deep surveillance cyan/teal palette (`vigilant-dark: #071616`, `vigilant-card: #0c1618`, `vigilant-teal: #15b89a`, `vigilant-border: #153032`).
- [ ] Process and save the high-resolution CCTV camera visual asset in `frontend/src/assets/cctv-camera.png` matching Reference 1.
- [ ] Install frontend dependencies (`lucide-react`, `axios`, etc.).
- [ ] Verify build via `npm run build`.
- [ ] Commit changes to git.

---

### Task 9: Frontend Authentication Client & Context Provider
**Files:**
- Create: `frontend/src/types/auth.ts`
- Create: `frontend/src/services/api.ts`
- Create: `frontend/src/context/AuthContext.tsx`
- Create: `frontend/src/components/ProtectedRoute.tsx`

- [ ] Define TypeScript types for user, tokens, and credentials.
- [ ] Implement `services/api.ts` with Axios interceptors for automated JWT injection and refresh token rotation on 401.
- [ ] Implement `AuthContext.tsx` managing `user`, `login()`, `logout()`, `register()`, and `loading` states.
- [ ] Implement `ProtectedRoute.tsx` ensuring unauthenticated users cannot access dashboard.
- [ ] Commit changes to git.

---

### Task 10: Surveillance Login Page Implementation (Faithful to Reference 1)
**Files:**
- Create: `frontend/src/components/BrandLogo.tsx`
- Create: `frontend/src/pages/Login.tsx`

- [ ] Implement `BrandLogo.tsx` with clean `VIGILANT` typography and pulsing green AI status indicator.
- [ ] Implement `Login.tsx`:
  - Left hero section displaying the 3D CCTV dome camera with ambient cyan spotlight reflection.
  - Floating dark card on the right with glowing "Sign in" header.
  - "Username" input field with placeholder `example@gmail.com`.
  - "Password" input field with eye icon to toggle show/hide.
  - "Forgot Password?" right-aligned link.
  - "Login" prominent teal button with loading spinner.
  - "Don't have an Account? Sign up" modal/toggle for registering additional users.
  - Clean error banners and field validation.
- [ ] Commit changes to git.

---

### Task 11: Empty Surveillance Dashboard & Command Center UI
**Files:**
- Create: `frontend/src/pages/Dashboard.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/main.tsx`

- [ ] Implement `Dashboard.tsx`:
  - Top surveillance navbar with system health indicator (`ONLINE`), AI inference status (`READY`), live clock, user badge (`cctv@gmail.com` / `SUPERADMIN`), and Logout button.
  - Telemetry summary cards: Active Cameras (0), AI Detections Today (0), Storage Used (0 GB), Threat Alerts (0).
  - Empty camera viewport: Surveillance crosshairs icon, "No CCTV Streams Connected", "Connect Camera Feed" action button.
- [ ] Wire up routes in `App.tsx` (`/login`, `/dashboard`, default redirect).
- [ ] Verify frontend build and styling.
- [ ] Commit changes to git.

---

### Task 12: End-to-End Verification, Automated Tests & Handoff Documentation
**Files:**
- Modify: `.agent/progress.md`
- Create: `README.md`

- [ ] Run backend unit and integration test suite (`pytest`).
- [ ] Verify seed script execution and self-wipeout behavior.
- [ ] Test frontend build (`npm run build`).
- [ ] Verify login flow with `cctv@gmail.com` / `123456789`.
- [ ] Create comprehensive `README.md` with Docker Compose startup instructions, architecture guide, and local execution details.
- [ ] Commit final updates to git.
