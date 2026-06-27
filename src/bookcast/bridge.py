from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

from .calibre import CalibreClient, find_calibredb
from .library import BookLibrary
from .tts import AudioCppProvider, TtsProvider, WindowsSapiProvider


def emit(event: str, **payload: Any) -> None:
    print(json.dumps({"event": event, **payload}, ensure_ascii=False), flush=True)


def diagnose(library_root: Path) -> int:
    tts = WindowsSapiProvider()
    emit(
        "diagnostic",
        library=str(library_root),
        ffmpeg=shutil.which("ffmpeg"),
        ffprobe=shutil.which("ffprobe"),
        calibredb=find_calibredb(),
        windows_sapi=tts.health(),
    )
    return 0


def voices(
    provider: str = "windows_sapi",
    audio_cpp_exe: str | None = None,
    audio_cpp_model: str | None = None,
    audio_cpp_backend: str = "cpu",
    audio_cpp_family: str | None = None,
) -> int:
    tts_provider = _tts_provider(
        provider,
        audio_cpp_exe=audio_cpp_exe,
        audio_cpp_model=audio_cpp_model,
        audio_cpp_backend=audio_cpp_backend,
        audio_cpp_family=audio_cpp_family,
    )
    emit(
        "voices",
        provider=tts_provider.id,
        voices=[voice.__dict__ for voice in tts_provider.list_voices()],
    )
    return 0


def list_books(library_root: Path) -> int:
    library = BookLibrary(library_root)
    try:
        emit("books", books=library.list_books())
    finally:
        library.close()
    return 0


def outputs(library_root: Path, book_id: str | None = None) -> int:
    library = BookLibrary(library_root)
    try:
        emit("outputs", outputs=library.list_outputs(book_id))
    finally:
        library.close()
    return 0


def book_preview(library_root: Path, book_id: str, max_chars: int = 1400) -> int:
    library = BookLibrary(library_root)
    try:
        book = library.get_book(book_id)
        if not book:
            raise ValueError(f"Unknown book id: {book_id}")
        chapters = library.get_chapters(book_id)
        chunks = library.get_chunks(book_id)
        preview_parts: list[str] = []
        for chapter in chapters[:5]:
            text = str(chapter["text"]).strip().replace("\r\n", "\n")
            preview_parts.append(f"# {chapter['title']}\n{text[:max_chars]}")
        emit(
            "book_preview",
            book=book,
            chapters=[
                {
                    "index": chapter["chapter_index"],
                    "title": chapter["title"],
                    "chars": len(str(chapter["text"])),
                }
                for chapter in chapters
            ],
            chunk_count=len(chunks),
            first_chunk=chunks[0] if chunks else None,
            preview="\n\n".join(preview_parts)[:max_chars],
        )
    finally:
        library.close()
    return 0


def import_file(library_root: Path, source: Path, cleanup_profile: str = "standard") -> int:
    emit("job_started", job="import", source=str(source))
    library = BookLibrary(library_root)
    try:
        book_id = library.import_source(source, cleanup_profile=cleanup_profile)
        book = library.get_book(book_id)
        emit("job_progress", job="import", progress=100)
        emit("job_done", job="import", book_id=book_id, book=book)
    finally:
        library.close()
    return 0


def calibre_scan(calibre_library: Path, calibredb: str | None = None, limit: int | None = None) -> int:
    executable = calibredb or find_calibredb() or "calibredb"
    emit("job_started", job="calibre_scan", calibre_library=str(calibre_library), calibredb=executable)
    client = CalibreClient(calibre_library, calibredb=executable)
    books = client.scan(limit=limit)
    supported = [book for book in books if book.preferred_format()]
    emit(
        "calibre_books",
        books=[book.__dict__ for book in supported],
        skipped=len(books) - len(supported),
    )
    emit("job_done", job="calibre_scan", count=len(supported))
    return 0


