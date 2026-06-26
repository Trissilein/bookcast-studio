from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from bookcast.importers import extract, probe, title_author_from_filename


def test_title_author_from_filename_author_first() -> None:
    assert title_author_from_filename("Jane Doe - My Book") == ("My Book", "Jane Doe")


def test_title_author_from_filename_title_first_article() -> None:
    assert title_author_from_filename("The Long Road - Jane Doe") == ("The Long Road", "Jane Doe")


def test_txt_extract(tmp_path: Path) -> None:
    source = tmp_path / "Jane Doe - Notes.txt"
    source.write_text("Hello\n\nWorld", encoding="utf-8")

    document = extract(source)

    assert document.metadata.title == "Notes"
    assert document.metadata.author == "Jane Doe"
    assert document.chapters[0].text == "Hello\n\nWorld"


def test_docx_is_blocked_until_m2(tmp_path: Path) -> None:
    source = tmp_path / "book.docx"
    source.write_bytes(b"placeholder")

    with pytest.raises(ValueError, match="planned for M2"):
        probe(source)


def test_epub_extracts_metadata_and_chapters(tmp_path: Path) -> None:
    source = tmp_path / "sample.epub"
    _write_epub(source)

    document = extract(source)

    assert document.metadata.title == "Sample Book"
    assert document.metadata.author == "Ada Author"
    assert document.metadata.language == "en"
    assert len(document.chapters) == 2
    assert document.chapters[0].title == "Start"
    assert "First chapter text" in document.raw_text


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
                <dc:title>Sample Book</dc:title>
                <dc:creator>Ada Author</dc:creator>
                <dc:language>en</dc:language>
              </metadata>
              <manifest>
                <item id="c1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
                <item id="c2" href="chapter2.xhtml" media-type="application/xhtml+xml"/>
              </manifest>
              <spine>
                <itemref idref="c1"/>
                <itemref idref="c2"/>
              </spine>
            </package>
            """,
        )
        zf.writestr("OEBPS/chapter1.xhtml", "<html><body><h1>Start</h1><p>First chapter text.</p></body></html>")
        zf.writestr("OEBPS/chapter2.xhtml", "<html><body><h1>Next</h1><p>Second chapter text.</p></body></html>")

