import sqlite3
from pathlib import Path
from typing import Any, Optional


PROJECT_FOLDER = Path(__file__).resolve().parent.parent

DATABASE_FILE = (
    PROJECT_FOLDER
    / "data"
    / "smart_support.db"
)


def get_connection() -> sqlite3.Connection:
    """
    SQLite veritabanı bağlantısını oluşturur.
    """

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    connection.row_factory = sqlite3.Row

    return connection


def column_exists(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str
) -> bool:
    """
    Belirtilen sütunun tabloda bulunup
    bulunmadığını kontrol eder.
    """

    rows = connection.execute(
        "PRAGMA table_info({})".format(
            table_name
        )
    ).fetchall()

    return any(
        row["name"] == column_name
        for row in rows
    )


def add_missing_columns(
    connection: sqlite3.Connection
) -> None:
    """
    Eski veritabanına sonradan eklenen
    sütunları güvenli şekilde ekler.
    """

    columns = {
        "confidence_score": "INTEGER DEFAULT 0",
        "confidence_level": "TEXT",
        "matched_question": "TEXT",
        "suggestion": "TEXT",
        "match_type": "TEXT",
        "rating": "INTEGER"
    }

    for column_name, column_definition in columns.items():

        if not column_exists(
            connection,
            "chats",
            column_name
        ):

            connection.execute(
                """
                ALTER TABLE chats
                ADD COLUMN {} {}
                """.format(
                    column_name,
                    column_definition
                )
            )


def init_database() -> None:
    """
    Sohbet tablosunu oluşturur ve eski
    veritabanındaki eksik sütunları ekler.
    """

    DATABASE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

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
                rating INTEGER,
                confidence_score INTEGER DEFAULT 0,
                confidence_level TEXT,
                matched_question TEXT,
                suggestion TEXT,
                match_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        add_missing_columns(
            connection
        )

        connection.commit()


def add_chat(
    chat_id: str,
    question: str,
    answer: str,
    category: str,
    category_name: str,
    confidence_score: int = 0,
    confidence_level: str = "Yetersiz",
    matched_question: Optional[str] = None,
    suggestion: Optional[str] = None,
    match_type: str = "not_found"
) -> None:
    """
    Kullanıcı sorusunu ve yapay zekâ
    cevabını veritabanına kaydeder.
    """

    with get_connection() as connection:

        connection.execute(
            """
            INSERT INTO chats (
                id,
                question,
                answer,
                category,
                category_name,
                feedback,
                rating,
                confidence_score,
                confidence_level,
                matched_question,
                suggestion,
                match_type
            )
            VALUES (
                ?,
                ?,
                ?,
                ?,
                ?,
                NULL,
                NULL,
                ?,
                ?,
                ?,
                ?,
                ?
            )
            """,
            (
                chat_id,
                question,
                answer,
                category,
                category_name,
                confidence_score,
                confidence_level,
                matched_question,
                suggestion,
                match_type
            )
        )

        connection.commit()


def get_all_chats() -> list[dict[str, Any]]:
    """
    Bütün sohbet kayıtlarını tarih
    sırasına göre getirir.
    """

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
                rating,
                confidence_score,
                confidence_level,
                matched_question,
                suggestion,
                match_type,
                created_at
            FROM chats
            ORDER BY created_at ASC
            """
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def get_chat_by_id(
    chat_id: str
) -> Optional[dict[str, Any]]:
    """
    Belirtilen kimliğe sahip sohbet
    kaydını getirir.
    """

    with get_connection() as connection:

        row = connection.execute(
            """
            SELECT
                id,
                question,
                answer,
                category,
                category_name,
                feedback,
                rating,
                confidence_score,
                confidence_level,
                matched_question,
                suggestion,
                match_type,
                created_at
            FROM chats
            WHERE id = ?
            """,
            (
                chat_id,
            )
        ).fetchone()

    if row is None:
        return None

    return dict(
        row
    )


def update_feedback(
    chat_id: str,
    feedback: str
) -> bool:
    """
    Sohbet kaydının olumlu veya olumsuz
    geri bildirimini günceller.
    """

    if feedback not in [
        "positive",
        "negative"
    ]:

        return False

    with get_connection() as connection:

        cursor = connection.execute(
            """
            UPDATE chats
            SET feedback = ?
            WHERE id = ?
            """,
            (
                feedback,
                chat_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0


def update_rating(
    chat_id: str,
    rating: int
) -> bool:
    """
    Kullanıcının verdiği 1-5 arasındaki
    yıldız puanını kaydeder.
    """

    if rating < 1 or rating > 5:
        return False

    with get_connection() as connection:

        cursor = connection.execute(
            """
            UPDATE chats
            SET rating = ?
            WHERE id = ?
            """,
            (
                rating,
                chat_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0


def clear_all_chats() -> None:
    """
    Bütün sohbet geçmişini siler.
    """

    with get_connection() as connection:

        connection.execute(
            """
            DELETE FROM chats
            """
        )

        connection.commit()