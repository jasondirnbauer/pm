# Backend Agent Guide

## Current purpose

This backend currently provides Part 2 scaffold behavior:
- FastAPI application with a modular router structure.
- API smoke endpoints under `/api`.
- Static HTML served from `/` by FastAPI.

## Structure

- `app/main.py`
	- App factory (`create_app`) and global `app`.
	- Registers API router and static route mounting.
- `app/routers/`
	- API route modules.
	- Current endpoints:
		- `GET /api/health`
		- `GET /api/hello`
- `app/static/index.html`
	- Hello-world static page.
	- Calls `/api/hello` in-browser to confirm API connectivity.
- `tests/test_smoke.py`
	- FastAPI TestClient smoke tests for root and API endpoints.

## Dependency management

- Python dependencies are declared in `pyproject.toml`.
- `uv` is used to resolve/install dependencies in container runtime.

## Run expectations

- Containerized run is the primary path:
	- `docker compose up --build`
- Service is exposed at `http://localhost:8000`.

## Notes for next phases

- This scaffold is intentionally minimal.
- Part 3 will replace static hello page with statically built Next.js output.
- Part 4+ will add auth, persistence, and AI endpoints.