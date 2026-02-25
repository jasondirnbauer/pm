# Project Plan (Detailed MVP Execution)

This document is the execution checklist for the full MVP described in `AGENTS.md`.

Scope assumptions locked in:
- Next.js frontend is statically exported for production serving.
- FastAPI backend serves API and static frontend from `/`.
- Dummy login credentials are fixed to username `user`, password `password`.
- SQLite stores one JSON Kanban board blob per user.
- Docker support includes both single-container (`Dockerfile`) and `docker-compose.yml`.

## Part 1: Plan and Documentation

### Checklist
- [x] Expand this plan into actionable substeps with tests and success criteria.
- [x] Create `frontend/AGENTS.md` documenting existing frontend architecture and behavior.
- [x] User reviews and approves this plan before implementation begins.

### Tests
- [x] Documentation sanity check: files exist, are readable, and align with current repository structure.

### Success criteria
- [x] `docs/PLAN.md` is detailed, sequenced, and test-driven.
- [x] `frontend/AGENTS.md` accurately describes current frontend code.
- [x] Explicit user approval is recorded.

## Part 2: Scaffolding (Docker + FastAPI + Scripts)

### Checklist
- [x] Initialize backend app in `backend/` with FastAPI app factory and router structure.
- [x] Add `pyproject.toml` using `uv` workflow and pinned runtime dependencies.
- [x] Add `Dockerfile` to build frontend static assets and run FastAPI service.
- [x] Add `docker-compose.yml` for local container orchestration.
- [x] Add scripts in `scripts/` for start/stop on Windows, macOS, Linux.
- [x] Implement hello-world static page and hello API endpoint for smoke validation.
- [x] Document local run commands in README updates (minimal).

### Tests
- [x] `docker compose up --build` succeeds.
- [x] GET `/` returns hello-world static response in container.
- [x] GET `/api/health` (or equivalent) returns 200 with JSON payload.
- [x] Start/stop scripts launch and stop containers on each OS path (syntax verified in repo).

### Success criteria
- [x] Local container starts cleanly with one command.
- [x] Static and API routes both reachable.
- [x] No manual setup required beyond `.env` and Docker.

## Part 3: Serve Existing Frontend

### Checklist
- [x] Build frontend with static export configuration.
- [x] Copy exported frontend assets into backend-served static directory in container build.
- [x] Route `/` and static files through FastAPI static mount.
- [x] Keep frontend tests operational in `frontend/`.

### Tests
- [x] Frontend unit tests: `npm run test:unit`.
- [x] Frontend e2e tests: `npm run test:e2e` against served app.
- [x] Container smoke test: `/` shows Kanban board UI.

### Success criteria
- [x] Existing Kanban demo appears at `/` when running containerized app.
- [x] No regression in frontend test suite.

## Part 4: Dummy Sign-In Flow

### Checklist
- [x] Add backend auth endpoint validating `user` / `password`.
- [x] Add simple session mechanism for MVP (cookie-based).
- [x] Protect Kanban page/data behind authenticated session.
- [x] Add logout endpoint and UI logout action.
- [x] Add login UI state in frontend (before board render).

### Tests
- [x] Backend auth tests for valid/invalid credentials.
- [x] Frontend unit tests for login form behavior and error states.
- [x] Integration/e2e: unauthenticated user sees login, authenticated sees board, logout returns to login.

### Success criteria
- [x] Only valid credentials unlock board.
- [x] Session persists across page refresh during runtime.
- [x] Logout fully clears authenticated state.

## Part 5: Database Modeling (JSON Blob per User)

### Checklist
- [ ] Propose SQLite schema with one board JSON blob per user.
- [ ] Document schema, migration/bootstrapping approach, and tradeoffs in `docs/`.
- [ ] Define default-board initialization logic for first login/use.
- [ ] Define constraints and indexes for lookup by username.
- [ ] Obtain user sign-off before backend persistence implementation.

