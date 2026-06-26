from __future__ import annotations

import argparse
from pathlib import Path

from .library import BookLibrary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bookcast")
    sub = parser.add_subparsers(dest="command", required=True)

    import_parser = sub.add_parser("import", help="Import a TXT, MD, or EPUB source into a library")
    import_parser.add_argument("file", type=Path)
    import_parser.add_argument("--library", type=Path, required=True)

    list_parser = sub.add_parser("list", help="List imported books")
    list_parser.add_argument("--library", type=Path, required=True)

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

    parser.error("unknown command")
    return 2