def calibre_import(
    library_root: Path,
    calibre_library: Path,
    ids: list[str] | None = None,
    calibredb: str | None = None,
    limit: int | None = None,
    cleanup_profile: str = "standard",
) -> int:
    executable = calibredb or find_calibredb() or "calibredb"
    emit("job_started", job="calibre_import", calibre_library=str(calibre_library), calibredb=executable)
    client = CalibreClient(calibre_library, calibredb=executable)
    books = [book for book in client.scan(limit=limit) if book.preferred_format()]
    if ids:
        wanted = {str(item).strip() for item in ids if str(item).strip()}
        books = [book for book in books if book.id in wanted]
    if not books:
        emit("error", message="No matching Calibre books with EPUB/TXT/MD found.", error_type="NoCalibreBooks")
        return 1

    library = BookLibrary(library_root)
    try:
        total = len(books)
        imported: list[dict[str, object]] = []
        for index, book in enumerate(books, start=1):
            book_id = library.import_calibre_book(client, book, cleanup_profile=cleanup_profile)
            stored = library.get_book(book_id)
            imported.append({"calibre_id": book.id, "book_id": book_id, "book": stored})
            emit(
                "calibre_imported",
                calibre_id=book.id,
                book_id=book_id,
                title=book.title,
                author=book.authors,
            )
            emit(
                "job_progress",
                job="calibre_import",
                progress=int(index / total * 100),
                imported=index,
                total=total,
            )
        emit("job_done", job="calibre_import", count=len(imported), imported=imported)
    finally:
        library.close()
    return 0


def render_book(
    library_root: Path,
    book_id: str,
    output_format: str = "opus",
    voice: str | None = None,
    rate: int = 0,
    limit: int | None = None,
    ffmpeg: str = "ffmpeg",
    provider: str = "windows_sapi",
    audio_cpp_exe: str | None = None,
    audio_cpp_model: str | None = None,
    audio_cpp_backend: str = "cpu",
    audio_cpp_family: str | None = None,
) -> int:
    emit("job_started", job="render", book_id=book_id, format=output_format, provider=provider)
    library = BookLibrary(library_root)
    try:
        chunks = library.get_chunks(book_id)
        emit("job_progress", job="render", progress=5, chunks=len(chunks))
        tts_provider = _tts_provider(
            provider,
            audio_cpp_exe=audio_cpp_exe,
            audio_cpp_model=audio_cpp_model,
            audio_cpp_backend=audio_cpp_backend,
            audio_cpp_family=audio_cpp_family,
        )
        output = library.render_book(
            book_id,
            output_format=output_format,
            provider=tts_provider,
            voice=voice,
            rate=rate,
            limit=limit,
            ffmpeg=ffmpeg,
        )
        emit("job_progress", job="render", progress=100)
        emit("job_done", job="render", output=str(output))
    finally:
        library.close()
    return 0


def sample_render(
    library_root: Path,
    book_id: str,
    output_format: str = "opus",
    voice: str | None = None,
    rate: int = 0,
    ffmpeg: str = "ffmpeg",
    provider: str = "windows_sapi",
    audio_cpp_exe: str | None = None,
    audio_cpp_model: str | None = None,
    audio_cpp_backend: str = "cpu",
    audio_cpp_family: str | None = None,
) -> int:
    emit("job_started", job="sample_render", book_id=book_id, format=output_format, provider=provider)
    return render_book(
        library_root,
        book_id,
        output_format=output_format,
        voice=voice,
        rate=rate,
        limit=1,
        ffmpeg=ffmpeg,
        provider=provider,
        audio_cpp_exe=audio_cpp_exe,
        audio_cpp_model=audio_cpp_model,
        audio_cpp_backend=audio_cpp_backend,
        audio_cpp_family=audio_cpp_family,
    )


def _tts_provider(
    provider: str,
    *,
    audio_cpp_exe: str | None,
    audio_cpp_model: str | None,
    audio_cpp_backend: str,
    audio_cpp_family: str | None,
) -> TtsProvider:
    if provider == "audio_cpp":
        if not audio_cpp_exe:
            raise RuntimeError("audio.cpp executable is required")
        if not audio_cpp_model:
            raise RuntimeError("audio.cpp model is required")
        return AudioCppProvider(
            audio_cpp_exe,
            model=audio_cpp_model,
            backend=audio_cpp_backend,
            family=audio_cpp_family,
        )
    return WindowsSapiProvider()


def run_safely(fn, *args: Any, **kwargs: Any) -> int:
    try:
        return int(fn(*args, **kwargs))
    except Exception as exc:  # noqa: BLE001 - bridge must return structured errors.
        emit("error", message=str(exc), error_type=exc.__class__.__name__)
        return 1
