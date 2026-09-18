import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "receipts.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ai_request TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            record_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


def get_last_record():
    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM records
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    connection.close()
    return row


def insert_record(
    ai_request,
    ai_response,
    previous_hash,
    record_hash,
    created_at
):
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO records
        (
            ai_request,
            ai_response,
            previous_hash,
            record_hash,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            ai_request,
            ai_response,
            previous_hash,
            record_hash,
            created_at
        )
    )

    connection.commit()

    record_id = cursor.lastrowid

    connection.close()

    return record_id


def update_record_hash(record_id, record_hash):
    connection = get_connection()

    connection.execute(
        """
        UPDATE records
        SET record_hash = ?
        WHERE id = ?
        """,
        (record_hash, record_id)
    )

    connection.commit()
    connection.close()


def get_record(record_id):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM records
        WHERE id = ?
        """,
        (record_id,)
    ).fetchone()

    connection.close()

    return row


def get_previous_record(record_id):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM records
        WHERE id < ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (record_id,)
    ).fetchone()

    connection.close()

    return row


def get_all_records():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM records
        ORDER BY id ASC
        """
    ).fetchall()

    connection.close()

    return rows