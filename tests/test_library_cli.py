from __future__ import annotations

from pathlib import Path

from bookcast.cli import main
from bookcast.library import BookLibrary


def test_library_import_stores_book_chapters_chunks_and_source(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Plain Book.txt"
    source.write_text("Chapter text.\n\nMore text.", encoding="utf-8")

    library = BookLibrary(library_root)
    try:
        book_id = library.import_source(source)
        books = library.list_books()
    finally:
        library.close()

    assert book_id
    assert books[0]["title"] == "Plain Book"
    assert books[0]["author"] == "Ada Author"
    assert books[0]["chapter_count"] == 1
    assert books[0]["chunk_count"] == 1
    assert (library_root / "books" / book_id / "source" / source.name).exists()


def test_cli_import_smoke(tmp_path: Path, capsys) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - CLI Book.md"
    source.write_text("# Heading\n\nBody.", encoding="utf-8")

    result = main(["import", str(source), "--library", str(library_root)])

    assert result == 0
    assert "Imported Ada Author - CLI Book" in capsys.readouterr().out

