from __future__ import annotations

import json
import zipfile
from pathlib import Path

from bookcast.calibre import CalibreBook, diagnose_calibre_library, parse_calibre_list
from bookcast.library import BookLibrary


def test_parse_calibre_list_for_machine_json() -> None:
    output = json.dumps(
        [
            {
                "id": 7,
                "title": "Calibre Book",
                "authors": ["Ada Author"],
                "formats": ["EPUB", "PDF"],
                "languages": ["de"],
                "uuid": "abc-123",
            }
        ]
    )

    books = parse_calibre_list(output)

    assert books == [
        CalibreBook(
            id="7",
            title="Calibre Book",
            authors="Ada Author",
            formats=("EPUB", "PDF"),
            uuid="abc-123",
            language="de",
        )
    ]


def test_calibre_import_uses_external_id_for_dedupe(tmp_path: Path) -> None:
    exported = tmp_path / "exported.epub"
    _write_epub(exported)
    client = _FakeCalibreClient(tmp_path / "Calibre Library", exported)
    book = CalibreBook(
        id="42",
        title="Metadata Title",
        authors="Metadata Author",
        formats=("EPUB",),
        uuid="uuid-42",
        language="en",
    )
    library = BookLibrary(tmp_path / "bookcast")
    try:
        first = library.import_calibre_book(client, book)
        second = library.import_calibre_book(client, book)
        books = library.list_books()
    finally:
        library.close()

    assert first == second
    assert len(books) == 1
    assert books[0]["title"] == "Metadata Title"
    assert books[0]["author"] == "Metadata Author"


def test_calibre_diagnose_explains_wrong_folder(tmp_path: Path, monkeypatch) -> None:
    wrong_folder = tmp_path / "Author Name"
    wrong_folder.mkdir()
    monkeypatch.setattr("bookcast.calibre.find_calibredb", lambda: "calibredb.exe")

    diagnostic = diagnose_calibre_library(wrong_folder)

    assert diagnostic["healthy"] is False
    assert diagnostic["metadata_db_exists"] is False
    assert diagnostic["issues"] == [f"metadata.db not found in: {wrong_folder}"]
    assert diagnostic["hints"] == ["Choose the Calibre library root folder, not an author/book subfolder."]


class _FakeCalibreClient:
    def __init__(self, library_path: Path, exported: Path) -> None:
        self.library_path = library_path
        self.exported = exported

    def export_book(self, book: CalibreBook, fmt: str) -> Path:
        assert book.id == "42"
        assert fmt == "EPUB"
        return self.exported


def _write_epub(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
            <container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
              <rootfiles>
                <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
              </rootfiles>
            </container>
            """,
        )
        zf.writestr(
            "OEBPS/content.opf",
            """<?xml version="1.0" encoding="UTF-8"?>
            <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
              <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
                <dc:title>EPUB Title</dc:title>
                <dc:creator>EPUB Author</dc:creator>
                <dc:language>en</dc:language>
              </metadata>
              <manifest>
                <item id="c1" href="chapter.xhtml" media-type="application/xhtml+xml"/>
              </manifest>
              <spine>
                <itemref idref="c1"/>
              </spine>
            </package>
            """,
        )
        zf.writestr("OEBPS/chapter.xhtml", "<html><body><h1>Start</h1><p>Text.</p></body></html>")
