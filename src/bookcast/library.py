from __future__ import annotations

import hashlib
import json
import re
import shutil
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from .assembler import assemble_audio, chapter_timeline, probe_duration
from .calibre import CalibreBook, CalibreClient, SUPPORTED_IMPORT_FORMATS
from .db import Database
from .importers import extract
from .models import Chapter, Document, Metadata
from .podcast import PodcastScript, PodcastTurn
from .text_pipeline import chunk_chapters, clean_text
from .tts import TtsProvider, WindowsSapiProvider

ProgressCallback = Callable[[dict[str, object]], None]


class BookLibrary:
    def __init__(self, library_root: Path) -> None:
        self.root = Path(library_root)
        self.db = Database(self.root)

    def close(self) -> None:
        self.db.close()

    def import_source(self, source_path: Path, cleanup_profile: str = "standard") -> str:
        existing = self.find_file_source(source_path)
        if existing:
            return existing
        document = extract(Path(source_path))
        return self._store_document(document, Path(source_path), source_kind="file", cleanup_profile=cleanup_profile)

    def find_file_source(self, source_path: Path) -> str | None:
        source_hash = _sha256(Path(source_path))
        row = self.db.conn.execute(
            """
            SELECT book_id FROM sources
            WHERE source_kind = 'file'
              AND source_sha256 = ?
            LIMIT 1
            """,
            (source_hash,),
        ).fetchone()
        return str(row["book_id"]) if row else None

    def import_calibre_book(
        self,
        client: CalibreClient,
        book: CalibreBook,
        format_preference: tuple[str, ...] = SUPPORTED_IMPORT_FORMATS,
        cleanup_profile: str = "standard",
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
                cleanup_profile=cleanup_profile,
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
        cleanup_profile: str = "standard",
    ) -> str:
        book_id = uuid.uuid4().hex
        now = _now()
        book_dir = self.root / "books" / book_id
        source_dir = book_dir / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        stored_source = source_dir / Path(source_path).name
        shutil.copy2(source_path, stored_source)
        source_hash = _sha256(stored_source)
        profile = self.get_cleanup_profile(cleanup_profile)
        profile_config = profile.get("config", {})
        cleaned_chapters = [
            Chapter(
                index=chapter.index,
                title=chapter.title,
                text=clean_text(chapter.text, profile_config),
            )
            for chapter in document.chapters
        ]
        chunks = chunk_chapters(cleaned_chapters, profile=profile_config)

        conn = self.db.conn
        with conn:
            conn.execute(
                """
                INSERT INTO books(id, title, author, language, cleanup_profile, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    book_id,
                    document.metadata.title,
                    document.metadata.author,
                    document.metadata.language,
                    cleanup_profile,
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
            for chapter in cleaned_chapters:
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
                b.cleanup_profile,
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

    def get_chapters(self, book_id: str) -> list[dict[str, object]]:
        rows = self.db.conn.execute(
            """
            SELECT * FROM chapters
            WHERE book_id = ?
            ORDER BY chapter_index
            """,
            (book_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_cleanup_profiles(self) -> list[dict[str, object]]:
        rows = self.db.conn.execute(
            """
            SELECT * FROM cleanup_profiles
            ORDER BY name
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def get_cleanup_profile(self, name: str | None = None) -> dict[str, object]:
        profile_name = (name or "standard").strip() or "standard"
        row = self.db.conn.execute(
            """
            SELECT * FROM cleanup_profiles
            WHERE name = ?
            LIMIT 1
            """,
            (profile_name,),
        ).fetchone()
        if row:
            data = dict(row)
            data["config"] = json.loads(str(data.get("config_json") or "{}"))
            return data
        return {
            "id": "standard",
            "name": "standard",
            "config_json": json.dumps(
                {
                    "max_chars": 1800,
                    "join_hyphenated_lines": True,
                    "collapse_blank_lines": True,
                    "collapse_spaces": True,
                    "remove_soft_hyphens": True,
                    "strip_trailing_whitespace": True,
                    "trim": True,
                    "max_blank_lines": 2,
                },
                ensure_ascii=False,
            ),
            "config": {
                "max_chars": 1800,
                "join_hyphenated_lines": True,
                "collapse_blank_lines": True,
                "collapse_spaces": True,
                "remove_soft_hyphens": True,
                "strip_trailing_whitespace": True,
                "trim": True,
                "max_blank_lines": 2,
            },
        }

    def upsert_cleanup_profile(self, name: str, config: dict[str, object]) -> str:
        profile_id = safe_name(name).lower().replace(" ", "_")
        now = _now()
        with self.db.conn:
            self.db.conn.execute(
                """
                INSERT INTO cleanup_profiles(id, name, config_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    config_json = excluded.config_json,
                    updated_at = excluded.updated_at
                """,
                (profile_id, name, json.dumps(config, ensure_ascii=False), now, now),
            )
        return profile_id

    def set_book_cleanup_profile(self, book_id: str, cleanup_profile: str) -> None:
        with self.db.conn:
            self.db.conn.execute(
                """
                UPDATE books
                SET cleanup_profile = ?, updated_at = ?
                WHERE id = ?
                """,
                (cleanup_profile, _now(), book_id),
            )
        self.rechunk_book(book_id)

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

    def update_chapter(self, book_id: str, chapter_index: int, title: str, text: str) -> None:
        with self.db.conn:
            self.db.conn.execute(
                """
                UPDATE chapters
                SET title = ?, text = ?
                WHERE book_id = ? AND chapter_index = ?
                """,
                (title, text, book_id, chapter_index),
            )
            self.db.conn.execute(
                """
                UPDATE books
                SET status = 'Needs Rechunk', updated_at = ?
                WHERE id = ?
                """,
                (_now(), book_id),
            )
        self.rechunk_book(book_id)

    def rechunk_book(self, book_id: str) -> None:
        book = self.get_book(book_id)
        if not book:
            raise ValueError(f"Unknown book id: {book_id}")
        profile = self.get_cleanup_profile(str(book.get("cleanup_profile") or "standard"))
        profile_config = profile.get("config", {})
        chapter_rows = self.get_chapters(book_id)
        cleaned_chapters: list[Chapter] = []
        for row in chapter_rows:
            cleaned_chapters.append(
                Chapter(
                    index=int(row["chapter_index"]),
                    title=str(row["title"]),
                    text=clean_text(str(row["text"]), profile_config),
                )
            )
        chunks = chunk_chapters(cleaned_chapters, profile=profile_config)
        with self.db.conn:
            self.db.conn.execute("DELETE FROM chunks WHERE book_id = ?", (book_id,))
            for chunk in chunks:
                self.db.conn.execute(
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
            self.db.conn.execute("DELETE FROM outputs WHERE book_id = ?", (book_id,))
            self.db.conn.execute(
                """
                UPDATE books
                SET status = 'Imported', updated_at = ?
                WHERE id = ?
                """,
                (_now(), book_id),
            )
        self._clear_render_artifacts(book_id)

    def _clear_render_artifacts(self, book_id: str) -> None:
        book_dir = self.root / "books" / book_id
        for rel in ["audio_chunks", "output"]:
            path = book_dir / rel
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)

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

    def upsert_voice(self, provider: str, name: str, locale: str | None = None, config: dict | None = None) -> str:
        voice_id = f"{provider}:{name}"
        with self.db.conn:
            self.db.conn.execute(
                """
                INSERT INTO voices(id, provider, name, locale, config_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    provider = excluded.provider,
                    name = excluded.name,
                    locale = excluded.locale,
                    config_json = excluded.config_json
                """,
                (voice_id, provider, name, locale, json.dumps(config or {}, ensure_ascii=False)),
            )
        return voice_id

    def sync_speakers(
        self,
        book_id: str,
        speaker_names: list[str],
        voice_map: dict[str, str] | None = None,
        provider: str = "windows_sapi",
    ) -> None:
        voice_ids: dict[str, str | None] = {}
        if voice_map:
            for speaker_name in speaker_names:
                if speaker_name in voice_map and voice_map[speaker_name]:
                    voice_ids[speaker_name] = self.upsert_voice(provider, voice_map[speaker_name])
                else:
                    voice_ids[speaker_name] = None

        with self.db.conn:
            self.db.conn.execute("DELETE FROM speakers WHERE book_id = ?", (book_id,))
            for speaker_name in speaker_names:
                self.db.conn.execute(
                    """
                    INSERT INTO speakers(id, book_id, name, voice_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (uuid.uuid4().hex, book_id, speaker_name, voice_ids.get(speaker_name)),
                )

    def list_speakers(self, book_id: str) -> list[dict[str, object]]:
        rows = self.db.conn.execute(
            """
            SELECT s.name, s.voice_id, v.provider, v.name AS voice_name, v.locale
            FROM speakers s
            LEFT JOIN voices v ON v.id = s.voice_id
            WHERE s.book_id = ?
            ORDER BY s.name
            """,
            (book_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_voices(self) -> list[dict[str, object]]:
        rows = self.db.conn.execute(
            """
            SELECT * FROM voices
            ORDER BY provider, name
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def list_outputs(self, book_id: str | None = None) -> list[dict[str, object]]:
        if book_id:
            rows = self.db.conn.execute(
                """
                SELECT * FROM outputs
                WHERE book_id = ?
                ORDER BY created_at DESC
                """,
                (book_id,),
            ).fetchall()
        else:
            rows = self.db.conn.execute(
                """
                SELECT * FROM outputs
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def render_book(
        self,
        book_id: str,
        *,
        output_format: str = "opus",
        provider: TtsProvider | None = None,
        voice: str | None = None,
        rate: int = 0,
        ffmpeg: str = "ffmpeg",
        ffprobe: str = "ffprobe",
        limit: int | None = None,
        voice_map: dict[str, str] | None = None,
        progress_callback: ProgressCallback | None = None,
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

        chapter_rows = self.get_chapters(book_id)
        chapter_titles = {int(row["chapter_index"]): str(row["title"]) for row in chapter_rows}
        chunk_dir = self.root / "books" / book_id / "audio_chunks"
        rendered: list[Path] = []
        rendered_meta: list[tuple[int, Path]] = []
        total = len(chunks)
        if progress_callback:
            progress_callback({"phase": "tts", "progress": 10, "chunk": 0, "total": total})
        for index, chunk in enumerate(chunks, start=1):
            selected_voice = _voice_for_text(str(chunk["text"]), voice, voice_map)
            render_key = safe_name(f"{provider.id}_{selected_voice or 'default'}_rate{rate}")[:80]
            out_wav = chunk_dir / (
                f"c{int(chunk['chapter_index']):04d}_{int(chunk['chunk_index']):04d}_"
                f"{chunk['text_hash'][:12]}_{render_key}.wav"
            )
            cached = out_wav.exists() and out_wav.stat().st_size > 0
            if not cached:
                provider.synthesize(str(chunk["text"]), out_wav, voice=selected_voice, rate=rate)
                self._mark_chunk_rendered(str(chunk["id"]), out_wav)
            rendered.append(out_wav)
            rendered_meta.append((int(chunk["chapter_index"]), out_wav))
            if progress_callback:
                progress_callback(
                    {
                        "phase": "tts",
                        "progress": 10 + int(index / total * 75),
                        "chunk": index,
                        "total": total,
                        "cached": cached,
                        "chapter_index": int(chunk["chapter_index"]),
                        "chunk_index": int(chunk["chunk_index"]),
                        "voice": selected_voice or "",
                    }
                )

        output_dir = self.root / "books" / book_id / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_name = f"{safe_name(str(book['author']))} - {safe_name(str(book['title']))}.{output_format.lower()}"
        output_path = output_dir / output_name
        if progress_callback:
            progress_callback({"phase": "assemble", "progress": 92, "chunk": total, "total": total})
        timeline = chapter_timeline(rendered_meta, chapter_titles, ffprobe=ffprobe) if output_format.lower() == "m4b" else None
        assemble_kwargs = {"ffmpeg": ffmpeg}
        if timeline is not None:
            assemble_kwargs["chapters"] = timeline
        assemble_audio(rendered, output_path, output_format, **assemble_kwargs)
        self._add_output(book_id, output_format, output_path)
        return output_path

    def render_podcast_script(
        self,
        book_id: str,
        script: PodcastScript,
        *,
        output_format: str = "opus",
        provider: TtsProvider | None = None,
        voice_map: dict[str, str] | None = None,
        ffmpeg: str = "ffmpeg",
        ffprobe: str = "ffprobe",
        rate: int = 0,
        progress_callback: ProgressCallback | None = None,
    ) -> Path:
        book = self.get_book(book_id)
        if not book:
            raise ValueError(f"Unknown book id: {book_id}")
        provider = provider or WindowsSapiProvider()
        if not provider.health():
            raise RuntimeError(f"TTS provider not available: {provider.id}")
        if not script.turns:
            raise ValueError("Podcast script has no turns")

        speaker_names = list(dict.fromkeys(script.speakers or [turn.speaker for turn in script.turns]))
        self.sync_speakers(book_id, speaker_names, voice_map=voice_map, provider=provider.id)

        voice_by_speaker = voice_map or {}
        default_voice = None
        voices = provider.list_voices()
        if voices:
            default_voice = voices[0].id

        podcast_dir = self.root / "books" / book_id / "podcasts" / safe_name(script.title)
        chunk_dir = podcast_dir / "audio_chunks"
        chunk_dir.mkdir(parents=True, exist_ok=True)

        rendered: list[Path] = []
        elapsed = 0.0
        chapter_marks: list[tuple[str, float]] = []
        total = len(script.turns)
        if progress_callback:
            progress_callback({"phase": "tts", "progress": 10, "chunk": 0, "total": total})
        for index, turn in enumerate(script.turns):
            voice_name = voice_by_speaker.get(turn.speaker) or default_voice
            render_key = safe_name(f"{provider.id}_{voice_name or 'default'}_rate{rate}")[:80]
            out_wav = chunk_dir / f"t{index:04d}_{safe_name(turn.speaker)}_{render_key}.wav"
            cached = out_wav.exists() and out_wav.stat().st_size > 0
            if not cached:
                provider.synthesize(turn.text, out_wav, voice=voice_name, rate=rate)
            rendered.append(out_wav)
            chapter_marks.append((turn.speaker, elapsed))
            elapsed += probe_duration(out_wav, ffprobe=ffprobe)
            if progress_callback:
                progress_callback(
                    {
                        "phase": "tts",
                        "progress": 10 + int((index + 1) / total * 75),
                        "chunk": index + 1,
                        "total": total,
                        "cached": cached,
                        "speaker": turn.speaker,
                    }
                )

        output_path = podcast_dir / f"{safe_name(script.title)}.{output_format.lower()}"
        if progress_callback:
            progress_callback({"phase": "assemble", "progress": 92, "chunk": total, "total": total})
        timeline = chapter_marks if output_format.lower() == "m4b" else None
        assemble_kwargs = {"ffmpeg": ffmpeg}
        if timeline is not None:
            assemble_kwargs["chapters"] = timeline
        assemble_audio(rendered, output_path, output_format, **assemble_kwargs)
        self.save_podcast_script(book_id, script.to_dict())
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

    def add_output(self, book_id: str, output_format: str, output_path: Path) -> None:
        self._add_output(book_id, output_format, output_path)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _voice_for_text(text: str, default_voice: str | None, voice_map: dict[str, str] | None) -> str | None:
    if not voice_map:
        return default_voice
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    first_line_lower = first_line.lower()
    sample = clean_text(text)[:500]
    for speaker, speaker_voice in voice_map.items():
        speaker = speaker.strip()
        speaker_voice = speaker_voice.strip()
        if not speaker or not speaker_voice:
            continue
        speaker_lower = speaker.lower()
        if first_line_lower.startswith(f"{speaker_lower}:") or first_line_lower.startswith(f"{speaker_lower} -"):
            return speaker_voice
        if _dialogue_attributed_to(sample, speaker):
            return speaker_voice
    return default_voice


def _dialogue_attributed_to(text: str, speaker: str) -> bool:
    speaker_pattern = re.escape(speaker)
    speaker_ref = rf"(?<!\w){speaker_pattern}(?!\w)"
    verbs = (
        "said|asked|replied|whispered|called|cried|answered|"
        "muttered|shouted|murmured|continued|"
        "sagte|fragte|antwortete|flüsterte|flusterte|rief|meinte|"
        "erwiderte|murmelte|schrie|sprach|entgegnete|bemerkte"
    )
    for quoted in re.finditer(r'["“„»«][^"“”„»«]{1,240}["”»«]', text):
        after_quote = text[quoted.end() : quoted.end() + 120]
        before_quote = text[max(0, quoted.start() - 100) : quoted.start()]
        if (
            re.search(rf"\b(?:{verbs})\s+{speaker_ref}", after_quote, flags=re.IGNORECASE)
            or re.search(rf"{speaker_ref}\s*(?:,|:)?\s*\b(?:{verbs})\b", after_quote, flags=re.IGNORECASE)
            or re.search(rf"{speaker_ref}\s*(?:,|:)?\s*\b(?:{verbs})\b", before_quote, flags=re.IGNORECASE)
            or re.search(rf"\b(?:{verbs})\s+{speaker_ref}", before_quote, flags=re.IGNORECASE)
        ):
            return True
    return False


def safe_name(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*]+', "-", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:120] or "Untitled"
