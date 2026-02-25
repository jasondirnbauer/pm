# Backend Agent Guide

## Current purpose

This backend currently provides Part 3 behavior:
- FastAPI application with a modular router structure.
- API smoke endpoints under `/api`.
- Cookie-session auth endpoints under `/api/auth`.
- Exported Next.js frontend served from `/`.
- Fallback static smoke page for non-container local resilience.

## Structure

- `app/main.py`
	- App factory (`create_app`) and global `app`.
	- Registers API router and mounts static frontend at `/`.
- `app/routers/`
	- API route modules.
	- Current endpoints:
		- `POST /api/auth/login`
		- `GET /api/auth/me`
		- `POST /api/auth/logout`
		- `GET /api/health`
		- `GET /api/hello`
- `app/frontend_static/` (container runtime)
	- Populated from Next.js `frontend/out` at image build time.
- `app/static/index.html`
	- Kept as fallback smoke page when exported frontend is not present.
- `tests/test_smoke.py`
	- FastAPI TestClient smoke tests for root, auth, and API endpoints.

## Dependency management

- Python dependencies are declared in `pyproject.toml`.
- `uv` is used to resolve/install dependencies in container runtime.

## Run expectations

- Containerized run is the primary path:
	- `docker compose up --build`
- Service is exposed at `http://localhost:8000`.

## Notes for next phases

- Part 3 integration is complete via Docker multi-stage build.
- Part 4+ will add auth, persistence, and AI endpoints.