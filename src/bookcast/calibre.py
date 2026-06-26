from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_IMPORT_FORMATS = ("EPUB", "TXT", "MD")


@dataclass(frozen=True)
class CalibreBook:
    id: str
    title: str
    authors: str
    formats: tuple[str, ...]
    uuid: str | None = None
    language: str | None = None
    series: str | None = None
    series_index: str | None = None

    def preferred_format(self, preference: tuple[str, ...] = SUPPORTED_IMPORT_FORMATS) -> str | None:
        available = {fmt.upper() for fmt in self.formats}
        for fmt in preference:
            if fmt.upper() in available:
                return fmt.upper()
        return None


class CalibreClient:
    def __init__(self, library_path: Path, calibredb: str = "calibredb") -> None:
        self.library_path = Path(library_path)
        self.calibredb = calibredb

    def scan(self, search: str | None = None, limit: int | None = None) -> list[CalibreBook]:
        args = [
            self.calibredb,
            "list",
            "--library-path",
            str(self.library_path),
            "--for-machine",
            "--fields",
            "id,title,authors,formats,languages,uuid,series,series_index",
        ]
        if search:
            args.extend(["--search", search])
        if limit:
            args.extend(["--limit", str(limit)])
        output = self._run(args)
        return parse_calibre_list(output)

    def export_book(self, book: CalibreBook, fmt: str) -> Path:
        fmt = fmt.upper()
        with tempfile.TemporaryDirectory(prefix="bookcast-calibre-") as tmp:
            tmp_path = Path(tmp)
            args = [
                self.calibredb,
                "export",
                "--library-path",
                str(self.library_path),
                "--to-dir",
                str(tmp_path),
                "--single-dir",
                "--formats",
                fmt,
                "--dont-write-opf",
                "--dont-save-cover",
                "--dont-save-extra-files",
                book.id,
            ]
            self._run(args)
            candidates = sorted(tmp_path.glob(f"*.{fmt.lower()}")) + sorted(tmp_path.glob(f"*.{fmt}"))
            if not candidates:
                raise RuntimeError(f"Calibre exported no {fmt} file for book {book.id}")
            exported = candidates[0]
            stable_tmp = Path(tempfile.mkdtemp(prefix="bookcast-calibre-export-"))
            target = stable_tmp / exported.name
            shutil.copy2(exported, target)
            return target

    def _run(self, args: list[str]) -> str:
        try:
            proc = subprocess.run(args, check=False, text=True, capture_output=True)
        except FileNotFoundError as exc:
            raise RuntimeError("calibredb not found. Install Calibre or configure calibredb path.") from exc
        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip()
            raise RuntimeError(f"calibredb failed: {detail}")
        return proc.stdout


def find_calibredb() -> str | None:
    found = shutil.which("calibredb")
    if found:
        return found
    candidates = [
        Path("C:/Program Files/Calibre2/calibredb.exe"),
        Path("C:/Program Files (x86)/Calibre2/calibredb.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def parse_calibre_list(output: str) -> list[CalibreBook]:
    data = json.loads(output or "[]")
    books: list[CalibreBook] = []
    for item in data:
        formats = item.get("formats") or []
        if isinstance(formats, str):
            formats = [part.strip() for part in formats.split(",") if part.strip()]
        authors = item.get("authors") or "Unknown Author"
        if isinstance(authors, list):
            authors = ", ".join(str(author) for author in authors)
        languages = item.get("languages") or []
        language = None
        if isinstance(languages, list) and languages:
            language = str(languages[0])
        elif isinstance(languages, str) and languages:
            language = languages
        books.append(
            CalibreBook(
                id=str(item.get("id")),
                title=str(item.get("title") or "Untitled"),
                authors=str(authors),
                formats=tuple(str(fmt).upper() for fmt in formats),
                uuid=item.get("uuid"),
                language=language,
                series=item.get("series"),
                series_index=str(item.get("series_index")) if item.get("series_index") is not None else None,
            )
        )
    return books
