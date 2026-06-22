import hashlib
import os
import sqlite3
from datetime import datetime

from config import SQLITE_DB_PATH


def get_connection():
    connection = sqlite3.connect(SQLITE_DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _sha256(file_path):
    digest = hashlib.sha256()
    with open(file_path, "rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _ensure_column(cursor, table_name, column_name, definition):
    columns = {
        row[1]
        for row in cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
        )


def _backfill_document_hashes(connection):
    rows = connection.execute(
        "SELECT id, file_path FROM documents WHERE file_hash IS NULL"
    ).fetchall()
    for row in rows:
        file_path = row["file_path"]
        if not file_path or not os.path.isfile(file_path):
            continue
        try:
            connection.execute(
                "UPDATE documents SET file_hash = ? WHERE id = ?",
                (_sha256(file_path), row["id"]),
            )
        except OSError:
            continue


def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT,
        total_chunks INTEGER DEFAULT 0,
        status TEXT DEFAULT 'uploaded',
        created_at TEXT NOT NULL,
        file_hash TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        chroma_id TEXT NOT NULL,
        chunk_text TEXT NOT NULL,
        page_number INTEGER,
        chunk_index INTEGER,
        created_at TEXT NOT NULL,
        FOREIGN KEY(document_id) REFERENCES documents(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        answer TEXT,
        created_at TEXT NOT NULL,
        latency_ms INTEGER,
        status TEXT DEFAULT 'success'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS retrieval_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL,
        chunk_id INTEGER,
        chroma_id TEXT,
        source_type TEXT,
        score REAL,
        rank_position INTEGER,
        created_at TEXT NOT NULL,
        FOREIGN KEY(question_id) REFERENCES questions(id)
    )
    """)

    _ensure_column(cursor, "documents", "file_hash", "TEXT")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash)"
    )
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_chunks_chroma_id ON chunks(chroma_id)"
    )
    _backfill_document_hashes(connection)

    connection.commit()
    connection.close()


def insert_document(filename, file_path, file_type, file_hash=None):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    INSERT INTO documents (
        filename, file_path, file_type, status, created_at, file_hash
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        filename,
        file_path,
        file_type,
        "processing",
        datetime.utcnow().isoformat(),
        file_hash,
    ))
    document_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return document_id


def get_processed_document_by_hash(file_hash):
    if not file_hash:
        return None
    connection = get_connection()
    row = connection.execute("""
    SELECT *
    FROM documents
    WHERE file_hash = ? AND status = 'processed'
    ORDER BY id DESC
    LIMIT 1
    """, (file_hash,)).fetchone()
    connection.close()
    return dict(row) if row else None


def update_document_status(document_id, status, total_chunks=0):
    connection = get_connection()
    connection.execute("""
    UPDATE documents
    SET status = ?, total_chunks = ?
    WHERE id = ?
    """, (status, total_chunks, document_id))
    connection.commit()
    connection.close()


def insert_chunk(document_id, chroma_id, chunk_text, page_number, chunk_index):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    INSERT INTO chunks (
        document_id, chroma_id, chunk_text, page_number, chunk_index, created_at
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        document_id,
        chroma_id,
        chunk_text,
        page_number,
        chunk_index,
        datetime.utcnow().isoformat(),
    ))
    chunk_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return chunk_id


def insert_chunks_bulk(document_id, chunks):
    """Insert all chunks in one transaction and return Chroma-ready rows."""
    connection = get_connection()
    cursor = connection.cursor()
    created_at = datetime.utcnow().isoformat()
    stored_chunks = []

    try:
        for chunk in chunks:
            chroma_id = f"doc_{document_id}_chunk_{chunk['chunk_index']}"
            cursor.execute("""
            INSERT INTO chunks (
                document_id,
                chroma_id,
                chunk_text,
                page_number,
                chunk_index,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                document_id,
                chroma_id,
                chunk["text"],
                chunk["page_number"],
                chunk["chunk_index"],
                created_at,
            ))
            stored_chunks.append({
                "chunk_id": cursor.lastrowid,
                "chroma_id": chroma_id,
                "text": chunk["text"],
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
            })
        connection.commit()
        return stored_chunks
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def delete_chunks_for_document(document_id):
    connection = get_connection()
    connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
    connection.commit()
    connection.close()


def get_all_chunks():
    connection = get_connection()
    rows = connection.execute("""
    SELECT
        chunks.id,
        chunks.document_id,
        chunks.chroma_id,
        chunks.chunk_text,
        chunks.page_number,
        chunks.chunk_index,
        documents.filename
    FROM chunks
    JOIN documents ON chunks.document_id = documents.id
    WHERE documents.status = 'processed'
    """).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def insert_question(question, answer, latency_ms, status="success"):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    INSERT INTO questions (question, answer, latency_ms, status, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (
        question,
        answer,
        latency_ms,
        status,
        datetime.utcnow().isoformat(),
    ))
    question_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return question_id


def insert_retrieval_log(
    question_id,
    chunk_id,
    chroma_id,
    source_type,
    score,
    rank_position,
):
    connection = get_connection()
    connection.execute("""
    INSERT INTO retrieval_logs (
        question_id,
        chunk_id,
        chroma_id,
        source_type,
        score,
        rank_position,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        question_id,
        chunk_id,
        chroma_id,
        source_type,
        score,
        rank_position,
        datetime.utcnow().isoformat(),
    ))
    connection.commit()
    connection.close()


def get_documents():
    connection = get_connection()
    rows = connection.execute("""
    SELECT *
    FROM documents
    ORDER BY id DESC
    """).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_document(document_id):
    connection = get_connection()
    row = connection.execute(
        "SELECT * FROM documents WHERE id = ?",
        (document_id,),
    ).fetchone()
    connection.close()
    return dict(row) if row else None


def get_chunks_for_document(document_id):
    connection = get_connection()
    rows = connection.execute("""
    SELECT
        id,
        document_id,
        chroma_id,
        chunk_text,
        page_number,
        chunk_index,
        created_at
    FROM chunks
    WHERE document_id = ?
    ORDER BY chunk_index ASC
    """, (document_id,)).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_questions():
    connection = get_connection()
    rows = connection.execute("""
    SELECT *
    FROM questions
    ORDER BY id DESC
    LIMIT 50
    """).fetchall()
    connection.close()
    return [dict(row) for row in rows]
