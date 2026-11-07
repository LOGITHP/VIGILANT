# VIGILANT Video Upload, Storage & Playback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an enterprise-grade CCTV video upload, MinIO object storage, FFprobe/FFmpeg metadata extraction, HTTP 206 range-based streaming, and surveillance video player & library for VIGILANT.

**Architecture:** Frontend React splits video into 5MB chunks and transmits with SHA-256 hashes to FastAPI; FastAPI tracks chunks in PostgreSQL and reassembles the stream into MinIO object storage; an asynchronous background worker executes FFprobe for stream telemetry and FFmpeg for thumbnail generation; video playback uses HTTP 206 Partial Content range proxying directly from MinIO with full scrub and speed controls in a surveillance-aesthetic UI.

**Tech Stack:** React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, FastAPI (Python 3.12), SQLAlchemy 2.0 (async), Alembic, MinIO S3 Object Storage, FFmpeg & FFprobe, PostgreSQL 16, Docker Compose.

**Spec:** `docs/vigilant-video-pipeline-design.md`

## Global Constraints
- **Database Engine**: PostgreSQL 16 with async SQLAlchemy 2.0 and Alembic migrations.
- **Object Storage**: MinIO with persistent volume `minio_data` and buckets `vigilant-videos` and `vigilant-thumbnails`.
- **Media Inspection**: Native `ffprobe` and `ffmpeg` installed in backend container.
- **Authentication**: All endpoints protected with JWT Bearer tokens; Role-Based Access Control (`SUPERADMIN`, `OPERATOR`, `VIEWER`).
- **Chunk Size**: Standard 5MB (5,242,880 bytes) chunks with SHA-256 integrity validation.
- **Streaming**: Strict HTTP 206 Partial Content compliance with `Range: bytes=start-end` and `Accept-Ranges: bytes`.
- **UI Aesthetics**: Surveillance dark teal theme (`#081818`, `#0c1618`, `#15b89a`, `#2dd4bf`), responsive, glassmorphic accents.

## Review Focus
1. **Interrupted / Resumed Uploads**: When an upload is paused or network drops, already uploaded chunks must be recognized and not re-uploaded.
2. **SHA-256 Hash Mismatch**: Corrupted chunks must be rejected immediately with an HTTP 400 error.
3. **HTTP 206 Range Seeking**: Seeking forward/backward in the video player must request exact byte ranges from MinIO without buffering the whole file.
4. **Non-blocking Media Metadata**: FFprobe extraction on multi-gigabyte files must run asynchronously without blocking API responses.
5. **Memory Efficiency**: Chunk reassembly and range streaming must stream byte chunks without reading entire gigabyte files into RAM.

---

## Tasks

### Task 1: MinIO Storage Infrastructure & Backend Dependencies
**Files:**
- Modify: `docker-compose.yml:1-67`
- Modify: `backend/Dockerfile:1-30`
- Modify: `backend/requirements.txt:1-19`
- Modify: `backend/app/core/config.py:1-40`
- Create: `backend/app/core/minio_client.py`
- Test: `backend/tests/test_minio_client.py`

**Steps:**
- [ ] Add `minio>=7.2.10` and `aiofiles>=24.1.0` to `backend/requirements.txt`.
- [ ] Update `backend/Dockerfile` to install `ffmpeg` (which supplies both `ffmpeg` and `ffprobe`).
- [ ] Add `minio` container definition and `minio_data` volume in `docker-compose.yml`.
- [ ] Update `backend/app/core/config.py` with MinIO configuration settings (`MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_SECURE`, `MINIO_BUCKET_VIDEOS`, `MINIO_BUCKET_THUMBNAILS`).
- [ ] Create `backend/app/core/minio_client.py` with singleton MinIO client and bucket auto-initialization.
- [ ] Write unit test `backend/tests/test_minio_client.py` to verify configuration loading and bucket creation logic.
- [ ] Run test: `$env:PYTHONPATH='backend'; python -m pytest backend/tests/test_minio_client.py`.
- [ ] Commit: `git add -A && git commit -m "feat(infra): add minio object storage service and backend dependencies"`.

---

### Task 2: Database Models & Alembic Migration for Video Archive
**Files:**
- Create: `backend/app/models/video.py`
- Modify: `backend/app/models/__init__.py:1-15`
- Create: `backend/alembic/versions/002_video_storage_schema.py`
- Test: `backend/tests/test_video_models.py`

**Steps:**
- [ ] Create `backend/app/models/video.py` defining `Video`, `VideoUploadSession`, and `VideoChunk` SQLAlchemy 2.0 ORM models with relations to `User`.
- [ ] Export new models in `backend/app/models/__init__.py`.
- [ ] Create Alembic migration `backend/alembic/versions/002_video_storage_schema.py` creating `videos`, `video_upload_sessions`, and `video_chunks` tables with indices.
- [ ] Write test `backend/tests/test_video_models.py` creating records in SQLite/Postgres.
- [ ] Run test: `$env:PYTHONPATH='backend'; python -m pytest backend/tests/test_video_models.py`.
- [ ] Commit: `git add -A && git commit -m "feat(db): add video archive, upload sessions, and chunks database models"`.

