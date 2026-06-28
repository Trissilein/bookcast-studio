from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .calibre import CalibreClient, diagnose_calibre_library, find_calibredb
from .characters import suggest_characters as generate_character_suggestions
from .importers import SUPPORTED_EXTENSIONS
from .library import BookLibrary
from .llm import OllamaProvider
from .podcast import generate_podcast_script
from .tts import AudioCppProvider, PiperProvider, TtsProvider, WindowsSapiProvider


DEFAULT_PIPER_EXE = Path(r"D:\GIT\Trispr_Flow\src-tauri\bin\piper\piper.exe")
DEFAULT_PIPER_VOICE_DIR = Path(r"D:\GIT\Trispr_Flow\src-tauri\bin\piper\voices")
DEFAULT_AUDIO_CPP_EXE = Path(r"D:\GIT\audio.cpp\build\windows-cpu-release\bin\audiocpp_cli.exe")


def emit(event: str, **payload: Any) -> None:
    print(json.dumps({"event": event, **payload}, ensure_ascii=False), flush=True)


def diagnose(library_root: Path) -> int:
    tts = WindowsSapiProvider()
    piper = PiperProvider(str(DEFAULT_PIPER_EXE), voice_dir=str(DEFAULT_PIPER_VOICE_DIR))
    emit(
        "diagnostic",
        library=str(library_root),
        ffmpeg=shutil.which("ffmpeg"),
        ffprobe=shutil.which("ffprobe"),
        calibredb=find_calibredb(),
        windows_sapi=tts.health(),
        piper=piper.health() if DEFAULT_PIPER_EXE.exists() else False,
        piper_executable=str(DEFAULT_PIPER_EXE) if DEFAULT_PIPER_EXE.exists() else "",
        piper_voice_dir=str(DEFAULT_PIPER_VOICE_DIR) if DEFAULT_PIPER_VOICE_DIR.exists() else "",
        audio_cpp_executable=str(DEFAULT_AUDIO_CPP_EXE) if DEFAULT_AUDIO_CPP_EXE.exists() else "",
    )
    return 0


def voices(
    provider: str = "windows_sapi",
    audio_cpp_exe: str | None = None,
    audio_cpp_model: str | None = None,
    audio_cpp_backend: str = "cpu",
    audio_cpp_family: str | None = None,
    piper_exe: str | None = None,
    piper_voice_dir: str | None = None,
    piper_model: str | None = None,
) -> int:
    tts_provider = _tts_provider(
        provider,
        audio_cpp_exe=audio_cpp_exe,
        audio_cpp_model=audio_cpp_model,
        audio_cpp_backend=audio_cpp_backend,
        audio_cpp_family=audio_cpp_family,
        piper_exe=piper_exe,
        piper_voice_dir=piper_voice_dir,
        piper_model=piper_model,
    )
    emit(
        "voices",
        provider=tts_provider.id,
        voices=[voice.__dict__ for voice in tts_provider.list_voices()],
    )
    return 0


def tts_test(
    library_root: Path,
    text: str,
    output_format: str = "wav",
    voice: str | None = None,
    rate: int = 0,
    provider: str = "windows_sapi",
    audio_cpp_exe: str | None = None,
    audio_cpp_model: str | None = None,
    audio_cpp_backend: str = "cpu",
    audio_cpp_family: str | None = None,
    piper_exe: str | None = None,
    piper_voice_dir: str | None = None,
    piper_model: str | None = None,
) -> int:
    text = text.strip()
    if not text:
        raise ValueError("TTS test text is required")
    if output_format != "wav":
        raise ValueError("TTS test currently writes WAV only")
    tts_provider = _tts_provider(
        provider,
        audio_cpp_exe=audio_cpp_exe,
        audio_cpp_model=audio_cpp_model,
        audio_cpp_backend=audio_cpp_backend,
        audio_cpp_family=audio_cpp_family,
        piper_exe=piper_exe,
        piper_voice_dir=piper_voice_dir,
        piper_model=piper_model,
    )
    emit("job_started", job="tts_test", provider=tts_provider.id, chars=len(text))
    output_dir = Path(library_root) / "diagnostics" / "tts_tests"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = output_dir / f"{stamp}_{tts_provider.id}.wav"
    emit("job_progress", job="tts_test", progress=20)
    tts_provider.synthesize(text, output, voice=voice, rate=rate)
    emit("job_progress", job="tts_test", progress=100)
    emit("tts_test", provider=tts_provider.id, output=str(output), chars=len(text), voice=voice or "")
    emit("job_done", job="tts_test", output=str(output))
    return 0


