# Database Approach (Step 5)

This document defines the MVP persistence model for Kanban data.

## Goals

- Support multiple users in the database.
- Store exactly one board per user for MVP.
- Keep persistence simple: one JSON board blob per user.
- Create the database automatically if it does not exist.

## SQLite file

- File path (planned): `backend/data/pm.db`
- Engine: SQLite

## Schema

```sql
CREATE TABLE IF NOT EXISTS user_boards (
  username TEXT PRIMARY KEY,
  board_json TEXT NOT NULL CHECK (json_valid(board_json)),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
```

## Data model details

- `username`
  - Unique user identifier.
  - Maps directly to signed-in username.
- `board_json`
  - Full board snapshot as JSON text.
  - Shape mirrors frontend `BoardData` (`columns`, `cards`).
- `created_at`, `updated_at`
  - UTC timestamps for auditing and debugging.

## Default-board initialization

On first successful authenticated access to board APIs:

1. Query `user_boards` by `username`.
2. If row exists, return stored `board_json`.
3. If row does not exist, insert row with default board JSON.
4. Return inserted board.

Planned insert behavior:

```sql
INSERT INTO user_boards (username, board_json)
VALUES (?, ?)
ON CONFLICT(username) DO NOTHING;
```

## Read and write pattern

- Read board:

```sql
SELECT board_json FROM user_boards WHERE username = ?;
```

- Update board:

```sql
UPDATE user_boards
SET board_json = ?,
    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
WHERE username = ?;
```

## Constraints and indexes

- Primary key on `username` guarantees one board row per user.
- `json_valid` check prevents malformed JSON writes.
- No additional index is required for MVP because all lookups are by `username`.

## Tradeoffs

Benefits:
- Minimal schema and low implementation complexity.
- Easy round-trip with frontend board shape.
- Fast enough for local MVP usage.

Limitations:
- No partial updates at SQL level; full JSON blob write on each change.
- Limited queryability over individual cards/columns.
- Concurrency control is basic (last write wins) for MVP.

## Migration note (post-MVP)

If needed later, this can be normalized into separate tables (`boards`, `columns`, `cards`) without changing auth/session design.

## Step 5 decision summary

- Approved target: **one JSON board blob per user**.
- This schema is the baseline for Step 6 backend persistence APIs.