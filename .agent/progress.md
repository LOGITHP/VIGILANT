# Project Progress - VIGILANT

## Phase 1: Authentication & Empty Dashboard
- [x] Initial Requirements Analysis & Architecture Alignment
- [x] Technical Specification Document (`docs/vigilant-auth-design.md`)
- [x] Implementation Plan (`docs/vigilant-auth-plan.md`)
- [x] Task 1: Scaffolding & Root Configuration
- [x] Task 2: Backend Dependencies & Database Engine Setup
- [x] Task 3: Security & Cryptographic Primitives (Argon2id & JWT)
- [x] Task 4: Database Models & Alembic Schema Migrations
- [x] Task 5: Schemas, Services & Authentication REST Endpoints
- [x] Task 6: Ephemeral First-Run Seeding Script with Self-Wipeout
- [x] Task 7: Containerization & Docker Compose Topology
- [x] Task 8: Frontend Scaffolding, Tailwind CSS & Assets Setup
- [x] Task 9: Frontend Authentication Client & Context Provider
- [x] Task 10: Surveillance Login Page Implementation (Faithful to Reference 1)
- [x] Task 11: Empty Surveillance Dashboard & Command Center UI
- [x] Task 12: End-to-End Verification, Automated Tests & Documentation
- [x] Task 13: UI Refinements & Bug Fixes:
  - Removed clutter badges (`AI INTELLIGENCE ONLINE`, `CAM-01 • PTZ 4K AI SENSOR`, `ENCRYPTION: ARGON2ID + JWT`) per user request.
  - Re-rendered camera asset with cosine radial alpha blending and floor glow, eliminating square borders.
  - Fixed client-side API endpoint resolution & Vite preview proxy routing.
  - Enhanced Pydantic `LoginRequest` validator to accept both `username` and `email` payload keys.

## Phase 2: Video Upload, Storage, Media Processing & Playback
- [x] Technical Specification Document (`docs/vigilant-video-pipeline-design.md`)
- [x] Implementation Plan (`docs/vigilant-video-pipeline-plan.md`)
- [x] Task 1: MinIO Storage Infrastructure & Backend Dependencies (`cgr.dev/chainguard/minio:latest`, `minio>=7.2.10`, `aiofiles>=24.1.0`)
- [x] Task 2: Database Models & Alembic Migration for Video Archive (`videos`, `video_upload_sessions`, `video_chunks`)
- [x] Task 3: MinIO Storage Service & Chunk Assembly Engine (5MB chunk validation, SHA-256 integrity check, bucket lifecycle)
- [x] Task 4: Media Telemetry (FFprobe) & Thumbnail Generation (FFmpeg) (duration, fps, resolution, codecs, bitrate, frame snapshot)
- [x] Task 5: Video REST API Endpoints (Upload, Library, Range Streaming, Thumbnail)
- [x] Task 6: Frontend Video Types & Resumable Chunk Upload Engine (Web Crypto SHA-256, pause/resume, speed/ETA telemetry)
- [x] Task 7: Frontend Video Upload Center UI (Drag-and-drop dropzone, queue tracker, camera tags)
- [x] Task 8: Frontend Surveillance Video Library UI (Grid & Table views, debounced search, status filter, pagination)
- [x] Task 9: Frontend Surveillance Video Player Modal (Scrub bar, jump keys, variable speed 0.5x-2.0x, telemetry drawer)
- [x] Task 10: Integrated Top Navigation & Main View Integration (Tabs: LIVE CCTV, VIDEO ARCHIVE, UPLOAD CENTER)
- [x] Task 11: End-to-End Containerization, Testing & Documentation (21/21 backend pytest suite + 9/9 live Docker container tests)
- [x] Task 12: Archive Segregation (Live CCTV Stream Archive vs Uploaded Video Archive):
  - Database schema: added `source_type` (`LIVE` vs `UPLOADED`) via Alembic migration `003_add_video_source_type.py`.
  - Backend API: added `source_type` query filtering and `POST /api/v1/videos/live/record` for live camera clip capture.
  - UI Navigation: segregated tabs into `LIVE CCTV`, `LIVE ARCHIVE` (red indicator), `UPLOADED ARCHIVE`, and `UPLOAD CENTER`.
  - Ingestion routing: added destination archive selector in `UploadCenter`.
  - Verification: confirmed strict isolation between live recordings and uploaded videos via live container tests.

## Phase 3: Video Preprocessing & Media Inspection
### Milestone 3.1.1: FFprobe Metadata Extractor & Media Inspection
- [x] Technical Specification Document (`docs/vigilant-video-preprocessing-design.md`)
- [x] Implementation Plan (`docs/vigilant-video-preprocessing-plan.md`)
- [x] Task 1: Database Models & Alembic Schema Migration (`video_inspections`, `video_streams` with cascade delete and indexing)
- [x] Task 2: Pydantic Normalization Schemas (5 information categories: FileInfo, ContainerInfo, VideoStreamInfo, AudioStreamInfo, StreamCatalog)
- [x] Task 3: Stream Selection & Rational Number Normalizer (Cover art filtering `attached_pic == 0`, resolution & default tiebreakers, rational FPS parsing)
- [x] Task 4: Media Inspection Worker Service (`asyncio.Semaphore(2)` bounded concurrency, 120s timeout, ephemeral MinIO retrieval, guaranteed cleanup)
- [x] Task 5: FastAPI REST Endpoints (`GET /videos/{id}/inspection`, `POST /videos/{id}/inspect`)
- [x] Task 6: Frontend Inspection Manifest Drawer (`VideoInspectionDrawer.tsx` with 5-category breakdown, dual status badges, raw FFprobe JSON viewer, wired to cards, tables, and player)
- [x] Task 7: Containerization, Testing & Live Integration Verification:
  - 29/29 Pytest tests passed (100% test suite success inside Docker).
  - End-to-end integration test (`scripts/test_live_inspection.py`) executed against live Docker stack: live clip recording, automatic FFprobe dissection, 5-category verification, state segregation (`metadata_status="COMPLETED"`, `validation_status="PENDING"`), and on-demand re-probing (`POST /inspect`).
  - Frontend TypeScript compile verified (0 errors).






