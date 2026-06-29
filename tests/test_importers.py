from __future__ import annotations

import zipfile
from pathlib import Path

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


def test_docx_extract(tmp_path: Path) -> None:
    source = tmp_path / "Ada Author - Doc Book.docx"
    _write_docx(source, ["First paragraph.", "Second paragraph."])

    document = extract(source)

    assert document.metadata.title == "Doc Book"
    assert document.metadata.author == "Ada Author"
    assert "First paragraph." in document.raw_text
    assert "Second paragraph." in document.raw_text


def test_pdf_extract(tmp_path: Path) -> None:
    source = tmp_path / "Ada Author - Pdf Book.pdf"
    _write_pdf(source, "Hello PDF")

    document = extract(source)

    assert document.metadata.title == "Pdf Book"
    assert document.metadata.author == "Ada Author"
    assert "Hello PDF" in document.raw_text


def test_golden_messy_pdf_extracts_pages_and_cleans_text(tmp_path: Path) -> None:
    source = tmp_path / "Paper Lab - Messy Pdf.pdf"
    _write_pdf_pages(
        source,
        [
            ["Chapter 1   Overview", "This   page has    weird spacing.", "hyphen-", "ated line after extraction."],
            ["Chapter 2 Notes", "Second    page text."],
        ],
    )

    document = extract(source)

    assert document.metadata.title == "Messy Pdf"
    assert document.metadata.author == "Paper Lab"
    assert [chapter.title for chapter in document.chapters] == ["Page 1", "Page 2"]
    assert "Chapter 1 Overview" in document.raw_text
    assert "This page has weird spacing." in document.raw_text
    assert "hyphenated line after extraction." in document.raw_text
    assert "Second page text." in document.raw_text


def test_epub_extracts_metadata_and_chapters(tmp_path: Path) -> None:
    source = tmp_path / "sample.epub"
    _write_epub(
        source,
        title="Sample Book",
        author="Ada Author",
        language="en",
        chapters=[
            ("Start", "First chapter text."),
            ("Next", "Second chapter text."),
        ],
    )

    document = extract(source)

    assert document.metadata.title == "Sample Book"
    assert document.metadata.author == "Ada Author"
    assert document.metadata.language == "en"
    assert len(document.chapters) == 2
    assert document.chapters[0].title == "Start"
    assert "First chapter text" in document.raw_text


def test_golden_epub_samples_cover_german_and_english_metadata(tmp_path: Path) -> None:
    samples = [
        (
            "de",
            "Der große Anfang",
            "Erika Mustermann",
            [("Kapitel Eins", "Grüße aus München & Überblick."), ("Zweites Kapitel", "Noch ein deutscher Absatz.")],
        ),
        (
            "en",
            "The Small Voyage",
            "John Writer",
            [("Opening", "A clean English paragraph."), ("Landing", "Another chapter follows.")],
        ),
    ]

    for language, title, author, chapters in samples:
        source = tmp_path / f"{language}.epub"
        _write_epub(source, title=title, author=author, language=language, chapters=chapters)

        metadata = probe(source)
        document = extract(source)

        assert metadata.title == title
        assert metadata.author == author
        assert metadata.language == language
        assert document.metadata.title == title
        assert document.metadata.author == author
        assert document.metadata.language == language
        assert [chapter.title for chapter in document.chapters] == [chapter[0] for chapter in chapters]
        assert chapters[0][1].replace("&", "&") in document.raw_text


def _write_epub(path: Path, *, title: str, author: str, language: str, chapters: list[tuple[str, str]]) -> None:
    manifest_items = "\n".join(
        f'<item id="c{index}" href="text/chapter{index}.xhtml" media-type="application/xhtml+xml"/>'
        for index, _chapter in enumerate(chapters, start=1)
    )
    spine_items = "\n".join(f'<itemref idref="c{index}"/>' for index, _chapter in enumerate(chapters, start=1))

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
            f"""<?xml version="1.0" encoding="UTF-8"?>
            <package xmlns="http://www.idpf.org/2007/opf" version="3.0">
              <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
                <dc:title>{_xml_escape(title)}</dc:title>
                <dc:creator>{_xml_escape(author)}</dc:creator>
                <dc:language>{_xml_escape(language)}</dc:language>
              </metadata>
              <manifest>
                {manifest_items}
              </manifest>
              <spine>
                {spine_items}
              </spine>
            </package>
            """,
        )
        for index, (chapter_title, chapter_text) in enumerate(chapters, start=1):
            zf.writestr(
                f"OEBPS/text/chapter{index}.xhtml",
                f"<html><body><h1>{_xml_escape(chapter_title)}</h1><p>{_xml_escape(chapter_text)}</p></body></html>",
            )


def _xml_escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _write_docx(path: Path, paragraphs: list[str]) -> None:
    body = "".join(
        f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"
        for text in paragraphs
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}</w:body>"
        "</w:document>"
    )
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", "")
        zf.writestr("word/document.xml", document_xml)


def _write_pdf(path: Path, text: str) -> None:
    _write_pdf_pages(path, [[text]])


def _write_pdf_pages(path: Path, pages: list[list[str]]) -> None:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{' '.join(f'{4 + index * 2} 0 R' for index in range(len(pages)))}] /Count {len(pages)} >>".encode(
            "ascii"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    for index, lines in enumerate(pages):
        page_obj = 4 + index * 2
        content_obj = page_obj + 1
        stream = _pdf_text_stream(lines)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_obj} 0 R >>".encode(
                "ascii"
            )
        )
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream")

    parts = [b"%PDF-1.4\n"]
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(sum(len(part) for part in parts))
        parts.append(f"{index} 0 obj\n".encode("ascii") + obj + b"\nendobj\n")
    xref_offset = sum(len(part) for part in parts)
    parts.append(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        parts.append(f"{offset:010d} 00000 n \n".encode("ascii"))
    parts.append(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(b"".join(parts))


def _pdf_text_stream(lines: list[str]) -> bytes:
    commands = ["BT /F1 24 Tf 72 720 Td"]
    for index, line in enumerate(lines):
        if index:
            commands.append("0 -32 Td")
        commands.append(f"({_pdf_escape(line)}) Tj")
    commands.append("ET")
    return " ".join(commands).encode("ascii")


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
