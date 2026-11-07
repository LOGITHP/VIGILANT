# VIGILANT Documentation Hub

Welcome to the technical documentation repository for **VIGILANT**, an enterprise-grade AI-powered CCTV surveillance and computer vision intelligence system.

This directory contains the system specifications, architecture blueprints, implementation plans, and architecture decision records (ADRs) designed to guide development across all project phases.

---

## Documentation Index

### 1. Specifications & Architecture
- **[Authentication & Dashboard Specification](vigilant-auth-design.md)**
  - Comprehensive architectural design of the authentication service, PostgreSQL schema, RBAC role matrix, session revocation, and surveillance UI layout.
- **[Video Upload, Storage & Playback Specification](vigilant-video-pipeline-design.md)**
  - Technical design of the chunked upload ingestion protocol, MinIO S3 object storage, FFprobe media telemetry extraction, FFmpeg thumbnail generation, and HTTP 206 range streaming proxy.
- **[Video Preprocessing: FFprobe Metadata Extractor](vigilant-video-preprocessing-design.md)**
  - Architectural blueprint for Milestone 3.1.1: 5-category container and stream inspection, primary stream selection, metadata normalization, bounded concurrency, and inspection report schemas.

### 2. Implementation Plans & Workflows
- **[Phase 1 Implementation Plan](vigilant-auth-plan.md)**
  - Bite-sized execution tasks covering backend scaffolding, Argon2id/JWT cryptography, Alembic migrations, ephemeral seed automation, Docker Compose topology, and React frontend matching Reference 1.
- **[Phase 2 Implementation Plan: Video Pipeline](vigilant-video-pipeline-plan.md)**
  - Step-by-step TDD execution plan for MinIO containerization, chunk assembly, FFprobe/FFmpeg worker, video REST endpoints, React upload center, video library, and surveillance theater player.
- **[Phase 3.1.1 Implementation Plan: FFprobe Metadata Extractor](vigilant-video-preprocessing-plan.md)**
  - Detailed task breakdown for database inspection models, Pydantic normalizers, primary stream selector, bounded media inspection service, and frontend inspection drawer.

### 3. Decisions & Standards
- **[Architecture Decision Records (ADRs)](DECISIONS.md)**
  - **ADR-001**: Authentication architecture, Argon2id hashing parameters, and dual-token JWT lifecycle.
  - **ADR-002**: Ephemeral database bootstrap seed with automatic self-wipeout.
  - **ADR-003**: UI/UX visual fidelity and surveillance styling.

---

## System Architecture Diagram

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
     |     Password Verification   | |   Access & Refresh Tokens   |
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

## Security & Credentials Summary

| Role | Default Email | Password | Provisioning | Wipeout Policy |
| :--- | :--- | :--- | :--- | :--- |
| **Super Admin** | `cctv@gmail.com` | `123456789` | First-run container boot | Seed script wiped immediately from filesystem |
| **Operator** | *Configured by Admin* | *Hashed via Argon2id* | Admin invitation / API | N/A |
| **Viewer** | *Configured by Admin* | *Hashed via Argon2id* | Self-registration / Admin | N/A |

---

## Upcoming Architectural Sections
- **Phase 2:** RTSP/ONVIF Camera Stream Ingestion & WebRTC Low-Latency Live Streaming.
- **Phase 3:** Computer Vision & AI Inference Engine (YOLOv8 / RT-DETR object detection, intrusion zone trips, facial intelligence).
- **Phase 4:** Event Alerting, Webhook Notifications, and Historical Playback Storage.

