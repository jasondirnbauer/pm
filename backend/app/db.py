import json
import os
import sqlite3
import uuid
from pathlib import Path

import bcrypt

from app.board_defaults import default_board


def get_db_path() -> Path:
    configured_path = os.getenv("PM_DB_PATH")
    if configured_path:
        return Path(configured_path)

    return Path(__file__).parent.parent / "data" / "pm.db"


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with get_connection() as connection:
        _migrate_if_needed(connection)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS boards (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL DEFAULT 'My Board',
                board_json TEXT NOT NULL CHECK (json_valid(board_json)),
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id)"
        )
        _seed_default_user(connection)


def _migrate_if_needed(connection: sqlite3.Connection) -> None:
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "user_boards" not in tables or "users" in tables:
        return

    # Old schema exists and new schema doesn't — migrate
    connection.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE boards (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL DEFAULT 'My Board',
            board_json TEXT NOT NULL CHECK (json_valid(board_json)),
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    rows = connection.execute(
        "SELECT username, board_json, created_at, updated_at FROM user_boards"
    ).fetchall()

    for row in rows:
        password_hash = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode()
        connection.execute(
            "INSERT INTO users (username, password_hash, display_name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (row["username"], password_hash, row["username"], row["created_at"], row["updated_at"]),
        )
        user = connection.execute(
            "SELECT id FROM users WHERE username = ?", (row["username"],)
        ).fetchone()
        board_id = f"board-{uuid.uuid4()}"
        connection.execute(
            "INSERT INTO boards (id, user_id, name, board_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (board_id, user["id"], "My Board", row["board_json"], row["created_at"], row["updated_at"]),
        )

    connection.execute("DROP TABLE user_boards")


def _seed_default_user(connection: sqlite3.Connection) -> None:
    existing = connection.execute(
        "SELECT id FROM users WHERE username = 'user'"
    ).fetchone()
    if existing:
        return

    password_hash = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode()
    connection.execute(
        "INSERT INTO users (username, password_hash, display_name) VALUES (?, ?, ?)",
        ("user", password_hash, "Default User"),
    )
    user = connection.execute(
        "SELECT id FROM users WHERE username = 'user'"
    ).fetchone()
    board_id = f"board-{uuid.uuid4()}"
    board = default_board()
    connection.execute(
        "INSERT INTO boards (id, user_id, name, board_json) VALUES (?, ?, ?, ?)",
        (board_id, user["id"], "My Board", json.dumps(board)),
    )


# ── User operations ──────────────────────────────────────────────────────


def create_user(username: str, password_hash: str, display_name: str = "") -> dict:
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO users (username, password_hash, display_name) VALUES (?, ?, ?)",
            (username, password_hash, display_name),
        )
        row = connection.execute(
            "SELECT id, username, display_name FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return dict(row)


def get_user_by_username(username: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, username, password_hash, display_name FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, username, display_name FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def update_user_display_name(user_id: int, display_name: str) -> dict:
    with get_connection() as connection:
        connection.execute(
            "UPDATE users SET display_name = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = ?",
            (display_name, user_id),
        )
        row = connection.execute(
            "SELECT id, username, display_name FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row)


def update_user_password(user_id: int, password_hash: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE users SET password_hash = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = ?",
            (password_hash, user_id),
        )


# ── Board operations ─────────────────────────────────────────────────────


def create_board(user_id: int, name: str, board_json: dict | None = None) -> dict:
    board_id = f"board-{uuid.uuid4()}"
    data = board_json if board_json is not None else default_board()
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO boards (id, user_id, name, board_json) VALUES (?, ?, ?, ?)",
            (board_id, user_id, name, json.dumps(data)),
        )
        row = connection.execute(
            "SELECT id, name, board_json, created_at, updated_at FROM boards WHERE id = ?",
            (board_id,),
        ).fetchone()
        result = dict(row)
        result["board_json"] = json.loads(result["board_json"])
        return result


def get_boards_for_user(user_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, name, created_at, updated_at FROM boards WHERE user_id = ? ORDER BY created_at",
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_board(board_id: str, user_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, name, board_json, created_at, updated_at FROM boards WHERE id = ? AND user_id = ?",
            (board_id, user_id),
        ).fetchone()
        if not row:
            return None
        result = dict(row)
        result["board_json"] = json.loads(result["board_json"])
        return result


def update_board(board_id: str, user_id: int, board_json: dict) -> dict:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE boards SET
                board_json = ?,
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE id = ? AND user_id = ?
            """,
            (json.dumps(board_json), board_id, user_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("Board not found")
        row = connection.execute(
            "SELECT id, name, board_json, created_at, updated_at FROM boards WHERE id = ?",
            (board_id,),
        ).fetchone()
        result = dict(row)
        result["board_json"] = json.loads(result["board_json"])
        return result


def rename_board(board_id: str, user_id: int, name: str) -> dict:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE boards SET
                name = ?,
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE id = ? AND user_id = ?
            """,
            (name, board_id, user_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("Board not found")
        row = connection.execute(
            "SELECT id, name, created_at, updated_at FROM boards WHERE id = ?",
            (board_id,),
        ).fetchone()
        return dict(row)


def delete_board(board_id: str, user_id: int) -> bool:
    with get_connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) as cnt FROM boards WHERE user_id = ?",
            (user_id,),
        ).fetchone()["cnt"]
        if count <= 1:
            raise ValueError("Cannot delete the only board")

        cursor = connection.execute(
            "DELETE FROM boards WHERE id = ? AND user_id = ?",
            (board_id, user_id),
        )
        return cursor.rowcount > 0


def get_default_board_for_user(user_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, name, board_json, created_at, updated_at FROM boards WHERE user_id = ? ORDER BY created_at LIMIT 1",
            (user_id,),
        ).fetchone()
        if not row:
            # Create a default board if none exists
            return create_board(user_id, "My Board")
        result = dict(row)
        result["board_json"] = json.loads(result["board_json"])
        return result


# ── Legacy compatibility ─────────────────────────────────────────────────


def get_or_create_board(username: str) -> dict:
    """Legacy function for backward compatibility. Returns board_json dict."""
    user = get_user_by_username(username)
    if not user:
        raise ValueError(f"User not found: {username}")
    board = get_default_board_for_user(user["id"])
    return board["board_json"]