---

### Task 3: MinIO Storage Service & Chunk Assembly Engine
**Files:**
- Create: `backend/app/services/storage_service.py`
- Test: `backend/tests/test_storage_service.py`

**Steps:**
- [ ] Implement `StorageService` in `backend/app/services/storage_service.py` with methods:
  - `save_chunk(upload_id, chunk_index, chunk_data, expected_hash)`
  - `assemble_and_upload(upload_id, total_chunks, target_s3_key)`
  - `stream_byte_range(s3_key, start, length)`
  - `upload_thumbnail(video_id, image_bytes)`
  - `delete_video_objects(s3_key, thumbnail_s3_key)`
- [ ] Write unit tests in `backend/tests/test_storage_service.py` verifying chunk hash validation, disk cleanup, and streaming range slicing.
- [ ] Run test: `$env:PYTHONPATH='backend'; python -m pytest backend/tests/test_storage_service.py`.
- [ ] Commit: `git add -A && git commit -m "feat(storage): implement storage service for chunk management and minio integration"`.

---

### Task 4: Media Telemetry (FFprobe) & Thumbnail Generation (FFmpeg)
**Files:**
- Create: `backend/app/services/media_service.py`
- Test: `backend/tests/test_media_service.py`

**Steps:**
- [ ] Implement `MediaProcessingService` in `backend/app/services/media_service.py`:
  - `extract_metadata(file_path_or_stream)` using `ffprobe` JSON output (duration, width, height, fps, codecs, bitrate).
  - `generate_thumbnail(file_path_or_stream, timestamp_sec)` using `ffmpeg` single-frame extract scaled to 640px.
  - Asynchronous background task runner `process_video_post_upload(video_id, db_session)`.
- [ ] Write unit tests `backend/tests/test_media_service.py` with mock ffprobe outputs and sample generated frame.
- [ ] Run test: `$env:PYTHONPATH='backend'; python -m pytest backend/tests/test_media_service.py`.
- [ ] Commit: `git add -A && git commit -m "feat(media): implement ffprobe telemetry extractor and ffmpeg thumbnail generator"`.

---

### Task 5: Video REST API Endpoints (Upload, Library, Range Streaming)
**Files:**
- Create: `backend/app/schemas/video.py`
- Create: `backend/app/api/v1/videos.py`
- Modify: `backend/app/api/v1/__init__.py` or `backend/app/main.py:1-60`
- Test: `backend/tests/test_videos_api.py`

**Steps:**
- [ ] Create Pydantic schemas in `backend/app/schemas/video.py` (`VideoUploadInitRequest`, `VideoUploadInitResponse`, `ChunkUploadResponse`, `UploadCompleteRequest`, `VideoResponse`, `VideoListResponse`, `VideoFilterParams`).
- [ ] Create REST routes in `backend/app/api/v1/videos.py`:
  - `POST /upload/init` (Start upload session)
  - `POST /upload/chunk` (Store chunk with SHA-256 check)
  - `GET /upload/{upload_id}/status` (Get uploaded chunk indices for resumption)
  - `POST /upload/complete` (Reassemble, send to MinIO, trigger background task)
  - `GET /` (List videos with pagination, search query, status/format/date filters)
  - `GET /{video_id}` (Get single video metadata)
  - `GET /{video_id}/stream` (HTTP 206 Partial Content range streaming)
  - `GET /{video_id}/thumbnail` (Serve thumbnail JPEG)
  - `DELETE /{video_id}` (Delete video and remove MinIO objects)
- [ ] Register `/videos` router in `backend/app/main.py`.
- [ ] Write tests `backend/tests/test_videos_api.py` testing complete upload cycle, range streaming headers, and permission checks.
- [ ] Run test: `$env:PYTHONPATH='backend'; python -m pytest backend/tests/test_videos_api.py`.
- [ ] Commit: `git add -A && git commit -m "feat(api): implement video upload, library, and http 206 range streaming endpoints"`.

---

### Task 6: Frontend Video Types & Resumable Chunk Upload Engine
**Files:**
- Create: `frontend/src/types/video.ts`
- Create: `frontend/src/services/videoApi.ts`
- Create: `frontend/src/utils/chunkUploader.ts`

**Steps:**
- [ ] Create `frontend/src/types/video.ts` with TypeScript interfaces for `Video`, `VideoMetadata`, `UploadSession`, `UploadProgress`, `VideoFilter`.
- [ ] Create `frontend/src/services/videoApi.ts` calling all backend `/videos` endpoints via `apiClient`.
- [ ] Implement `frontend/src/utils/chunkUploader.ts`:
  - Splits `File` into 5MB chunks (`file.slice`).
  - Calculates chunk SHA-256 using Web Crypto API (`crypto.subtle.digest`).
  - Supports concurrency, pause, resume, progress callbacks, and retry on network hiccup.
- [ ] Commit: `git add -A && git commit -m "feat(frontend): add video types, api client, and resumable chunk uploader engine"`.

---

