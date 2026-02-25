# Backend Agent Guide

## Current purpose

This backend currently provides Part 6 behavior:
- FastAPI application with a modular router structure.
- API smoke endpoints under `/api`.
- Cookie-session auth endpoints under `/api/auth`.
- SQLite-backed board persistence via `/api/board`.
- OpenRouter connectivity endpoint via `/api/ai/connectivity`.
- Exported Next.js frontend served from `/`.
- Fallback static smoke page for non-container local resilience.

## Structure

- `app/main.py`
	- App factory (`create_app`) and global `app`.
	- Initializes SQLite schema on startup.
	- Registers API router and mounts static frontend at `/`.
- `app/db.py`
	- DB path resolution (`PM_DB_PATH` override support).
	- SQLite schema initialization.
	- Per-user board read/create and update helpers.
- `app/ai_client.py`
	- OpenRouter client wrapper for model `openai/gpt-oss-120b`.
	- Handles configuration, timeout, and upstream error mapping.
- `app/board_defaults.py`
	- Default board payload used for first-time user initialization.
- `app/routers/`
	- API route modules.
	- Current endpoints:
		- `POST /api/auth/login`
		- `GET /api/auth/me`
		- `POST /api/auth/logout`
		- `GET /api/board`
		- `PUT /api/board`
		- `POST /api/ai/connectivity`
		- `GET /api/health`
		- `GET /api/hello`
- `app/frontend_static/` (container runtime)
	- Populated from Next.js `frontend/out` at image build time.
- `app/static/index.html`
	- Kept as fallback smoke page when exported frontend is not present.
- `tests/test_smoke.py`
	- FastAPI TestClient coverage for root, auth, board persistence, and API endpoints.

## Dependency management

- Python dependencies are declared in `pyproject.toml`.
- `uv` is used to resolve/install dependencies in container runtime.

## Run expectations

- Containerized run is the primary path:
	- `docker compose up --build`
- Service is exposed at `http://localhost:8000`.

## Notes for next phases

- Part 3 integration is complete via Docker multi-stage build.
- Part 4 auth and Part 6 board persistence are complete.
- Next phases add frontend/backend board integration and AI functionality.