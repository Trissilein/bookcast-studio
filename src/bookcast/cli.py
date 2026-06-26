from __future__ import annotations

import argparse
import json
from pathlib import Path

from .assembler import assemble_audio
from .calibre import CalibreClient, find_calibredb
from .characters import suggest_characters
from .library import BookLibrary, safe_name
from .llm import OllamaProvider
from .podcast import PODCAST_MODES, PodcastTurn, generate_interactive_step, generate_podcast_script
from .tts import WindowsSapiProvider, play_wav


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bookcast")
    sub = parser.add_subparsers(dest="command", required=True)

    import_parser = sub.add_parser("import", help="Import a TXT, MD, or EPUB source into a library")
    import_parser.add_argument("file", type=Path)
    import_parser.add_argument("--library", type=Path, required=True)
    import_parser.add_argument("--cleanup-profile", default="standard")

    list_parser = sub.add_parser("list", help="List imported books")
    list_parser.add_argument("--library", type=Path, required=True)

    render_parser = sub.add_parser("render", help="Render a book to audio")
    render_parser.add_argument("book_id")
    render_parser.add_argument("--library", type=Path, required=True)
    render_parser.add_argument("--format", choices=["opus", "mp3", "wav", "m4b"], default="opus")
    render_parser.add_argument("--voice", default=None)
    render_parser.add_argument("--rate", type=int, default=0)
    render_parser.add_argument("--limit", type=int, default=None, help="Render only the first N chunks")
    render_parser.add_argument("--ffmpeg", default="ffmpeg")

    characters_parser = sub.add_parser("characters", help="LLM-assisted character tools")
    characters_sub = characters_parser.add_subparsers(dest="characters_command", required=True)
    characters_suggest = characters_sub.add_parser("suggest", help="Suggest speakers/characters for a book")
    characters_suggest.add_argument("book_id")
    characters_suggest.add_argument("--library", type=Path, required=True)
    characters_suggest.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    characters_suggest.add_argument("--model", default="qwen3:8b")

    podcast_parser = sub.add_parser("podcast", help="Static podcast generation")
    podcast_sub = podcast_parser.add_subparsers(dest="podcast_command", required=True)
    podcast_script = podcast_sub.add_parser("script", help="Generate a static podcast script from a book")
    podcast_script.add_argument("book_id")
    podcast_script.add_argument("--library", type=Path, required=True)
    podcast_script.add_argument("--mode", choices=sorted(PODCAST_MODES), default="educational")
    podcast_script.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    podcast_script.add_argument("--model", default="qwen3:8b")

    podcast_render = podcast_sub.add_parser("render", help="Generate and render a podcast episode")
    podcast_render.add_argument("book_id")
    podcast_render.add_argument("--library", type=Path, required=True)
    podcast_render.add_argument("--mode", choices=sorted(PODCAST_MODES), default="educational")
    podcast_render.add_argument("--format", choices=["opus", "mp3", "wav", "m4b"], default="opus")
    podcast_render.add_argument("--voice", action="append", default=[], help="Speaker=Voice mapping")
    podcast_render.add_argument("--rate", type=int, default=0)
    podcast_render.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    podcast_render.add_argument("--model", default="qwen3:8b")
    podcast_render.add_argument("--ffmpeg", default="ffmpeg")

    podcast_interactive = podcast_sub.add_parser("interactive", help="Run a live interactive podcast session")
    podcast_interactive.add_argument("book_id")
    podcast_interactive.add_argument("--library", type=Path, required=True)
    podcast_interactive.add_argument("--mode", choices=sorted(PODCAST_MODES), default="educational")
    podcast_interactive.add_argument("--format", choices=["opus", "mp3", "wav", "m4b"], default="opus")
    podcast_interactive.add_argument("--voice", action="append", default=[], help="Speaker=Voice mapping")
    podcast_interactive.add_argument("--rate", type=int, default=0)
    podcast_interactive.add_argument("--turns", type=int, default=6)
    podcast_interactive.add_argument("--playback", action=argparse.BooleanOptionalAction, default=True)
    podcast_interactive.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    podcast_interactive.add_argument("--model", default="qwen3:8b")
    podcast_interactive.add_argument("--ffmpeg", default="ffmpeg")
    podcast_interactive.add_argument("--seed-prompt", default=None)

    calibre_parser = sub.add_parser("calibre", help="Import from a Calibre library")
    calibre_sub = calibre_parser.add_subparsers(dest="calibre_command", required=True)

    calibre_scan = calibre_sub.add_parser("scan", help="List supported Calibre books")
    calibre_scan.add_argument("calibre_library", type=Path)
    calibre_scan.add_argument("--calibredb", default=None)
    calibre_scan.add_argument("--search", default=None)
    calibre_scan.add_argument("--limit", type=int, default=None)

    calibre_import = calibre_sub.add_parser("import", help="Import selected Calibre books")
    calibre_import.add_argument("calibre_library", type=Path)
    calibre_import.add_argument("--library", type=Path, required=True)
    calibre_import.add_argument("--calibredb", default=None)
    calibre_import.add_argument("--id", action="append", dest="ids", default=[])
    calibre_import.add_argument("--search", default=None)
    calibre_import.add_argument("--limit", type=int, default=None)
    calibre_import.add_argument("--cleanup-profile", default="standard")

    args = parser.parse_args(argv)
    if args.command == "import":
        library = BookLibrary(args.library)
        try:
            book_id = library.import_source(args.file, cleanup_profile=args.cleanup_profile)
            book = library.get_book(book_id)
        finally:
            library.close()
        print(f"Imported {book['author']} - {book['title']} ({book_id})")
        return 0

    if args.command == "list":
        library = BookLibrary(args.library)
        try:
            for book in library.list_books():
                print(
                    f"{book['id']} | {book['author']} | {book['title']} | {book['cleanup_profile']} | "
                    f"{book['chapter_count']} chapters | {book['chunk_count']} chunks | {book['status']}"
                )
        finally:
            library.close()
        return 0

    if args.command == "calibre":
        calibredb = args.calibredb or find_calibredb() or "calibredb"
        client = CalibreClient(args.calibre_library, calibredb=calibredb)
        books = client.scan(search=args.search, limit=args.limit)
        supported = [book for book in books if book.preferred_format()]

        if args.calibre_command == "scan":
            for book in supported:
                print(f"{book.id} | {book.authors} | {book.title} | {', '.join(book.formats)}")
            skipped = len(books) - len(supported)
            if skipped:
                print(f"Skipped {skipped} books without EPUB/TXT/MD")
            return 0

        if args.calibre_command == "import":
            selected = supported
            if args.ids:
                wanted = set(args.ids)
                selected = [book for book in supported if book.id in wanted]
            library = BookLibrary(args.library)
            try:
                for book in selected:
                    book_id = library.import_calibre_book(client, book, cleanup_profile=args.cleanup_profile)
                    print(f"Imported Calibre {book.id}: {book.authors} - {book.title} ({book_id})")
            finally:
                library.close()
            return 0

    if args.command == "render":
        library = BookLibrary(args.library)
        try:
            output = library.render_book(
                args.book_id,
                output_format=args.format,
                voice=args.voice,
                rate=args.rate,
                limit=args.limit,
                ffmpeg=args.ffmpeg,
            )
        finally:
            library.close()
        print(f"Rendered {output}")
        return 0

    if args.command == "characters":
        library = BookLibrary(args.library)
        try:
            text = library.get_book_text(args.book_id)
        finally:
            library.close()
        provider = OllamaProvider(model=args.model, base_url=args.ollama_url)
        if not provider.health():
            raise SystemExit(f"Ollama is not reachable at {args.ollama_url}")
        candidates = suggest_characters(text, provider)
        print(json.dumps([candidate.__dict__ for candidate in candidates], ensure_ascii=False, indent=2))
        return 0

    if args.command == "podcast":
        library = BookLibrary(args.library)
        try:
            text = library.get_book_text(args.book_id)
            provider = OllamaProvider(model=args.model, base_url=args.ollama_url)
            if not provider.health():
                raise SystemExit(f"Ollama is not reachable at {args.ollama_url}")
            if args.podcast_command == "script":
                script = generate_podcast_script(text, provider, mode=args.mode)
                output = library.save_podcast_script(args.book_id, script.to_dict())
                print(f"Wrote podcast script {output}")
                return 0
            if args.podcast_command == "render":
                script = generate_podcast_script(text, provider, mode=args.mode)
                voice_map = _parse_voice_map(args.voice)
                output = library.render_podcast_script(
                    args.book_id,
                    script,
                    output_format=args.format,
                    voice_map=voice_map,
                    ffmpeg=args.ffmpeg,
                    rate=args.rate,
                )
                print(f"Rendered podcast {output}")
                return 0
            if args.podcast_command == "interactive":
                voice_map = _parse_voice_map(args.voice)
                output = _run_interactive_podcast(
                    library=library,
                    book_id=args.book_id,
                    provider=provider,
                    mode=args.mode,
                    output_format=args.format,
                    voice_map=voice_map,
                    rate=args.rate,
                    turns=args.turns,
                    playback=args.playback,
                    ffmpeg=args.ffmpeg,
                    seed_prompt=args.seed_prompt,
                )
                print(f"Rendered interactive podcast {output}")
                return 0
        finally:
            library.close()

    parser.error("unknown command")
    return 2