def audio_cpp_health(
    audio_cpp_exe: str | None = None,
    audio_cpp_model: str | None = None,
    audio_cpp_backend: str = "cpu",
    audio_cpp_family: str | None = None,
) -> int:
    issues: list[str] = []
    hints: list[str] = []
    audio_cpp_exe = audio_cpp_exe or (str(DEFAULT_AUDIO_CPP_EXE) if DEFAULT_AUDIO_CPP_EXE.exists() else None)
    if not audio_cpp_exe:
        issues.append("audio.cpp executable is not configured")
        hints.append("Build audio.cpp, then set audiocpp_cli.exe with Browse in TTS Studio or Settings.")
    elif not Path(audio_cpp_exe).exists() and shutil.which(audio_cpp_exe) is None:
        issues.append(f"audio.cpp executable not found: {audio_cpp_exe}")
        hints.append("Use Browse to point to the built audiocpp_cli.exe, or rebuild audio.cpp.")
    if not audio_cpp_model:
        issues.append("audio.cpp model is not configured")
        hints.append("Choose a compatible local TTS model before using the audio.cpp engine.")
    elif any(marker in audio_cpp_model for marker in ("\\", "/", ":")) and not Path(audio_cpp_model).exists():
        issues.append(f"audio.cpp model path not found: {audio_cpp_model}")
        hints.append("Use Browse to choose an existing model file, or pass a valid model name if audio.cpp supports it.")
    if audio_cpp_model and not audio_cpp_family:
        hints.append("Family is optional; set it only if your audio.cpp model requires --family.")

    healthy = False
    if not issues:
        provider = AudioCppProvider(
            str(audio_cpp_exe),
            model=str(audio_cpp_model),
            backend=audio_cpp_backend,
            family=audio_cpp_family,
        )
        healthy = provider.health()
        if not healthy:
            issues.append("audio.cpp --help failed")

    emit(
        "audio_cpp_health",
        healthy=healthy,
        executable=audio_cpp_exe or "",
        model=audio_cpp_model or "",
        backend=audio_cpp_backend,
        family=audio_cpp_family or "",
        issues=issues,
        hints=hints,
    )
    return 0 if healthy else 1


def list_books(library_root: Path, preview_first: bool = False) -> int:
    library = BookLibrary(library_root)
    try:
        books = library.list_books()
        emit("books", books=books)
        if preview_first and books:
            emit("book_preview", **_book_preview_payload(library, str(books[0]["id"])))
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


def cleanup_profiles(library_root: Path) -> int:
    library = BookLibrary(library_root)
    try:
        profiles = library.list_cleanup_profiles() or [library.get_cleanup_profile("standard")]
        emit("cleanup_profiles", profiles=profiles)
    finally:
        library.close()
    return 0


def set_cleanup_profile(library_root: Path, book_id: str, cleanup_profile: str) -> int:
    emit("job_started", job="cleanup", book_id=book_id, cleanup_profile=cleanup_profile)
    library = BookLibrary(library_root)
    try:
        library.set_book_cleanup_profile(book_id, cleanup_profile)
        book = library.get_book(book_id)
        emit("job_progress", job="cleanup", progress=100)
        emit("job_done", job="cleanup", book_id=book_id, book=book)
        emit("book_preview", **_book_preview_payload(library, book_id))
    finally:
        library.close()
    return 0


def book_preview(library_root: Path, book_id: str, max_chars: int = 1400) -> int:
    library = BookLibrary(library_root)
    try:
        emit("book_preview", **_book_preview_payload(library, book_id, max_chars=max_chars))
    finally:
        library.close()
    return 0


def characters(
    library_root: Path,
    book_id: str,
    ollama_url: str = "http://127.0.0.1:11434",
    model: str = "qwen3:8b",
) -> int:
    emit("job_started", job="characters", book_id=book_id, provider="ollama", model=model)
    text = _book_text(library_root, book_id)
    provider = OllamaProvider(model=model, base_url=ollama_url)
    if not provider.health():
        raise RuntimeError(f"Ollama unavailable at {ollama_url}")
    emit("job_progress", job="characters", progress=20)
    candidates = generate_character_suggestions(text, provider)
    emit("characters", candidates=[candidate.__dict__ for candidate in candidates])
    emit("job_done", job="characters", count=len(candidates))
    return 0


def podcast_script(
    library_root: Path,
    book_id: str,
    mode: str = "educational",
    ollama_url: str = "http://127.0.0.1:11434",
    model: str = "qwen3:8b",
) -> int:
    emit("job_started", job="podcast_script", book_id=book_id, mode=mode, provider="ollama", model=model)
    text = _book_text(library_root, book_id)
    provider = OllamaProvider(model=model, base_url=ollama_url)
    if not provider.health():
        raise RuntimeError(f"Ollama unavailable at {ollama_url}")
    emit("job_progress", job="podcast_script", progress=20)
    script = generate_podcast_script(text, provider, mode=mode)
    library = BookLibrary(library_root)
    try:
        path = library.save_podcast_script(book_id, script.to_dict())
    finally:
        library.close()
    emit("podcast_script", script=script.to_dict(), path=str(path))
    emit("job_done", job="podcast_script", path=str(path), count=len(script.turns))
    return 0


