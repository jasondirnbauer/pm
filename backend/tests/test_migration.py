import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.board_defaults import default_board
from app.db import get_db_path, init_db
from app.main import create_app


def test_migration_from_old_schema(tmp_path, monkeypatch) -> None:
    from app.routers.auth import sessions
    sessions.clear()

    db_path = tmp_path / "pm.db"
    monkeypatch.setenv("PM_DB_PATH", str(db_path))

    # Create old schema and insert data
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE user_boards (
            username TEXT PRIMARY KEY,
            board_json TEXT NOT NULL CHECK (json_valid(board_json)),
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        )
        """
    )
    board = default_board()
    board["cards"]["card-1"]["title"] = "Migrated Title"
    conn.execute(
        "INSERT INTO user_boards (username, board_json) VALUES (?, ?)",
        ("user", json.dumps(board)),
    )
    conn.commit()
    conn.close()

    # Run init_db which should migrate
    init_db()

    # Verify migration
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "users" in tables
    assert "boards" in tables
    assert "user_boards" not in tables

    user = conn.execute("SELECT * FROM users WHERE username = 'user'").fetchone()
    assert user is not None

    boards = conn.execute("SELECT * FROM boards WHERE user_id = ?", (user["id"],)).fetchall()
    assert len(boards) >= 1
    board_data = json.loads(boards[0]["board_json"])
    assert board_data["cards"]["card-1"]["title"] == "Migrated Title"
    conn.close()

    # Verify login still works
    app = create_app()
    with TestClient(app) as client:
        resp = client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )
        assert resp.status_code == 200

    sessions.clear()


def test_fresh_install_creates_new_schema(tmp_path, monkeypatch) -> None:
    from app.routers.auth import sessions
    sessions.clear()

    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    init_db()

    conn = sqlite3.connect(tmp_path / "pm.db")
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "users" in tables
    assert "boards" in tables
    assert "user_boards" not in tables
    conn.close()

    sessions.clear()


def test_init_db_is_idempotent(tmp_path, monkeypatch) -> None:
    from app.routers.auth import sessions
    sessions.clear()

    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    init_db()
    init_db()  # Should not raise

    conn = sqlite3.connect(tmp_path / "pm.db")
    users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    # Should have exactly one seeded user, not duplicated
    assert users == 1
    conn.close()

    sessions.clear()
