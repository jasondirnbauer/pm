# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Run the app
```bash
docker compose up --build        # Build and start
docker compose down              # Stop
docker compose logs pm-app --tail 200  # View logs
```

### Backend tests (requires running container)
```bash
# On Windows (Git Bash) — MSYS_NO_PATHCONV=1 prevents path mangling
MSYS_NO_PATHCONV=1 docker exec -e PYTHONPATH=/app/backend pm-app /app/backend/.venv/bin/pytest -v
```

### Frontend tests (from `frontend/`)
```bash
npm run test:unit                # Vitest unit tests
npm run test:e2e                 # Playwright E2E tests
npm run test:e2e:integration     # Playwright integration tests
```

### Frontend dev server (from `frontend/`)
```bash
npm install
npm run dev    # Runs on localhost:3000
npm run build  # Static export to out/
```

### Run a single backend test
```bash
MSYS_NO_PATHCONV=1 docker exec -e PYTHONPATH=/app/backend pm-app /app/backend/.venv/bin/pytest tests/test_smoke.py::test_name -v
```

## Architecture

Single Docker container serves everything on port 8000:
- **FastAPI** backend handles API routes (`/api/*`) and serves the Next.js static export at `/`
- **Next.js** (static export, no SSR) is built in a multi-stage Dockerfile and copied into the Python image
- **SQLite** stores one JSON blob per user (`user_boards` table, `pm.db` in `backend/data/`)
- **OpenRouter** (`openai/gpt-oss-120b`) handles AI calls via `backend/app/ai_client.py`

### Request flow

```
Browser -> FastAPI -> SQLite (board data)
                   -> OpenRouter API (AI chat)
```

### Board data model

The entire board is stored as a single JSON blob per user:
```typescript
type BoardData = {
  columns: Column[];           // ordered list
  cards: Record<string, Card>; // keyed by id
};
```
`Column.cardIds` references card IDs in display order. This structure is shared between frontend TypeScript types (`frontend/src/lib/kanban.ts`) and the backend Python dicts.

### AI board action flow

`POST /api/ai/board-action` sends the user message + full board state + conversation history to OpenRouter. The model returns structured JSON with an `assistant_response` (text) and optional `board_update` (new board state). If `board_update` is provided, it's persisted to SQLite and returned to the frontend, which applies it directly.

### Authentication

Session-based with an in-memory token dict on the backend. Hardcoded credentials: `user` / `password`. The frontend's `AuthGate` component checks `GET /api/auth/me` on mount.

## Coding standards (from AGENTS.md)

- Use latest library versions and idiomatic approaches
- Keep it simple: never over-engineer, never add unnecessary defensive programming, no extra features
- No emojis anywhere
- When hitting issues: identify root cause with evidence before fixing — do not guess

## Color scheme

- Accent Yellow: `#ecad0a`
- Blue Primary: `#209dd7`
- Purple Secondary: `#753991` (buttons, important actions)
- Dark Navy: `#032147` (headings)
- Gray: `#888888` (labels, supporting text)

## Key files

- `backend/app/main.py` — FastAPI app factory, static file mounting
- `backend/app/routers/` — auth, board, ai, health endpoints
- `backend/app/ai_client.py` — OpenRouter client
- `backend/app/board_defaults.py` — default board template (5 columns, 8 sample cards)
- `frontend/src/lib/kanban.ts` — board type definitions and utility functions
- `frontend/src/components/KanbanBoard.tsx` — main board state and drag/drop orchestration
- `frontend/src/components/AIChatSidebar.tsx` — AI chat UI
- `docs/PLAN.md` — full MVP execution plan (all 10 steps completed)