### Task 7: Frontend Video Upload Center UI
**Files:**
- Create: `frontend/src/components/video/UploadCenter.tsx`
- Create: `frontend/src/components/video/UploadQueueItem.tsx`

**Steps:**
- [ ] Build `UploadCenter.tsx` with:
  - Drag-and-drop file dropzone with visual highlights.
  - Video file selector with multi-file support (`.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`).
  - Title and surveillance camera/location input metadata.
- [ ] Build `UploadQueueItem.tsx` displaying:
  - Live progress bar (0% - 100%), uploaded bytes vs total size.
  - Real-time upload speed (MB/s) and estimated time remaining (ETA).
  - Status pills (`Waiting`, `Uploading Chunk X/Y`, `Processing Metadata`, `Complete`, `Failed`).
  - Pause, Resume, Retry, and Cancel action buttons.
- [ ] Commit: `git add -A && git commit -m "feat(frontend): create video upload center with drag-and-drop and progress tracking"`.

---

### Task 8: Frontend Surveillance Video Library UI (Grid & Table Views)
**Files:**
- Create: `frontend/src/components/video/VideoLibrary.tsx`
- Create: `frontend/src/components/video/VideoCard.tsx`
- Create: `frontend/src/components/video/VideoTableView.tsx`
- Create: `frontend/src/components/video/VideoFilterBar.tsx`

**Steps:**
- [ ] Build `VideoFilterBar.tsx` with search input, status filter pills (`All`, `Ready`, `Processing`, `Uploading`, `Failed`), resolution and codec dropdowns, and Grid/Table layout toggle.
- [ ] Build `VideoCard.tsx` with thumbnail preview, duration pill, resolution badge (`4K`, `1080p`, `720p`), codec tag, time ago, and click-to-play trigger.
- [ ] Build `VideoTableView.tsx` with tabular surveillance columns: Title/File, Status, Duration, Resolution, FPS, Codecs, Size, Uploaded By, Date, Actions.
- [ ] Build `VideoLibrary.tsx` orchestrating data fetching, pagination, delete confirmation, and empty-state surveillance UI.
- [ ] Commit: `git add -A && git commit -m "feat(frontend): implement surveillance video library with card grid and table views"`.

---

### Task 9: Frontend Surveillance Video Player Modal
**Files:**
- Create: `frontend/src/components/video/VideoPlayerModal.tsx`
- Create: `frontend/src/components/video/VideoControls.tsx`

**Steps:**
- [ ] Build `VideoPlayerModal.tsx` with full surveillance theater aesthetic:
  - Header: Video title, camera tag, recorded timestamp, close button.
  - Video stream viewport connected to `/api/v1/videos/{id}/stream`.
  - Telemetry drawer: Resolution, Codec, FPS, Bitrate, SHA-256 Checksum, MinIO storage key.
- [ ] Build `VideoControls.tsx`:
  - Play / Pause button with spacebar shortcut.
  - Scrub bar with buffered progress and hover timestamp preview.
  - Time display: `HH:MM:SS / HH:MM:SS`.
  - Quick seek jumps: `-10s`, `-5s`, `+5s`, `+10s`.
  - Speed selector: `0.5x`, `1.0x`, `1.25x`, `1.5x`, `2.0x`.
  - Volume slider and mute toggle.
  - Fullscreen toggle.
- [ ] Commit: `git add -A && git commit -m "feat(frontend): create surveillance theater video player with range seeking and telemetry"`.

---

### Task 10: Integrated Top Navigation & Main View Integration
**Files:**
- Modify: `frontend/src/pages/Dashboard.tsx:1-120`
- Create: `frontend/src/components/layout/Navbar.tsx`

**Steps:**
- [ ] Create `Navbar.tsx` with brand logo, tab navigation (`Live CCTV`, `Video Archive`, `Upload Center`), upload count badge, and user profile / logout button.
- [ ] Refactor `Dashboard.tsx` to host tabbed views:
  - Tab 1: Live CCTV Command Center.
  - Tab 2: Video Archive Library.
  - Tab 3: Upload Center.
  - Active video player modal triggered from any tab.
- [ ] Commit: `git add -A && git commit -m "feat(frontend): integrate top surveillance navigation with live, archive, and upload views"`.

---

### Task 11: End-to-End Containerization, Testing & Documentation
**Files:**
- Modify: `docs/vigilant-video-pipeline-plan.md`
- Modify: `docs/README.md`
- Modify: `.agent/progress.md`
- Test: Local pytest suite, Docker Compose live testing.

**Steps:**
- [ ] Run all backend unit & API integration tests: `$env:PYTHONPATH='backend'; python -m pytest backend/tests`.
- [ ] Rebuild and start full Docker Compose stack: `docker compose up -d --build`.
- [ ] Verify MinIO is running and buckets `vigilant-videos` and `vigilant-thumbnails` are initialized.
- [ ] Execute test video upload via API / script (including chunk upload, reassembly, FFprobe metadata, and thumbnail).
- [ ] Verify HTTP 206 partial content streaming with curl range requests (`curl -r 0-1024 ...`).
- [ ] Update `docs/README.md` and `.agent/progress.md`.
- [ ] Commit and push to git repository.
