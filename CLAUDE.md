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
MSYS_NO_PATHCONV=1 docker exec -e PYTHONPATH=/app/backend pm-app /app/backend/.venv/bin/pytest tests/test_auth.py::test_name -v
```

## Architecture

Single Docker container serves everything on port 8000:
- **FastAPI** backend handles API routes (`/api/*`) and serves the Next.js static export at `/`
- **Next.js** (static export, no SSR) is built in a multi-stage Dockerfile and copied into the Python image
- **SQLite** with `users` and `boards` tables (`pm.db` in `backend/data/`)
- **OpenRouter** (`openai/gpt-oss-120b`) handles AI calls via `backend/app/ai_client.py`

### Database schema

```sql
users (id INTEGER PK, username TEXT UNIQUE, password_hash TEXT, display_name TEXT, created_at, updated_at)
boards (id TEXT PK, user_id INTEGER FK->users, name TEXT, board_json TEXT, created_at, updated_at)
```

Each board stores its full state as a JSON blob. Multiple boards per user.

### Request flow

```
Browser -> FastAPI -> SQLite (user + board data)
                   -> OpenRouter API (AI chat)
```

### Board data model

```typescript
type Card = {
  id: string; title: string; details: string;
  labels?: { id: string; text: string; color: string }[];
  due_date?: string | null;
  priority?: "none" | "low" | "medium" | "high" | "urgent";
};
type Column = { id: string; title: string; cardIds: string[] };
type BoardData = { columns: Column[]; cards: Record<string, Card> };
```

### API endpoints

**Auth:** `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`, `PUT /api/auth/me`, `PUT /api/auth/password`

**Boards:** `GET /api/boards`, `POST /api/boards`, `GET /api/boards/{id}`, `PUT /api/boards/{id}`, `PATCH /api/boards/{id}`, `DELETE /api/boards/{id}`

**Legacy:** `GET /api/board`, `PUT /api/board` (operate on user's first board)

**AI:** `POST /api/ai/connectivity`, `POST /api/ai/board-action` (accepts optional `board_id`)

### Authentication

Session-based with bcrypt password hashing. In-memory token dict maps session cookies to user info. Registration creates a default board automatically. A seeded `user`/`password` account exists for dev convenience.

### AI board action flow

`POST /api/ai/board-action` sends the user message + full board state + conversation history to OpenRouter. The model returns structured JSON with an `assistant_response` (text) and optional `board_update` (new board state). If `board_update` is provided, it's persisted to SQLite and returned to the frontend, which applies it directly.

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

## Test structure

**Backend** (51 tests across 5 files):
- `tests/conftest.py` — shared fixtures (isolated DB, auth helpers)
- `tests/test_health.py` — health/hello endpoints
- `tests/test_auth.py` — registration, login, logout, profile, password change
- `tests/test_boards.py` — board CRUD, multi-board, ownership, enhanced cards, backward compat
- `tests/test_ai.py` — AI connectivity, board actions with board_id
- `tests/test_migration.py` — schema migration from old format

**Frontend** (20 unit tests, 7 E2E tests):
- `src/lib/kanban.test.ts` — moveCard utility
- `src/components/AuthGate.test.tsx` — login, registration, error handling
- `src/components/KanbanBoard.test.tsx` — columns, cards, editing
- `src/components/AIChatSidebar.test.tsx` — chat, board updates, board_id
- `src/components/BoardSelector.test.tsx` — tabs, create, rename, delete
- `tests/kanban.spec.ts` — E2E: login, cards, drag-drop, AI, registration, board selector

## Key files

- `backend/app/main.py` — FastAPI app factory, static file mounting
- `backend/app/db.py` — SQLite schema, migration, user + board CRUD
- `backend/app/routers/auth.py` — registration, login, SessionUser, profile
- `backend/app/routers/board.py` — board CRUD endpoints, legacy endpoints, card validation
- `backend/app/routers/ai.py` — AI connectivity and board-action with board_id
- `backend/app/ai_client.py` — OpenRouter client
- `backend/app/board_defaults.py` — default board template (5 columns, 8 sample cards)
- `frontend/src/lib/kanban.ts` — board types (Card with labels/priority/due_date), utilities
- `frontend/src/lib/api.ts` — centralized API client
- `frontend/src/components/AuthGate.tsx` — login/registration UI
- `frontend/src/components/BoardSelector.tsx` — multi-board tab selector
- `frontend/src/components/KanbanBoard.tsx` — main board state, multi-board, drag/drop
- `frontend/src/components/KanbanCard.tsx` — card display with labels, priority, due date
- `frontend/src/components/AIChatSidebar.tsx` — AI chat with board_id support