def podcast_render(
    library_root: Path,
    book_id: str,
    mode: str = "educational",
    output_format: str = "opus",
    voice_entries: list[str] | None = None,
    rate: int = 0,
    ffmpeg: str = "ffmpeg",
    ollama_url: str = "http://127.0.0.1:11434",
    model: str = "qwen3:8b",
    provider: str = "windows_sapi",
    audio_cpp_exe: str | None = None,
    audio_cpp_model: str | None = None,
    audio_cpp_backend: str = "cpu",
    audio_cpp_family: str | None = None,
    piper_exe: str | None = None,
    piper_voice_dir: str | None = None,
    piper_model: str | None = None,
) -> int:
    emit("job_started", job="podcast_render", book_id=book_id, mode=mode, format=output_format, provider=provider)
    text = _book_text(library_root, book_id)
    llm = OllamaProvider(model=model, base_url=ollama_url)
    if not llm.health():
        raise RuntimeError(f"Ollama unavailable at {ollama_url}")
    emit("job_progress", job="podcast_render", progress=20)
    script = generate_podcast_script(text, llm, mode=mode)
    tts_provider = _tts_provider(
        provider,
        audio_cpp_exe=audio_cpp_exe,
        audio_cpp_model=audio_cpp_model,
        audio_cpp_backend=audio_cpp_backend,
        audio_cpp_family=audio_cpp_family,
        piper_exe=piper_exe,
        piper_voice_dir=piper_voice_dir,
        piper_model=piper_model,
    )
    library = BookLibrary(library_root)
    try:
        output = library.render_podcast_script(
            book_id,
            script,
            output_format=output_format,
            provider=tts_provider,
            voice_map=_parse_voice_entries(voice_entries or []),
            ffmpeg=ffmpeg,
            rate=rate,
            progress_callback=lambda payload: emit("job_progress", job="podcast_render", **payload),
        )
        outputs_payload = library.list_outputs(book_id)
    finally:
        library.close()
    emit("podcast_script", script=script.to_dict(), output=str(output))
    emit("outputs", outputs=outputs_payload)
    emit("job_progress", job="podcast_render", progress=100)
    emit("job_done", job="podcast_render", output=str(output), count=len(script.turns))
    return 0


def import_file(library_root: Path, source: Path, cleanup_profile: str = "standard") -> int:
    emit("job_started", job="import", source=str(source))
    library = BookLibrary(library_root)
    try:
        sources = _source_files(source)
        imported: list[dict[str, object]] = []
        total = len(sources)
        for index, path in enumerate(sources, start=1):
            book_id = library.import_source(path, cleanup_profile=cleanup_profile)
            book = library.get_book(book_id)
            imported.append({"book_id": book_id, "book": book, "source": str(path)})
            emit("source_imported", book_id=book_id, book=book, source=str(path))
            emit("job_progress", job="import", progress=int(index / total * 100), imported=index, total=total)
        first = imported[0]
        emit("job_done", job="import", book_id=first["book_id"], book=first["book"], count=len(imported), imported=imported)
        emit("book_preview", **_book_preview_payload(library, str(first["book_id"])))
    finally:
        library.close()
    return 0


def calibre_scan(calibre_library: Path, calibredb: str | None = None, limit: int | None = None) -> int:
    diagnostic = diagnose_calibre_library(calibre_library, calibredb=calibredb)
    emit("calibre_diagnostic", **diagnostic)
    if diagnostic["issues"]:
        return 1
    executable = str(diagnostic["calibredb"])
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


def calibre_diagnose(calibre_library: Path, calibredb: str | None = None) -> int:
    diagnostic = diagnose_calibre_library(calibre_library, calibredb=calibredb)
    emit("calibre_diagnostic", **diagnostic)
    return 0 if diagnostic["healthy"] else 1


