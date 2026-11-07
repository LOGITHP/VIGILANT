# Architecture Decision Records (ADRs) - VIGILANT

## ADR-001: Authentication Architecture & Cryptographic Primitives
- **Date:** 2026-11-06
- **Status:** Accepted
- **Context:** An enterprise AI CCTV surveillance platform requires robust protection against credential cracking, token replay attacks, and insider tampering.
- **Decision:**
  - Adopt **Argon2id** (`argon2-cffi`) for password hashing with parameters: memory_cost=64MB, time_cost=3, parallelism=4.
  - Implement a dual-token **JWT** architecture:
    - 15-minute Access Tokens with claims (`sub`, `email`, `roles`).
    - 7-day sliding Refresh Tokens stored hashed in the `sessions` table to support real-time token revocation upon logout or threat detection.
  - Utilize **SQLAlchemy 2.0** with async engine support and **Alembic** for schema migrations.

## ADR-002: Ephemeral Database Seeding with Self-Wipe
- **Date:** 2026-11-06
- **Status:** Accepted
- **Context:** The system requires a bootstrap superuser (`cctv@gmail.com` / `123456789`) on the first container startup, persisted into Docker volumes, while strictly ensuring no plaintext seed credentials or seed scripts persist on the container filesystem across restarts.
- **Decision:**
  - Implement an ephemeral container entrypoint sequence:
    1. Run `alembic upgrade head`.
    2. Execute `seed_first_user.py` if present.
    3. The seed script provisions the initial superuser only if absent, commits to the persistent PostgreSQL volume, and permanently deletes itself from the filesystem (`rm -f`).
    4. Subsequent container startups detect the absence of the seed script and proceed without re-provisioning or throwing errors.

## ADR-003: UI/UX Fidelity & Visual Assets
- **Date:** 2026-11-06
- **Status:** Accepted
- **Context:** The login interface must mirror the provided reference design: CCTV camera render with cyan/teal ambiance on the left, floating glassmorphic card on the right, and brand identity "VIGILANT".
- **Decision:**
  - Render an optimized high-resolution CCTV camera visual asset for the left hero panel.
  - Implement the right-side authentication card with Tailwind CSS, custom dark cyan styling (`#0c1618`), glowing teal typography, rounded inputs, password reveal toggle, and a responsive glassmorphic backdrop.
  - Omit third-party social logins (Google, Apple, Facebook) as requested.

## ADR-004: Client-Side Reverse Proxy & Flexible Identifier Ingestion
- **Date:** 2026-11-07
- **Status:** Accepted
- **Context:** Containerized production preview environments and varied clients may submit credentials under either `username` or `email` payload keys, and browser clients need predictable API proxying.
- **Decision:**
  - Enhance FastAPI Pydantic `LoginRequest` validator to seamlessly accept both `username` and `email` payload keys.
  - Configure Vite preview mode with reverse proxy forwarding `/api` to the backend service.
  - Configure client-side API base URL with fallback to `http://localhost:8000/api/v1` for local browser execution.

## ADR-005: Resumable Chunk Ingestion, Chainguard MinIO Storage & HTTP 206 Streaming
- **Date:** 2026-11-07
- **Status:** Accepted
- **Context:** Surveillance feeds produce large, continuous video files (1080p, 4K) that risk transfer timeouts, memory exhaustion, and playback lag if transferred or stored as monolithic payloads.
- **Decision:**
  - **Chunked Resumable Upload**: Clients divide media into 5MB chunks, computing client-side Web Crypto SHA-256 hashes per chunk. FastAPI verifies each chunk's integrity on arrival, stores them in ephemeral staging, and supports pausing/resuming interrupted uploads via `/upload/{id}/status`.
  - **S3 Object Storage**: Selected `cgr.dev/chainguard/minio:latest` for zero-vulnerability S3 object storage with persistent Docker volume `vigilant_minio_data`. Automated startup hooks guarantee bucket existence (`vigilant-videos`, `vigilant-thumbnails`).
  - **FFprobe & FFmpeg Telemetry**: Native containerized `ffprobe` extracts exact stream metadata (duration, FPS, resolution, codecs, bitrate) stored into PostgreSQL `videos`. Asynchronous `ffmpeg` generates an instant surveillance thumbnail at timestamp 1.0s and uploads it to MinIO.
  - **HTTP 206 Partial Content Streaming**: Backend proxies range-sliced object streams (`get_object(offset, length)`) directly from MinIO, delivering byte-level scrubbing, timestamp jumping, and instant seek in modern HTML5 surveillance video players.



