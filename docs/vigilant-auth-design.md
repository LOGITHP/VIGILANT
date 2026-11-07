# VIGILANT - AI CCTV Surveillance Intelligence System
## Authentication & Empty Dashboard Technical Specification

- **Project Name:** VIGILANT
- **System Classification:** AI-Powered CCTV Intelligence System
- **Module:** Authentication Service, Security Architecture & Initial Dashboard
- **Date:** 2026-11-06
- **Status:** Approved / In Design

---

## 1. System Overview & Objectives

VIGILANT is an enterprise-grade AI-powered CCTV surveillance and computer vision intelligence platform. This specification details the design for the core authentication module, database schema, containerized infrastructure, and the initial user dashboard.

### Key Objectives
1. **Surveillance Aesthetic Login Interface:** Faithfully reproduce the reference visual layout featuring the 3D CCTV dome camera with ambient cyan/teal illumination and a floating glassmorphic authentication card.
2. **Robust Security Stack:**
   - **Argon2id** password hashing (`argon2-cffi`).
   - **JWT** (JSON Web Token) access and sliding refresh tokens.
   - **RBAC** (Role-Based Access Control) supporting `SUPERADMIN`, `OPERATOR`, and `VIEWER` roles.
   - **Audit Logs & Sessions:** Detailed forensic tracking for compliance in surveillance systems.
3. **Automated First-Run Provisioning & Ephemeral Wipeout:**
   - Default Super Admin: `cctv@gmail.com` / `123456789`.
   - Idempotently stored in the PostgreSQL persistent Docker volume on first startup.
   - Self-deleting seed script (`seed_first_user.py`) that scrubs all creation artifacts immediately upon initialization, preventing plaintext credential exposure.
4. **Empty Dashboard Foundation:** Surveillance command center placeholder displaying system status, AI engine readiness, live telemetry clocks, user badge, and secure logout.

---

## 2. System Architecture

Mapped directly to the approved security architecture:

```
+-------------------------------------------------------------------+
|                           React Frontend                          |
|         Login Form / Field Validation / Auth State Context        |
+---------------------------------+---------------------------------+
                                  |
                           HTTPS / REST API
                                  |
                                  v
+-------------------------------------------------------------------+
|                    FastAPI Authentication Service                 |
|       Login - Token Validation - RBAC - Session Management       |
+-------------------+---------------------------+-------------------+
                    |                           |
                    v                           v
     +-----------------------------+ +-----------------------------+
     |          Argon2id           | |             JWT             |
     |     Password Verification   | |        Token Issuance       |
     +--------------+--------------+ +--------------+--------------+
                    |                               |
                    +---------------+---------------+
                                    |
                                    v
+-------------------------------------------------------------------+
|                         PostgreSQL Database                       |
|        Users - Roles - Permissions - Sessions - Audit Logs       |
+-------------------------------------------------------------------+
```

---

## 3. Directory & Folder Structure

```
VIGILANT/
├── docs/
│   ├── vigilant-auth-design.md
│   └── DECISIONS.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── entrypoint.sh
│   ├── scripts/
│   │   └── seed_first_user.py         # Ephemeral script: self-deletes after execution
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 001_initial_auth_schema.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py              # Pydantic BaseSettings
│   │   │   └── security.py            # Argon2id password hasher & JWT manager
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py             # Async SQLAlchemy 2.0 engine & sessionmaker
│   │   │   └── base.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py                # User, Role, Permission, UserRole, RolePermission
│   │   │   ├── session.py             # UserSession
│   │   │   └── audit.py               # AuditLog
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                # Token, LoginRequest, RegisterRequest, RefreshRequest
│   │   │   ├── user.py                # UserResponse, UserProfile
│   │   │   └── audit.py               # AuditLogRead
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py        # Login, logout, session tracking
│   │   │   └── audit_service.py       # Structured audit event logging
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── deps.py                # Dependency injection: get_db, get_current_user
│   │       └── v1/
│   │           ├── __init__.py
│   │           ├── router.py
│   │           └── auth.py            # REST endpoints
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_security.py
│       ├── test_auth_api.py
│       └── test_seeding.py
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── assets/
        │   └── cctv-camera.png        # Rendered CCTV dome camera asset
        ├── components/
        │   ├── ui/
        │   │   ├── Input.tsx
        │   │   └── Button.tsx
        │   ├── BrandLogo.tsx
        │   └── ProtectedRoute.tsx
        ├── pages/
        │   ├── Login.tsx              # Matches Reference 1 layout & aesthetic
        │   └── Dashboard.tsx          # Surveillance Command Center (Empty state)
        ├── context/
        │   └── AuthContext.tsx        # Authentication provider & token lifecycle
        ├── services/
        │   └── api.ts                 # Axios client with JWT refresh interceptor
        ├── types/
        │   └── auth.ts
        ├── App.tsx
        ├── main.tsx
        └── index.css
```

