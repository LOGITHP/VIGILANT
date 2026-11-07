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

## ADR-006: Segregated Surveillance Archives (Live CCTV Stream Archive vs Uploaded Video Archive)
- **Date:** 2026-11-07
- **Status:** Accepted
- **Context:** Operators need clear separation between continuous 24/7 or event-triggered CCTV camera stream recordings and manually imported external evidence / offline surveillance files. Mixing both into a single unsegmented table leads to operational confusion.
- **Decision:**
  - **Data Model Segregation**: Added `source_type` (`LIVE` vs `UPLOADED`) to the `videos` PostgreSQL schema with Alembic migration `003_add_video_source_type.py` and indexed column lookups.
  - **API Scoping**: Updated `GET /api/v1/videos` to accept `source_type=LIVE` or `source_type=UPLOADED`, guaranteeing completely disjoint result sets for client queries. Added `POST /api/v1/videos/live/record` for immediate camera clip ingestion.
  - **UI/UX Segregation**: Replaced the monolithic `VIDEO ARCHIVE` with dedicated top-level navigation tabs:
    - `LIVE ARCHIVE` (featuring pulsating red indicators, camera channel tags, live clip capture, and stream metadata).
    - `UPLOADED ARCHIVE` (featuring uploader identity, file format details, and upload center ingestion).
  - **Upload Routing**: Enhanced the `UploadCenter` to permit selecting whether ingested batches belong to the manual Uploaded Archive or a Live Camera Stream Dump.

## ADR-007: Phase 3.1.1 FFprobe Metadata Extractor, Primary Stream Selection & Dual State Machine
- **Date:** 2026-11-07
- **Status:** Accepted
- **Context:** Raw container metadata extraction must systematically classify telemetry across 5 distinct categories (File Info, Container Info, Primary Video Stream, Primary Audio Stream, Stream Catalog). Furthermore, CCTV containers frequently bundle attached cover art/poster JPEGs as stream 0, which can mislead naive stream selection. Crucially, successful header inspection must never imply full media validation (corrupted subsequent frames require full decode validation in Milestone 3.1.2).
- **Decision:**
  - **5-Category Normalized Telemetry**: Standardized output across FileInfo (SHA-256, size, format), ContainerInfo (format, duration, bitrate, start time), VideoStreamInfo (codec, dimensions, rational FPS, pixel format, time base), AudioStreamInfo (codec, sample rate, channels), and Stream Catalog (all streams with dispositions).
  - **Intelligent Stream Selector**: Explicitly ignores static attached pictures (`disposition.attached_pic == 1`) and resolves the true continuous video feed prioritizing default flags, then highest pixel count ($width \times height$).
  - **Dual State Machine**: Retained strict segregation between `metadata_status` (`PENDING`, `EXTRACTING`, `COMPLETED`, `FAILED`) and `validation_status` (`PENDING`, `VALIDATING`, `VALIDATED`, `INVALID`), ensuring header extraction does not falsely mark corrupted files as validated before Milestones 3.1.2/3.1.3.
  - **Resource Protection**: Bounded concurrency to 2 simultaneous inspections via `asyncio.Semaphore(2)`, 120-second timeout, and ephemeral sandboxing with guaranteed cleanup.
  - **Database & UI Integration**: PostgreSQL `video_inspections` and `video_streams` schemas with cascading deletes, REST endpoints (`GET /videos/{id}/inspection`, `POST /videos/{id}/inspect`), and a dedicated 5-category surveillance metadata inspection drawer in React.





