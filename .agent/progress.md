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
- [ ] Task 1: MinIO Storage Infrastructure & Backend Dependencies
- [ ] Task 2: Database Models & Alembic Migration for Video Archive
- [ ] Task 3: MinIO Storage Service & Chunk Assembly Engine
- [ ] Task 4: Media Telemetry (FFprobe) & Thumbnail Generation (FFmpeg)
- [ ] Task 5: Video REST API Endpoints (Upload, Library, Range Streaming)
- [ ] Task 6: Frontend Video Types & Resumable Chunk Upload Engine
- [ ] Task 7: Frontend Video Upload Center UI
- [ ] Task 8: Frontend Surveillance Video Library UI (Grid & Table Views)
- [ ] Task 9: Frontend Surveillance Video Player Modal
- [ ] Task 10: Integrated Top Navigation & Main View Integration
- [ ] Task 11: End-to-End Containerization, Testing & Documentation