---

## 4. Database Schema Specifications (`PostgreSQL`)

### 4.1 Tables
1. **`users`**:
   - `id`: UUID (Primary Key, default uuid4)
   - `email`: VARCHAR(255) (Unique, Not Null, Indexed)
   - `hashed_password`: VARCHAR(255) (Not Null, Argon2id hash string)
   - `full_name`: VARCHAR(255) (Nullable)
   - `is_active`: BOOLEAN (Default True)
   - `is_superuser`: BOOLEAN (Default False)
   - `created_at`: TIMESTAMPTZ (Default now())
   - `updated_at`: TIMESTAMPTZ (Default now(), onupdate now())

2. **`roles`**:
   - `id`: INTEGER (Primary Key, Autoincrement)
   - `name`: VARCHAR(50) (Unique, Not Null, e.g., `SUPERADMIN`, `OPERATOR`, `VIEWER`)
   - `description`: VARCHAR(255)

3. **`permissions`**:
   - `id`: INTEGER (Primary Key, Autoincrement)
   - `name`: VARCHAR(100) (Unique, Not Null, e.g., `camera:stream`, `camera:manage`, `audit:read`)
   - `resource`: VARCHAR(50)
   - `action`: VARCHAR(50)

4. **`user_roles`**:
   - `user_id`: UUID (Foreign Key `users.id` ON DELETE CASCADE)
   - `role_id`: INTEGER (Foreign Key `roles.id` ON DELETE CASCADE)
   - Primary Key: `(user_id, role_id)`

5. **`role_permissions`**:
   - `role_id`: INTEGER (Foreign Key `roles.id` ON DELETE CASCADE)
   - `permission_id`: INTEGER (Foreign Key `permissions.id` ON DELETE CASCADE)
   - Primary Key: `(role_id, permission_id)`

6. **`sessions`**:
   - `id`: UUID (Primary Key)
   - `user_id`: UUID (Foreign Key `users.id` ON DELETE CASCADE)
   - `refresh_token_hash`: VARCHAR(255) (Indexed, Not Null)
   - `ip_address`: VARCHAR(45) (Nullable)
   - `user_agent`: VARCHAR(255) (Nullable)
   - `expires_at`: TIMESTAMPTZ (Not Null)
   - `is_revoked`: BOOLEAN (Default False)
   - `created_at`: TIMESTAMPTZ (Default now())

7. **`audit_logs`**:
   - `id`: UUID (Primary Key)
   - `user_id`: UUID (Foreign Key `users.id` ON DELETE SET NULL, Nullable)
   - `event`: VARCHAR(50) (Not Null: `LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGOUT`, `TOKEN_REFRESH`, `SEED_PROVISION`)
   - `ip_address`: VARCHAR(45) (Nullable)
   - `user_agent`: VARCHAR(255) (Nullable)
   - `details`: JSONB (Nullable)
   - `created_at`: TIMESTAMPTZ (Default now(), Indexed)

---

## 5. Security & Authentication Flow

### 5.1 Password Hashing with Argon2id
- Library: `argon2-cffi`
- Type: Argon2id (resists side-channel and GPU cracking attacks)
- Configuration:
  - `memory_cost`: 65536 KB (64 MiB)
  - `time_cost`: 3 iterations
  - `parallelism`: 4 threads

### 5.2 Token Strategy (JWT)
- **Access Token**:
  - Expiration: 15 minutes
  - Payload: `{ "sub": user_id, "email": email, "roles": [...], "type": "access", "exp": ... }`
  - Signature: HMAC-SHA256 (`HS256`) with `JWT_SECRET`
- **Refresh Token**:
  - Expiration: 7 days
  - Payload: `{ "sub": user_id, "session_id": session_id, "type": "refresh", "exp": ... }`
  - Stored in database as a secure hash for instant revocation on logout or anomaly detection.

### 5.3 REST API Endpoints
- `POST /api/v1/auth/login`: Accepts email & password, verifies Argon2id hash, records session, returns `access_token`, `refresh_token`, and user profile.
- `POST /api/v1/auth/refresh`: Accepts refresh token, validates against session table, issues new access token.
- `POST /api/v1/auth/logout`: Revokes current session in the database.
- `GET /api/v1/auth/me`: Returns profile and permissions of authenticated user.
- `POST /api/v1/auth/register`: Supports account registration.

---

## 6. First-Run Seed & Ephemeral Wipeout Strategy

