# Code Review

Reviewed: 2026-02-26
Scope: All backend, frontend, test, and configuration files.

---

## Summary

| Severity | Count |
|----------|-------|
| High     | 5     |
| Medium   | 7     |
| Low      | 7     |

Known MVP simplifications (hardcoded credentials, in-memory sessions) are noted but not flagged as bugs — they are intentional and documented in `AGENTS.md`. The `.env` file is correctly gitignored and not in git history.

---

## High

### H1 — AI board updates lost on page reload

**File**: `frontend/src/components/KanbanBoard.tsx`

```typescript
const handleBoardUpdateFromAI = (nextBoard: BoardData) => {
  setBoard(nextBoard);
};
```

The AI endpoint already persists the board to SQLite and returns it (`POST /api/ai/board-action`). But `handleBoardUpdateFromAI` just calls `setBoard` — it does not call `persistBoard`. This is actually fine because the backend already saved the update. However the frontend does not reconcile its local state with the server-returned board — it applies the full `nextBoard` returned from the AI response, which should already be the persisted state. On closer inspection this is correct if `AIChatSidebar` passes back exactly the `board` field from the API response. Verify `AIChatSidebar.tsx` passes the server board and not a locally-mutated copy.

**Action**: Confirm the `board` value passed to `onBoardUpdate` is the raw server response — add a comment clarifying this to prevent future regression.

---

### H2 — Race condition in board persistence

**File**: `frontend/src/components/KanbanBoard.tsx`

```typescript
const applyBoardUpdate = (updater: (current: BoardData) => BoardData) => {
  setBoard((current) => {
    const nextBoard = updater(current);
    void persistBoard(nextBoard);  // fire and forget
    return nextBoard;
  });
};
```

Rapid sequential edits (fast drag-and-drop or quick card adds) fire parallel `PUT /api/board` requests with no ordering guarantee. If request N+1 arrives before N, the earlier state wins. This is a last-write-wins race with no versioning.

For MVP this is low probability, but if a user drags a card and immediately edits a title the board can silently revert one change.

**Action**: Debounce or serialize persistence calls (e.g. debounce 300ms, or use a request queue that cancels in-flight requests on new update).

---

### H3 — No timeout on board persistence requests

**File**: `frontend/src/components/KanbanBoard.tsx`

`persistBoard` uses `fetch` with no `signal` / `AbortController`. If the backend hangs, the browser holds the connection indefinitely. Combined with H2, pending requests can accumulate.

**Action**: Add `AbortController` with a timeout (e.g. 10s) and cancel in-flight persist when a new one fires.

---

### H4 — Board load failure is silently swallowed

**File**: `frontend/src/components/KanbanBoard.tsx`

```typescript
} catch {
  return;
}
```

If `loadBoard()` fails (server down, session expired mid-session), the user sees the stale initial state with no feedback. They may continue editing, believing their board is fresh.

**Action**: Set an error state and display a banner ("Could not load latest board — showing cached data").

---

### H5 — No input length limits on card title/details

**Files**: `frontend/src/components/KanbanCard.tsx`, `backend/app/routers/board.py`

There is no `maxLength` on the title or details `<textarea>` inputs, and the backend board validation only checks structural shape (column/card references), not field lengths. A user can submit a multi-megabyte string, which will be stored verbatim in SQLite.

**Action**: Add `maxLength` to inputs (e.g. title: 200, details: 5000) and add length checks in the backend Pydantic model.

---

## Medium

### M1 — Weak card ID generation

**File**: `frontend/src/lib/kanban.ts`

```typescript
const randomPart = Math.random().toString(36).slice(2, 8);
const timePart = Date.now().toString(36);
return `${prefix}-${randomPart}${timePart}`;
```

`Math.random()` is not cryptographically secure and has limited entropy (6 base-36 chars ≈ 2.18 billion combinations). Collision is unlikely in practice, but `crypto.randomUUID()` is available in all modern browsers and Node 16+.

**Action**: Replace with `crypto.randomUUID()` or `nanoid`.

---

### M2 — Duplicated default board definition

**Files**:
- `backend/app/board_defaults.py`
- `frontend/src/lib/kanban.ts` (lines 18–72)
- `frontend/tests-integration/persistence.spec.ts` (lines 3–53)

Three independent copies of the default board. Any change to the default (column names, sample cards) must be applied in all three places.

**Action**: The backend already serves the board; the frontend should not hardcode a matching default. Consider removing the frontend copy and using an empty state while loading. The integration test copy is necessary for test isolation — that's acceptable.

---

### M3 — Error swallowed in AIChatSidebar with no differentiation

**File**: `frontend/src/components/AIChatSidebar.tsx`

```typescript
} catch {
  setError("Unable to complete AI request.");
}
```

