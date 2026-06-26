from __future__ import annotations

import html
import posixpath
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

from .models import Chapter, Document, Metadata
from .text_pipeline import clean_text

SUPPORTED_EXTENSIONS = {".txt", ".md", ".epub", ".pdf", ".docx"}


def probe(path: Path) -> Metadata:
    path = Path(path)
    _ensure_supported(path)
    if path.suffix.lower() == ".epub":
        try:
            return _epub_metadata(path)
        except Exception:
            pass
    title, author = title_author_from_filename(path.stem)
    return Metadata(title=title, author=author)


def extract(path: Path) -> Document:
    path = Path(path)
    _ensure_supported(path)
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return _extract_text_file(path)
    if suffix == ".epub":
        return _extract_epub(path)
    if suffix == ".docx":
        return _extract_docx(path)
    if suffix == ".pdf":
        return _extract_pdf(path)
    raise ValueError(f"Unsupported source format: {suffix}")


def title_author_from_filename(stem: str) -> tuple[str, str]:
    stem = re.sub(r"[_]+", " ", stem).strip()
    stem = re.sub(r"\s+", " ", stem)
    if " - " not in stem:
        return stem or "Untitled", "Unknown Author"

    first, second = [p.strip() for p in stem.split(" - ", 1)]
    title_first = ("der ", "die ", "das ", "the ", "a ", "an ", "ein ", "eine ")
    if first.lower().startswith(title_first):
        return first or "Untitled", second or "Unknown Author"
    return second or "Untitled", first or "Unknown Author"


def _ensure_supported(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported source format: {suffix}")


def _extract_text_file(path: Path) -> Document:
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    text = clean_text(raw)
    metadata = probe(path)
    chapter = Chapter(index=0, title=metadata.title, text=text)
    return Document(source_path=path, metadata=metadata, chapters=[chapter], raw_text=text)


def _epub_metadata(path: Path) -> Metadata:
    with zipfile.ZipFile(path) as zf:
        opf_path = _find_opf_path(zf)
        opf = ET.fromstring(zf.read(opf_path))
    ns = {
        "opf": "http://www.idpf.org/2007/opf",
        "dc": "http://purl.org/dc/elements/1.1/",
    }
    title = _xml_text(opf.find(".//dc:title", ns)) or path.stem
    author = _xml_text(opf.find(".//dc:creator", ns)) or "Unknown Author"
    language = _xml_text(opf.find(".//dc:language", ns))
    return Metadata(title=html.unescape(title).strip(), author=html.unescape(author).strip(), language=language)


def _extract_epub(path: Path) -> Document:
    with zipfile.ZipFile(path) as zf:
        opf_path = _find_opf_path(zf)
        opf_dir = posixpath.dirname(opf_path)
        opf = ET.fromstring(zf.read(opf_path))
        metadata = _epub_metadata(path)
        spine_items = _epub_spine_items(opf, opf_dir)
        chapters: list[Chapter] = []
        texts: list[str] = []
        for index, item_path in enumerate(spine_items):
            try:
                raw_html = zf.read(item_path).decode("utf-8", errors="replace")
            except KeyError:
                continue
            text = clean_text(_html_to_text(raw_html))
            if not text:
                continue
            title = _first_heading(raw_html) or f"Chapter {len(chapters) + 1}"
            chapters.append(Chapter(index=len(chapters), title=title, text=text))
            texts.append(text)

    if not chapters:
        raise ValueError(f"No readable chapters found in EPUB: {path}")
    return Document(source_path=path, metadata=metadata, chapters=chapters, raw_text="\n\n".join(texts))


def _extract_docx(path: Path) -> Document:
    metadata = probe(path)
    with zipfile.ZipFile(path) as zf:
        try:
            document_xml = zf.read("word/document.xml")
        except KeyError as exc:
            raise ValueError(f"DOCX has no word/document.xml: {path}") from exc
    root = ET.fromstring(document_xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", ns):
        texts = [node.text or "" for node in paragraph.findall(".//w:t", ns)]
        line = clean_text("".join(texts))
        if line:
            paragraphs.append(line)
    text = clean_text("\n\n".join(paragraphs))
    if not text:
        raise ValueError(f"No readable text found in DOCX: {path}")
    return Document(
        source_path=path,
        metadata=metadata,
        chapters=[Chapter(index=0, title=metadata.title, text=text)],
        raw_text=text,
    )


def _extract_pdf(path: Path) -> Document:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF import requires pypdf. Install with: python -m pip install -e .[dev]") from exc

    metadata = probe(path)
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        text = clean_text(text)
        if text:
            pages.append(text)
    raw_text = clean_text("\n\n".join(pages))
    if not raw_text:
        raise ValueError(f"No readable text found in PDF: {path}")
    chapters = [Chapter(index=i, title=f"Page {i + 1}", text=text) for i, text in enumerate(pages)]
    return Document(source_path=path, metadata=metadata, chapters=chapters, raw_text=raw_text)


def _find_opf_path(zf: zipfile.ZipFile) -> str:
    container = ET.fromstring(zf.read("META-INF/container.xml"))
    ns = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
    rootfile = container.find(".//c:rootfile", ns)
    if rootfile is None:
        raise ValueError("EPUB container has no rootfile")
    full_path = rootfile.attrib.get("full-path")
    if not full_path:
        raise ValueError("EPUB rootfile is missing full-path")
    return full_path


def _epub_spine_items(opf: ET.Element, opf_dir: str) -> list[str]:
    ns = {"opf": "http://www.idpf.org/2007/opf"}
    manifest = {
        item.attrib["id"]: item.attrib.get("href", "")
        for item in opf.findall(".//opf:manifest/opf:item", ns)
        if "id" in item.attrib
    }
    paths: list[str] = []
    for itemref in opf.findall(".//opf:spine/opf:itemref", ns):
        href = manifest.get(itemref.attrib.get("idref", ""))
        if href:
            paths.append(posixpath.normpath(posixpath.join(opf_dir, href)))
    return paths


def _xml_text(node: ET.Element | None) -> str | None:
    return node.text.strip() if node is not None and node.text else None


def _html_to_text(raw_html: str) -> str:
    parser = _TextHTMLParser()
    parser.feed(raw_html)
    return parser.text()


def _first_heading(raw_html: str) -> str | None:
    match = re.search(r"<h[1-3][^>]*>(.*?)</h[1-3]>", raw_html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return clean_text(re.sub(r"<[^>]+>", "", html.unescape(match.group(1))))


class _TextHTMLParser(HTMLParser):
    BLOCK_TAGS = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "section"}

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self.BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if data.strip():
            self._parts.append(html.unescape(data))

    def text(self) -> str:
        return clean_text(" ".join(self._parts))
