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
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(f'BT /F1 24 Tf 72 720 Td ({escaped}) Tj ET'.encode('ascii'))} >>\nstream\nBT /F1 24 Tf 72 720 Td ({escaped}) Tj ET\nendstream".encode("ascii"),
    ]
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