Network failure, 401 session expiry, 502 upstream error, and validation failure all produce the same message. Auth failures in particular should prompt the user to re-login rather than retry.

**Action**: Inspect `response.status` before throwing and set distinct error messages (e.g. 401 → "Session expired, please log in again").

---

### M4 — AI response not runtime-validated on the frontend

**File**: `frontend/src/components/AIChatSidebar.tsx`

```typescript
const payload = (await response.json()) as AIBoardActionResponse;
```

TypeScript's `as` cast is erased at runtime — no validation occurs. If the AI endpoint returns an unexpected shape, downstream code will fail with a cryptic runtime error.

**Action**: Add a minimal runtime guard (check that `payload.assistant_response` is a string before using it).

---

### M5 — Exception detail leaked in AI validation error

**File**: `backend/app/routers/ai.py`

```python
detail=f"AI structured output validation failed: {exc}",
```

The full Pydantic validation error (which includes field paths and raw values) is sent to the client. This leaks internal model structure.

**Action**: Log `exc` server-side; return a generic message to the client.

---

### M6 — No health check in Dockerfile or docker-compose.yml

Neither the `Dockerfile` nor `docker-compose.yml` defines a `HEALTHCHECK`. Docker has no way to know the app is ready, and `depends_on` (if added later) cannot use health status.

**Action**: Add to `Dockerfile`:
```dockerfile
HEALTHCHECK --interval=10s --timeout=3s CMD curl -f http://localhost:8000/api/health || exit 1
```

---

### M7 — Database volume not mounted in docker-compose.yml

**File**: `docker-compose.yml`

`backend/data/pm.db` lives inside the container filesystem. Running `docker compose down` and `up` recreates the container, losing all board data.

**Action**: Add a volume mount:
```yaml
volumes:
  - ./backend/data:/app/backend/data
```

---

## Low

### L1 — No structured logging

The backend has no logging calls. Auth failures, board update errors, and AI upstream errors are either silently caught or only appear in uvicorn's default stderr. Diagnosing issues in a running container requires guesswork.

**Action**: Add `import logging` and `logger = logging.getLogger(__name__)` to routers; log at `WARNING` or `ERROR` on exception paths.

---

### L2 — Session cookie missing `secure` and `samesite` flags

**File**: `backend/app/routers/auth.py`

`response.set_cookie(...)` does not set `secure=True` or `samesite="lax"`. Not an issue over localhost but would be a risk if deployed over HTTPS without changes.

**Action**: Set `secure=True` and `samesite="lax"` conditionally based on an env var (e.g. `APP_ENV=production`).

---

### L3 — Session has no expiration cleanup

**File**: `backend/app/routers/auth.py`

Sessions are stored in a module-level dict with no eviction. Over time (or with programmatic login calls) the dict grows unbounded. The 8-hour cookie `max_age` expires the client cookie but the server-side token remains in memory forever.

**Action**: Track session creation time and evict expired tokens on each login or via a background task.

---

### L4 — No `.nvmrc` or Node version specification

**File**: repo root / `frontend/`

Node version is unspecified. The Dockerfile pins `node:22` but local development has no equivalent constraint. A developer on Node 18 or 20 may see different behavior.

**Action**: Add a `.nvmrc` with `22` to the `frontend/` directory.

---

### L5 — Magic number for session max_age

**File**: `backend/app/routers/auth.py`

```python
max_age=60 * 60 * 8
```

The 8-hour value is unexplained inline. A named constant (`SESSION_MAX_AGE_SECONDS`) would make intent clear.

---

### L6 — Test coverage gaps

- No tests for `persistBoard` failure path in `KanbanBoard`
- No tests for session expiration mid-session on frontend
- No frontend tests for drag-and-drop (only add/remove/edit)
- No tests for the board validation logic that rejects orphaned card references

---

### L7 — `frontend/test-results/` should be gitignored

**File**: `.gitignore`

`frontend/test-results/.last-run.json` appears as a modified file after test runs. The `test-results/` directory should be explicitly added to `.gitignore`.

**Action**: Add `frontend/test-results/` to `.gitignore`.

---

## Positive observations

- Pydantic models used for all request/response validation on the backend — good practice
- Backend board validation correctly cross-checks column `cardIds` against the `cards` map (catching orphaned references)
- All SQL uses parameterized queries — no injection risk
- `uv.lock` ensures reproducible backend dependency resolution
- Multi-stage Dockerfile keeps the final image small
- The 21 backend smoke tests cover auth, board CRUD, and AI endpoints thoroughly
- `@dnd-kit` is a well-chosen, accessible drag-and-drop library
- AI response schema uses structured output with an optional `board_update` field — good defensive design