def calibre_import(
    library_root: Path,
    calibre_library: Path,
    ids: list[str] | None = None,
    calibredb: str | None = None,
    limit: int | None = None,
    cleanup_profile: str = "standard",
) -> int:
    diagnostic = diagnose_calibre_library(calibre_library, calibredb=calibredb)
    emit("calibre_diagnostic", **diagnostic)
    if diagnostic["issues"]:
        return 1
    executable = str(diagnostic["calibredb"])
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
            emit("book_preview", **_book_preview_payload(library, book_id))
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
    piper_exe: str | None = None,
    piper_voice_dir: str | None = None,
    piper_model: str | None = None,
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
            piper_exe=piper_exe,
            piper_voice_dir=piper_voice_dir,
            piper_model=piper_model,
        )
        output = library.render_book(
            book_id,
            output_format=output_format,
            provider=tts_provider,
            voice=voice,
            rate=rate,
            limit=limit,
            ffmpeg=ffmpeg,
            progress_callback=lambda payload: emit("job_progress", job="render", **payload),
        )
        outputs_payload = library.list_outputs(book_id)
        emit("job_progress", job="render", progress=100)
        emit("outputs", outputs=outputs_payload)
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
    piper_exe: str | None = None,
    piper_voice_dir: str | None = None,
    piper_model: str | None = None,
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
        piper_exe=piper_exe,
        piper_voice_dir=piper_voice_dir,
        piper_model=piper_model,
    )


def _tts_provider(
    provider: str,
    *,
    audio_cpp_exe: str | None,
    audio_cpp_model: str | None,
    audio_cpp_backend: str,
    audio_cpp_family: str | None,
    piper_exe: str | None = None,
    piper_voice_dir: str | None = None,
    piper_model: str | None = None,
) -> TtsProvider:
    if provider == "audio_cpp":
        audio_cpp_exe = audio_cpp_exe or (str(DEFAULT_AUDIO_CPP_EXE) if DEFAULT_AUDIO_CPP_EXE.exists() else None)
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
    if provider == "piper":
        executable = piper_exe or (str(DEFAULT_PIPER_EXE) if DEFAULT_PIPER_EXE.exists() else None)
        voice_dir = piper_voice_dir or (str(DEFAULT_PIPER_VOICE_DIR) if DEFAULT_PIPER_VOICE_DIR.exists() else None)
        if not executable:
            raise RuntimeError("Piper executable is required")
        return PiperProvider(executable, voice_dir=voice_dir, model=piper_model)
    return WindowsSapiProvider()


def _book_text(library_root: Path, book_id: str) -> str:
    library = BookLibrary(library_root)
    try:
        book = library.get_book(book_id)
        if not book:
            raise ValueError(f"Unknown book id: {book_id}")
        return "\n\n".join(str(chapter["text"]) for chapter in library.get_chapters(book_id))
    finally:
        library.close()


def _book_preview_payload(library: BookLibrary, book_id: str, max_chars: int = 1400) -> dict[str, object]:
    book = library.get_book(book_id)
    if not book:
        raise ValueError(f"Unknown book id: {book_id}")
    chapters = library.get_chapters(book_id)
    chunks = library.get_chunks(book_id)
    preview_parts: list[str] = []
    for chapter in chapters[:5]:
        text = str(chapter["text"]).strip().replace("\r\n", "\n")
        preview_parts.append(f"# {chapter['title']}\n{text[:max_chars]}")
    return {
        "book": book,
        "chapters": [
            {
                "index": chapter["chapter_index"],
                "title": chapter["title"],
                "chars": len(str(chapter["text"])),
            }
            for chapter in chapters
        ],
        "chunk_count": len(chunks),
        "chunks": [
            {
                "chapter_index": chunk["chapter_index"],
                "chunk_index": chunk["chunk_index"],
                "chars": len(str(chunk["text"])),
                "text_hash": chunk["text_hash"],
                "status": chunk["status"],
                "preview": str(chunk["text"]).strip().replace("\r\n", "\n")[:240],
            }
            for chunk in chunks[:12]
        ],
        "first_chunk": chunks[0] if chunks else None,
        "preview": "\n\n".join(preview_parts)[:max_chars],
    }


def _source_files(source: Path) -> list[Path]:
    source = Path(source)
    if source.is_dir():
        files = sorted(
            path
            for path in source.rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        if not files:
            raise ValueError(f"No supported source files found in folder: {source}")
        return files
    return [source]


def _parse_voice_entries(entries: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for entry in entries:
        if "=" not in entry:
            raise ValueError(f"Invalid voice mapping: {entry!r}; expected speaker=voice")
        speaker, voice = entry.split("=", 1)
        speaker = speaker.strip()
        voice = voice.strip()
        if not speaker or not voice:
            raise ValueError(f"Invalid voice mapping: {entry!r}; expected speaker=voice")
        mapping[speaker] = voice
    return mapping


def run_safely(fn, *args: Any, **kwargs: Any) -> int:
    try:
        return int(fn(*args, **kwargs))
    except Exception as exc:  # noqa: BLE001 - bridge must return structured errors.
        emit("error", message=str(exc), error_type=exc.__class__.__name__)
        return 1
