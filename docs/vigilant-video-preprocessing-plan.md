# Video Preprocessing: FFprobe Metadata Extractor Implementation Plan (Milestone 3.1.1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and integrate an automated, high-fidelity media metadata inspection service (Milestone 3.1.1) that inspects ingested surveillance video footage using containerized FFprobe, extracts 5 standardized metadata categories, intelligently selects the primary video stream, normalizes rational frame rates and time bases, persists results to dedicated PostgreSQL inspection tables, and exposes structured REST APIs.

**Architecture:** An asynchronous background inspection worker manages bounded concurrency (max 2 concurrent FFprobe processes) and a 120-second execution timeout. Ingested videos stored in MinIO are staged in ephemeral sandboxes, parsed via FFprobe, normalized through Pydantic 2 models, and stored across `video_inspections` and `video_streams` tables while strictly maintaining separate states for `metadata_status` ("COMPLETED") and `validation_status` ("PENDING").

**Tech Stack:** Python 3.12, FFprobe, FastAPI, Pydantic 2, SQLAlchemy 2 (async), PostgreSQL 16, Alembic, MinIO S3 SDK, Docker, Pytest.

**Spec:** `docs/vigilant-video-preprocessing-design.md`

---

## Global Constraints

- **FFprobe Concurrency Bound**: Unbounded FFprobe processes are prohibited; execution must be constrained to a maximum of 2 concurrent processes via `asyncio.Semaphore(2)`.
- **Subprocess Timeout**: FFprobe execution must enforce a hard 120-second timeout.
- **State Segregation**: `metadata_status = "COMPLETED"` must **never** be conflated with `validation_status = "VALIDATED"`. Media decode validation is deferred to Milestone 3.1.2.
- **Temporary Sandbox Cleanup**: Files downloaded from MinIO for inspection must be strictly deleted (`shutil.rmtree` in `finally` blocks) regardless of extraction success or failure.
- **Stream Assumption Prevention**: The system must not assume stream 0 is the primary video stream; cover art / attached pictures must be discarded during candidate ranking.

---

## Review Focus

1. **Cover Art / Attached Picture Disqualification**: Ensure that MP4 files with embedded poster frames or album art (`attached_pic == 1`) are not selected as the primary video stream.
2. **Missing Frame Count Resilience**: Handle containers (e.g. streaming MKV/MP4) where `nb_frames` is absent or "N/A" without failing normalization.
3. **Rational FPS Evaluation**: Accurately evaluate rational strings (`30000/1001` -> 29.97, `24000/1001` -> 23.976, `25/1` -> 25.0) with zero division protection.
4. **Silent / Non-Audio Feeds**: Gracefully handle silent CCTV surveillance streams where no audio stream is present (`has_audio = False`, null audio fields).
5. **Corrupted File Header Handling**: When encountering invalid or corrupted byte payloads, ensure `metadata_status = "FAILED"`, persist the error message, and prevent unhandled process crashes.

---

## Implementation Tasks

### Task 1: Database Models & Alembic Schema Migration
**Files:**
- Modify: `backend/app/models/video.py`
- Create: `backend/alembic/versions/004_video_inspections_schema.py`
- Test: `backend/tests/test_inspection_models.py`

- [ ] Add `metadata_status` (`EXTRACTING`, `COMPLETED`, `FAILED`) and `validation_status` (`PENDING`, `VALIDATED`, `INVALID`) columns to `Video`.
- [ ] Implement `VideoInspection` model:
  - Stores file and container details (format, duration, bitrate, start time).
  - Stores primary video stream attributes (stream index, codec, resolution, fps, rational fps, pixel format, time base).
  - Stores primary audio stream attributes (has_audio, audio codec, sample rate, channels, channel layout).
  - Stores raw FFprobe output in JSON column `raw_ffprobe_json`.
- [ ] Implement `VideoStream` model:
  - Catalogs every stream in the container with index, type, codec, disposition flags, and metadata.
- [ ] Author Alembic migration `004_video_inspections_schema.py` creating both tables with foreign key cascades.
- [ ] Write unit test in `test_inspection_models.py` verifying model instantiation and relationship cascade.

---

### Task 2: Pydantic Normalization Schemas
**Files:**
- Create: `backend/app/schemas/inspection.py`
- Modify: `backend/app/schemas/video.py`
- Test: `backend/tests/test_inspection_schemas.py`

- [ ] Define `FileInfoSchema` (original filename, size, format, SHA-256, upload timestamp).
- [ ] Define `ContainerInfoSchema` (format name, long name, duration, bitrate, start time, size).
- [ ] Define `VideoStreamInfoSchema` (stream index, codec, dimensions, fps, rational fps, pixel format, time base, duration, reported frame count).
- [ ] Define `AudioStreamInfoSchema` (has audio, codec, sample rate, channels, layout, duration).
- [ ] Define `StreamSummarySchema` (catalog item for each stream).
- [ ] Define `VideoInspectionReportResponse` (composite manifest presenting all 5 categories, extractor version, metadata status, and validation status).
- [ ] Write schema validation tests in `test_inspection_schemas.py`.

