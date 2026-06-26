from __future__ import annotations

import hashlib
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .db import Database
from .importers import extract
from .models import Document
from .text_pipeline import chunk_chapters


class BookLibrary:
    def __init__(self, library_root: Path) -> None:
        self.root = Path(library_root)
        self.db = Database(self.root)

    def close(self) -> None:
        self.db.close()

    def import_source(self, source_path: Path) -> str:
        document = extract(Path(source_path))
        book_id = uuid.uuid4().hex
        now = _now()
        book_dir = self.root / "books" / book_id
        source_dir = book_dir / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        stored_source = source_dir / Path(source_path).name
        shutil.copy2(source_path, stored_source)
        source_hash = _sha256(stored_source)
        chunks = chunk_chapters(document.chapters)

        conn = self.db.conn
        with conn:
            conn.execute(
                """
                INSERT INTO books(id, title, author, language, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    book_id,
                    document.metadata.title,
                    document.metadata.author,
                    document.metadata.language,
                    "Imported",
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT INTO sources(id, book_id, original_path, stored_path, source_sha256, format, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uuid.uuid4().hex,
                    book_id,
                    str(Path(source_path).resolve()),
                    str(stored_source),
                    source_hash,
                    Path(source_path).suffix.lower().lstrip("."),
                    now,
                ),
            )
            for chapter in document.chapters:
                conn.execute(
                    """
                    INSERT INTO chapters(id, book_id, chapter_index, title, text)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (uuid.uuid4().hex, book_id, chapter.index, chapter.title, chapter.text),
                )
            for chunk in chunks:
                conn.execute(
                    """
                    INSERT INTO chunks(id, book_id, chapter_index, chunk_index, text, text_hash, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        uuid.uuid4().hex,
                        book_id,
                        chunk.chapter_index,
                        chunk.chunk_index,
                        chunk.text,
                        chunk.text_hash,
                        "Ready",
                    ),
                )
        return book_id

    def list_books(self) -> list[dict[str, object]]:
        rows = self.db.conn.execute(
            """
            SELECT
                b.id,
                b.title,
                b.author,
                b.language,
                b.status,
                COUNT(DISTINCT c.id) AS chapter_count,
                COUNT(DISTINCT k.id) AS chunk_count,
                b.updated_at
            FROM books b
            LEFT JOIN chapters c ON c.book_id = b.id
            LEFT JOIN chunks k ON k.book_id = b.id
            GROUP BY b.id
            ORDER BY b.updated_at DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def get_book(self, book_id: str) -> dict[str, object] | None:
        row = self.db.conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        return dict(row) if row else None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_name(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*]+', "-", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:120] or "Untitled"