def _parse_voice_map(entries: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for entry in entries:
        if "=" not in entry:
            raise SystemExit(f"Invalid --voice mapping: {entry!r}; expected speaker=voice")
        speaker, voice = entry.split("=", 1)
        speaker = speaker.strip()
        voice = voice.strip()
        if not speaker or not voice:
            raise SystemExit(f"Invalid --voice mapping: {entry!r}; expected speaker=voice")
        mapping[speaker] = voice
    return mapping


def _run_interactive_podcast(
    *,
    library: BookLibrary,
    book_id: str,
    provider: OllamaProvider,
    mode: str,
    output_format: str,
    voice_map: dict[str, str],
    rate: int,
    turns: int,
    playback: bool,
    ffmpeg: str,
    seed_prompt: str | None,
) -> Path:
    book = library.get_book(book_id)
    if not book:
        raise SystemExit(f"Unknown book id: {book_id}")
    if not provider.health():
        raise SystemExit(f"Ollama is not reachable at {provider.base_url}")
    text = library.get_book_text(book_id)
    tts = WindowsSapiProvider()
    if not tts.health():
        raise SystemExit("Windows SAPI is not available")

    speaker_names = list(voice_map) or ["host"]
    library.sync_speakers(book_id, speaker_names, voice_map=voice_map, provider=tts.id)

    session_dir = library.root / "books" / book_id / "podcasts" / "interactive" / safe_name(str(book["title"]))
    session_dir.mkdir(parents=True, exist_ok=True)
    state_path = session_dir / "session.json"
    transcript: list[PodcastTurn] = []
    rendered_segments: list[Path] = []
    interruption = seed_prompt

    for turn_index in range(max(1, turns)):
        step = generate_interactive_step(text, provider, mode, transcript, interruption=interruption)
        wav_path = session_dir / f"turn_{turn_index:03d}_{safe_name(step.speaker)}.wav"
        tts.synthesize(step.text, wav_path, voice=voice_map.get(step.speaker), rate=rate)
        rendered_segments.append(wav_path)
        transcript.append(PodcastTurn(speaker=step.speaker, text=step.text))
        state_path.write_text(
            json.dumps(
                {
                    "book_id": book_id,
                    "mode": mode,
                    "turns": [turn.__dict__ for turn in transcript],
                    "follow_up": step.follow_up,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"[{turn_index + 1}] {step.speaker}: {step.text}")
        if step.follow_up:
            print(f"Follow-up: {step.follow_up}")
        if playback:
            play_wav(wav_path)

        if turn_index + 1 >= turns:
            break
        try:
            interruption = input("Interrupt / follow-up (Enter to continue, q to stop): ").strip()
        except EOFError:
            interruption = ""
        if interruption.lower() in {"q", "quit", "stop"}:
            break
        if not interruption:
            interruption = step.follow_up or None

    output_dir = session_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_name(str(book['author']))} - {safe_name(str(book['title']))}_interactive.{output_format.lower()}"
    assemble_audio(rendered_segments, output_path, output_format, ffmpeg=ffmpeg)
    library.add_output(book_id, output_format, output_path)
    return output_path