---

### Task 3: Stream Selection & Rational Number Normalizer
**Files:**
- Create: `backend/app/services/metadata_normalizer.py`
- Test: `backend/tests/test_metadata_normalizer.py`

- [ ] Implement `parse_rational_number(val: Optional[str]) -> Tuple[Optional[float], Optional[str]]` handling "30000/1001", "25/1", "0/0", and null inputs.
- [ ] Implement `select_primary_video_stream(streams: List[dict]) -> Optional[dict]` filtering out `attached_pic` and prioritizing `disposition.default` and highest pixel area.
- [ ] Implement `select_primary_audio_stream(streams: List[dict]) -> Optional[dict]`.
- [ ] Implement full normalizer converting raw FFprobe dictionary into Pydantic models.
- [ ] Write tests covering edge cases: multiple video streams, MP4 with attached cover picture, audio-less feeds, invalid rational numbers.

---

### Task 4: Media Inspection Worker Service
**Files:**
- Create: `backend/app/services/metadata_extractor.py`
- Modify: `backend/app/core/config.py`
- Test: `backend/tests/test_metadata_extractor.py`

- [ ] Add settings in `config.py`: `MAX_CONCURRENT_INSPECTIONS = 2`, `FFPROBE_TIMEOUT_SECONDS = 120`.
- [ ] Implement `MetadataInspectionService.run_ffprobe(file_path: str) -> dict` with async subprocess and 120s timeout.
- [ ] Implement `MetadataInspectionService.inspect_video(video_id: UUID) -> VideoInspection`:
  - Enforce concurrency semaphore (`asyncio.Semaphore(2)`).
  - Stage object from MinIO to `/tmp/inspection_workspace/{job_id}`.
  - Run FFprobe, normalize telemetry, and persist to `video_inspections` and `video_streams`.
  - Update `Video.metadata_status = "COMPLETED"`, update video summary fields, set `Video.validation_status = "PENDING"`.
  - Clean up temporary files in `finally` block.
- [ ] Handle error states: update `metadata_status = "FAILED"`, save `error_message`, log warnings.
- [ ] Write unit tests mocking MinIO and FFprobe subprocess.

---

### Task 5: FastAPI REST Endpoints
**Files:**
- Modify: `backend/app/api/v1/videos.py`
- Test: `backend/tests/test_inspection_api.py`

- [ ] Implement `GET /api/v1/videos/{video_id}/inspection` returning the structured 5-category inspection report.
- [ ] Implement `POST /api/v1/videos/{video_id}/inspect` triggering on-demand inspection via `BackgroundTasks`.
- [ ] Integrate inspection trigger automatically into `POST /upload/complete` and `POST /live/record`.
- [ ] Write API integration tests verifying response format, authorization, and 404 handling.

---

### Task 6: Frontend Inspection Manifest Modal / Drawer
**Files:**
- Create: `frontend/src/components/video/VideoInspectionDrawer.tsx`
- Modify: `frontend/src/types/video.ts`
- Modify: `frontend/src/services/videoApi.ts`
- Modify: `frontend/src/components/video/VideoPlayerModal.tsx`
- Modify: `frontend/src/components/video/VideoCard.tsx`
- Modify: `frontend/src/components/video/VideoTableView.tsx`

- [ ] Add TypeScript interfaces in `video.ts` for `VideoInspectionReport`, `FileInfo`, `ContainerInfo`, `VideoStreamInfo`, `AudioStreamInfo`.
- [ ] Add `videoApi.getInspectionReport(videoId)` and `videoApi.triggerInspection(videoId)`.
- [ ] Build `VideoInspectionDrawer.tsx` displaying:
  - Status badges: `METADATA EXTRACTED` (emerald) vs `VALIDATION PENDING (3.1.2)` (amber).
  - Tabbed or card layout for the 5 categories (File, Container, Primary Video, Audio, All Streams).
  - Stream disposition badges (`Default`, `Attached Pic`, `Time Base`, `Rational FPS`).
- [ ] Wire the inspection drawer trigger into `VideoPlayerModal` telemetry drawer and `VideoTableView` actions.

---

### Task 7: Containerization & End-to-End Live Verification
**Files:**
- Create: `scripts/test_inspection_pipeline.py`
- Modify: `.agent/progress.md`
- Modify: `docs/DECISIONS.md`

- [ ] Apply Alembic migration inside backend Docker container.
- [ ] Rebuild and launch updated containers (`backend`, `frontend`).
- [ ] Run automated live script `test_inspection_pipeline.py` verifying:
  - Video upload -> automated FFprobe extraction.
  - Multi-stream inspection verification.
  - Verification that `metadata_status == "COMPLETED"` and `validation_status == "PENDING"`.
  - API retrieval of complete 5-category inspection manifest.
- [ ] Update `.agent/progress.md` and add ADR-007 to `docs/DECISIONS.md`.
- [ ] Commit all code and push to `origin/master`.