### Tests
- [ ] Schema doc review checklist complete.
- [ ] Local DB initialization creates tables if missing.
- [ ] Insert/read roundtrip validates JSON fidelity.

### Success criteria
- [ ] Schema is simple, explicit, and aligned to MVP requirements.
- [ ] Database behavior is documented and approved before coding Part 6.

## Part 6: Backend Kanban API

### Checklist
- [ ] Implement DB layer and startup init to create DB/tables if absent.
- [ ] Add endpoints to read board and update board for authenticated user.
- [ ] Validate request payload shape and reject malformed board updates.
- [ ] Keep API surface minimal and versionable.

### Tests
- [ ] Backend unit tests for DB init and CRUD operations.
- [ ] API tests for auth-required access, read success, update success, and invalid payload rejection.
- [ ] Persistence test verifying updates survive server restart.

### Success criteria
- [ ] Backend is source of truth for board state.
- [ ] Board updates are persisted per user in SQLite JSON blob.

## Part 7: Frontend + Backend Integration

### Checklist
- [ ] Replace in-memory frontend board state bootstrapping with backend fetch.
- [ ] Persist card/column edits and drag-drop moves through backend API.
- [ ] Handle loading and API error states with minimal UX.
- [ ] Ensure frontend remains static-export compatible.

### Tests
- [ ] Unit tests for API client functions.
- [ ] Component/integration tests with mocked backend responses.
- [ ] E2E tests covering login, board load, edits, refresh persistence.

### Success criteria
- [ ] Board state is persistent and reload-safe.
- [ ] Core interactions (rename/add/delete/move) function end-to-end.

## Part 8: AI Connectivity (OpenRouter)

### Checklist
- [ ] Add backend AI client using OpenRouter with `.env` key.
- [ ] Use model `openai/gpt-oss-120b`.
- [ ] Implement simple diagnostic call path for connectivity checks.
- [ ] Add robust timeout and error mapping for upstream failures.

### Tests
- [ ] Connectivity test prompt `2+2` returns expected semantic result.
- [ ] Missing/invalid API key path returns clear backend error.
- [ ] Network failure path is handled gracefully.

### Success criteria
- [ ] Backend can successfully call OpenRouter in local container runtime.
- [ ] Error paths are deterministic and debuggable.

## Part 9: Structured AI Board Actions

### Checklist
- [ ] Define strict structured output schema (assistant reply + optional board update).
- [ ] Send board JSON + user question + conversation history to backend AI endpoint.
- [ ] Validate AI structured output before applying any board mutation.
- [ ] Persist approved board updates and return updated state.

### Tests
- [ ] Schema validation tests for valid/invalid AI outputs.
- [ ] Backend tests ensuring optional board update applies only when valid.
- [ ] Conversation-history tests confirming prior turns are included.

### Success criteria
- [ ] AI responses are machine-parseable and safe to apply.
- [ ] Board mutation happens only through validated structured output.

## Part 10: Frontend AI Sidebar

### Checklist
- [ ] Add sidebar chat UI with message history and input.
- [ ] Wire chat UI to backend AI endpoint.
- [ ] Apply returned board updates to UI immediately after successful response.
- [ ] Keep UX simple and aligned with existing design tokens/colors.

### Tests
- [ ] Component tests for chat rendering, submit, loading, and error states.
- [ ] Integration tests for board refresh after AI update.
- [ ] E2E test: user sends message, receives reply, board updates when instructed.

### Success criteria
- [ ] Sidebar supports full roundtrip chat.
- [ ] Valid AI-issued updates are reflected without manual reload.
- [ ] Existing Kanban interactions continue to work.

## Cross-cutting Definition of Done

For each completed part:
- [ ] Relevant tests pass locally.
- [ ] Minimal docs are updated in `docs/` and/or project README files.
- [ ] No unrelated refactors or scope expansion were introduced.
- [ ] Root-cause evidence is captured for any bug fix.

## Approval Gates

- [x] Gate A (required): Approve this plan before Part 2 starts.
- [ ] Gate B (required): Approve database approach docs before Part 6 starts.