1. **Trigger**: Handled in backend container startup `entrypoint.sh`:
   ```bash
   # 1. Run database migrations
   alembic upgrade head

   # 2. Run seed script if present
   if [ -f /app/scripts/seed_first_user.py ]; then
       python /app/scripts/seed_first_user.py
       # 3. Permanently wipe out seed script
       rm -f /app/scripts/seed_first_user.py
   fi

   # 4. Start ASGI server
   exec uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
2. **Seed Logic (`seed_first_user.py`)**:
   - Queries `users` table for `cctv@gmail.com`.
   - If not found:
     - Creates `SUPERADMIN`, `OPERATOR`, and `VIEWER` roles.
     - Hashes `123456789` using Argon2id.
     - Inserts user `cctv@gmail.com` with `is_superuser = True` and links to `SUPERADMIN` role.
     - Inserts an audit log record: `event = 'SEED_PROVISION'`, `details = {'user': 'cctv@gmail.com'}`.
   - If found:
     - Logs: `"Default user already exists in persistent database volume. Skipping."`
   - Closes database connection and removes itself from the filesystem (`os.remove(__file__)` or via `entrypoint.sh`).

---

## 7. Frontend UI Specification

### 7.1 Visual Layout (Matching Reference 1)
- **Aesthetic**: Deep surveillance slate/teal gradient with cinematic lighting.
- **Header**: Top-left `VIGILANT` logo in clean bold sans-serif with a glowing emerald surveillance beacon dot.
- **Left Column**: High-resolution 3D CCTV dome camera seated on a circular matte pedestal with cyan spotlight reflections.
- **Right Column (Sign In Card)**:
  - Dark floating card (`bg-[#0c1618]/90`, backdrop-blur, border `#153032`, rounded-2xl).
  - Glowing mint/teal header: **Sign in** (`text-[#15b89a]`).
  - **Username** input field:
    - Label: `Username`
    - Placeholder: `example@gmail.com`
    - Rounded border, dark slate input styling with smooth focus ring.
  - **Password** input field:
    - Label: `Password`
    - Rounded border with show/hide password toggle button (eye icon).
  - **Forgot Password?** right-aligned muted link.
  - **Login** button: Prominent teal button (`bg-[#15b89a]`, hover `bg-[#139a81]`, rounded-lg, text-white font-semibold, loading state).
  - **Don't have an Account? Sign up** link: Toggles to a registration form view for user provisioning.
  - Note: Social logins (Google, Apple, Facebook) are completely excluded as requested.

### 7.2 Empty Dashboard Layout
- **Surveillance Command Header**:
  - Brand identity: `VIGILANT` | AI CCTV Intelligence System
  - Telemetry badges:
    - `SYSTEM ONLINE` (animated green pulsing LED)
    - `AI ENGINE: READY` (YOLO / Vision Inference model standby)
    - Real-time digital clock (UTC & Local Time with seconds counter)
  - User badge: `cctv@gmail.com` (`SUPERADMIN`)
  - **Logout** button with confirmation and clean session termination.
- **Empty State Telemetry Grid**:
  - Summary metrics: Active Cameras: `0`, AI Alerts Today: `0`, Storage: `0 GB`, Inference Latency: `0 ms`.
  - Center Viewport:
    - Dark surveillance grid with crosshairs icon.
    - Title: **"No CCTV Streams Connected"**.
    - Subtitle: *"Add your first IP camera feed (RTSP, ONVIF, or WebRTC) to activate automated neural surveillance, perimeter intrusion alerts, and object tracking."*
    - Action button: **"Connect Camera Feed"** (opens stream configuration modal).

---

## 8. Docker Compose Configuration

- **`db` service**: `postgres:16-alpine`
  - Volume: `postgres_data:/var/lib/postgresql/data` (preserves all data across container restarts)
  - Healthcheck: `pg_isready -U postgres -d vigilant_db`
- **`backend` service**: Python 3.12 FastAPI application
  - Port `8000:8000`
  - Depends on `db` healthy state
- **`frontend` service**: React + Vite application
  - Port `5173:5173`
  - Proxies `/api` requests to backend

---

## 9. Verification & Acceptance Criteria
1. When `docker compose up` is executed for the first time:
   - Database tables are created via Alembic.
   - User `cctv@gmail.com` with password `123456789` is seeded and stored in the persistent volume.
   - Seed script `seed_first_user.py` is permanently deleted from the container.
2. When `docker compose down` and `docker compose up` is run again:
   - No errors occur.
   - User `cctv@gmail.com` remains valid in the database volume.
   - Seed script is absent and no duplicate user is created.
3. Accessing the frontend displays the CCTV surveillance login interface matching Reference 1.
4. Logging in with `cctv@gmail.com` and `123456789`:
   - Returns 200 OK with valid JWT tokens.
   - Navigates to `/dashboard`.
   - Displays authenticated dashboard with `cctv@gmail.com` and `SUPERADMIN` status.
5. Clicking Logout revokes the session, clears tokens, and redirects back to `/login`.

