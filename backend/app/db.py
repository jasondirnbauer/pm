import json
import os
import sqlite3
from pathlib import Path

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
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_boards (
                username TEXT PRIMARY KEY,
                board_json TEXT NOT NULL CHECK (json_valid(board_json)),
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )
            """
        )


def get_or_create_board(username: str) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT board_json FROM user_boards WHERE username = ?",
            (username,),
        ).fetchone()

        if row:
            return json.loads(row["board_json"])

        board = default_board()
        connection.execute(
            "INSERT INTO user_boards (username, board_json) VALUES (?, ?)",
            (username, json.dumps(board)),
        )
        return board


def update_board(username: str, board: dict) -> dict:
    board_json = json.dumps(board)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO user_boards (username, board_json)
            VALUES (?, ?)
            ON CONFLICT(username) DO UPDATE SET
                board_json = excluded.board_json,
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            """,
            (username, board_json),
        )

    return board
