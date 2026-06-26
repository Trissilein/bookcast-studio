from __future__ import annotations

import hashlib
import json
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .assembler import assemble_audio
from .calibre import CalibreBook, CalibreClient, SUPPORTED_IMPORT_FORMATS
from .db import Database
from .importers import extract
from .models import Document, Metadata
from .text_pipeline import chunk_chapters
from .tts import TtsProvider, WindowsSapiProvider


class BookLibrary:
    def __init__(self, library_root: Path) -> None:
        self.root = Path(library_root)
        self.db = Database(self.root)

    def close(self) -> None:
        self.db.close()

    def import_source(self, source_path: Path) -> str:
        document = extract(Path(source_path))
        return self._store_document(document, Path(source_path), source_kind="file")

    def import_calibre_book(
        self,
        client: CalibreClient,
        book: CalibreBook,
        format_preference: tuple[str, ...] = SUPPORTED_IMPORT_FORMATS,
    ) -> str:
        existing = self.find_calibre_book(client.library_path, book)
        if existing:
            return existing

        fmt = book.preferred_format(format_preference)
        if not fmt:
            raise ValueError(f"Calibre book {book.id} has no supported format: {', '.join(book.formats)}")

        exported = client.export_book(book, fmt)
        try:
            document = extract(exported)
            document = Document(
                source_path=document.source_path,
                metadata=Metadata(
                    title=book.title or document.metadata.title,
                    author=book.authors or document.metadata.author,
                    language=book.language or document.metadata.language,
                ),
                chapters=document.chapters,
                raw_text=document.raw_text,
            )
            return self._store_document(
                document,
                exported,
                source_kind="calibre",
                external_id=book.id,
                external_library_path=str(client.library_path),
                external_uuid=book.uuid,
            )
        finally:
            if exported.parent.name.startswith("bookcast-calibre-export-"):
                shutil.rmtree(exported.parent, ignore_errors=True)

    def find_calibre_book(self, library_path: Path, book: CalibreBook) -> str | None:
        if book.uuid:
            row = self.db.conn.execute(
                """
                SELECT book_id FROM sources
                WHERE source_kind = 'calibre'
                  AND external_library_path = ?
                  AND external_uuid = ?
                LIMIT 1
                """,
                (str(Path(library_path)), book.uuid),
            ).fetchone()
            if row:
                return str(row["book_id"])

        row = self.db.conn.execute(
            """
            SELECT book_id FROM sources
            WHERE source_kind = 'calibre'
              AND external_library_path = ?
              AND external_id = ?
            LIMIT 1
            """,
            (str(Path(library_path)), book.id),
        ).fetchone()
        return str(row["book_id"]) if row else None

    def _store_document(
        self,
        document: Document,
        source_path: Path,
        *,
        source_kind: str,
        external_id: str | None = None,
        external_library_path: str | None = None,
        external_uuid: str | None = None,
    ) -> str:
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
                INSERT INTO sources(
                    id, book_id, original_path, stored_path, source_sha256, format,
                    source_kind, external_id, external_library_path, external_uuid, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uuid.uuid4().hex,
                    book_id,
                    str(Path(source_path).resolve()),
                    str(stored_source),
                    source_hash,
                    Path(source_path).suffix.lower().lstrip("."),
                    source_kind,
                    external_id,
                    external_library_path,
                    external_uuid,
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

    def get_chunks(self, book_id: str) -> list[dict[str, object]]:
        rows = self.db.conn.execute(
            """
            SELECT * FROM chunks
            WHERE book_id = ?
            ORDER BY chapter_index, chunk_index
            """,
            (book_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_book_text(self, book_id: str) -> str:
        rows = self.db.conn.execute(
            """
            SELECT title, text FROM chapters
            WHERE book_id = ?
            ORDER BY chapter_index
            """,
            (book_id,),
        ).fetchall()
        if not rows:
            raise ValueError(f"Book has no chapters: {book_id}")
        return "\n\n".join(f"# {row['title']}\n\n{row['text']}" for row in rows)

    def save_podcast_script(self, book_id: str, script: dict[str, object]) -> Path:
        book = self.get_book(book_id)
        if not book:
            raise ValueError(f"Unknown book id: {book_id}")
        now = _now()
        project_id = uuid.uuid4().hex
        out_dir = self.root / "books" / book_id / "podcasts"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{safe_name(str(script.get('title') or 'podcast'))}.json"
        out_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
        with self.db.conn:
            self.db.conn.execute(
                """
                INSERT INTO podcast_projects(id, source_book_id, title, mode, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    book_id,
                    str(script.get("title") or "Untitled Podcast"),
                    str(script.get("mode") or "educational"),
                    "Scripted",
                    now,
                    now,
                ),
            )
        return out_path

    def render_book(
        self,
        book_id: str,
        *,
        output_format: str = "opus",
        provider: TtsProvider | None = None,
        voice: str | None = None,
        rate: int = 0,
        ffmpeg: str = "ffmpeg",
        limit: int | None = None,
    ) -> Path:
        book = self.get_book(book_id)
        if not book:
            raise ValueError(f"Unknown book id: {book_id}")
        provider = provider or WindowsSapiProvider()
        if not provider.health():
            raise RuntimeError(f"TTS provider not available: {provider.id}")

        chunks = self.get_chunks(book_id)
        if limit is not None:
            chunks = chunks[:limit]
        if not chunks:
            raise ValueError(f"Book has no chunks: {book_id}")

        chunk_dir = self.root / "books" / book_id / "audio_chunks"
        rendered: list[Path] = []
        for chunk in chunks:
            out_wav = chunk_dir / f"c{int(chunk['chapter_index']):04d}_{int(chunk['chunk_index']):04d}_{chunk['text_hash'][:12]}.wav"
            if not out_wav.exists() or out_wav.stat().st_size == 0:
                provider.synthesize(str(chunk["text"]), out_wav, voice=voice, rate=rate)
                self._mark_chunk_rendered(str(chunk["id"]), out_wav)
            rendered.append(out_wav)

        output_dir = self.root / "books" / book_id / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_name = f"{safe_name(str(book['author']))} - {safe_name(str(book['title']))}.{output_format.lower()}"
        output_path = output_dir / output_name
        assemble_audio(rendered, output_path, output_format, ffmpeg=ffmpeg)
        self._add_output(book_id, output_format, output_path)
        return output_path

    def _mark_chunk_rendered(self, chunk_id: str, audio_path: Path) -> None:
        with self.db.conn:
            self.db.conn.execute(
                """
                UPDATE chunks
                SET status = 'Rendered', audio_path = ?, audio_format = 'wav', rendered_at = ?
                WHERE id = ?
                """,
                (str(audio_path), _now(), chunk_id),
            )

    def _add_output(self, book_id: str, output_format: str, output_path: Path) -> None:
        with self.db.conn:
            self.db.conn.execute(
                """
                INSERT INTO outputs(id, book_id, format, path, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (uuid.uuid4().hex, book_id, output_format.lower(), str(output_path), _now()),
            )


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
