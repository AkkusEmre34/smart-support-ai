import sqlite3
from pathlib import Path
from typing import Any


PROJECT_FOLDER = Path(__file__).resolve().parent.parent
DATABASE_FILE = PROJECT_FOLDER / "data" / "smart_support.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row

    return connection


def init_database() -> None:
    DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                category TEXT NOT NULL,
                category_name TEXT NOT NULL,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.commit()


def add_chat(
    chat_id: str,
    question: str,
    answer: str,
    category: str,
    category_name: str
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO chats (
                id,
                question,
                answer,
                category,
                category_name,
                feedback
            )
            VALUES (?, ?, ?, ?, ?, NULL)
            """,
            (
                chat_id,
                question,
                answer,
                category,
                category_name
            )
        )

        connection.commit()


def get_all_chats() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                question,
                answer,
                category,
                category_name,
                feedback,
                created_at
            FROM chats
            ORDER BY created_at ASC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def update_feedback(chat_id: str, feedback: str) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE chats
            SET feedback = ?
            WHERE id = ?
            """,
            (feedback, chat_id)
        )

        connection.commit()

        return cursor.rowcount > 0


def clear_all_chats() -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM chats")
        connection.commit()