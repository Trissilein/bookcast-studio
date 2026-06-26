from __future__ import annotations

import argparse
import json
from pathlib import Path

from .calibre import CalibreClient, find_calibredb
from .characters import suggest_characters
from .library import BookLibrary
from .llm import OllamaProvider
from .podcast import PODCAST_MODES, generate_podcast_script


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bookcast")
    sub = parser.add_subparsers(dest="command", required=True)

    import_parser = sub.add_parser("import", help="Import a TXT, MD, or EPUB source into a library")
    import_parser.add_argument("file", type=Path)
    import_parser.add_argument("--library", type=Path, required=True)

    list_parser = sub.add_parser("list", help="List imported books")
    list_parser.add_argument("--library", type=Path, required=True)

    render_parser = sub.add_parser("render", help="Render a book to audio")
    render_parser.add_argument("book_id")
    render_parser.add_argument("--library", type=Path, required=True)
    render_parser.add_argument("--format", choices=["opus", "mp3", "wav"], default="opus")
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

    args = parser.parse_args(argv)
    if args.command == "import":
        library = BookLibrary(args.library)
        try:
            book_id = library.import_source(args.file)
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
                    f"{book['id']} | {book['author']} | {book['title']} | "
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
                    book_id = library.import_calibre_book(client, book)
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
            script = generate_podcast_script(text, provider, mode=args.mode)
            output = library.save_podcast_script(args.book_id, script.to_dict())
        finally:
            library.close()
        print(f"Wrote podcast script {output}")
        return 0

    parser.error("unknown command")
    return 2
