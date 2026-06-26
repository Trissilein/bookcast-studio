from __future__ import annotations

import argparse
from pathlib import Path

from .calibre import CalibreClient, find_calibredb
from .library import BookLibrary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bookcast")
    sub = parser.add_subparsers(dest="command", required=True)

    import_parser = sub.add_parser("import", help="Import a TXT, MD, or EPUB source into a library")
    import_parser.add_argument("file", type=Path)
    import_parser.add_argument("--library", type=Path, required=True)

    list_parser = sub.add_parser("list", help="List imported books")
    list_parser.add_argument("--library", type=Path, required=True)

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

    parser.error("unknown command")
    return 2
