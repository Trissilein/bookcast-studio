from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_IMPORT_FORMATS = ("EPUB", "DOCX", "TXT", "MD", "PDF")
SUPPORTED_IMPORT_SUFFIXES = tuple(f".{fmt.lower()}" for fmt in SUPPORTED_IMPORT_FORMATS)


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


def diagnose_calibre_library(library_path: Path, calibredb: str | None = None) -> dict[str, object]:
    path = Path(library_path)
    executable = calibredb or find_calibredb()
    issues: list[str] = []
    hints: list[str] = []
    metadata_db = path / "metadata.db"
    suggested_library = ""
    candidate_libraries: list[str] = []
    source_file_candidates: list[str] = []
    readable = False
    sample_count: int | None = None

    if not path.exists():
        issues.append(f"Calibre library path does not exist: {path}")
        hints.append("Choose the Calibre library root folder, not an individual EPUB file.")
    elif not path.is_dir():
        issues.append(f"Calibre library path is not a folder: {path}")
        hints.append("Choose the folder that contains metadata.db.")
    elif not metadata_db.exists():
        parent_db = path.parent / "metadata.db"
        if parent_db.exists():
            suggested_library = str(path.parent)
            issues.append(f"metadata.db not found in: {path}")
            hints.append(f"Selected folder looks like a Calibre subfolder. Use parent library: {path.parent}")
        else:
            candidate_libraries = _calibre_library_candidates(path)
            if candidate_libraries:
                issues.append(f"metadata.db not found in: {path}")
                hints.append(
                    "Selected folder contains possible Calibre libraries. Choose one candidate below, not the parent folder."
                )
            else:
                source_file_candidates = _supported_source_files(path)
                issues.append(f"metadata.db not found in: {path}")
                if source_file_candidates:
                    hints.append(
                        "Selected folder contains supported ebook files but no Calibre metadata.db. Use Import Source -> Folder for raw EPUB/PDF/DOCX/TXT/MD folders, or choose the real Calibre library root."
                    )
                else:
                    hints.append("Choose the Calibre library root folder, not an author/book subfolder.")

    if not executable:
        issues.append("calibredb not found")
        hints.append("Install Calibre or pass --calibredb with the full path to calibredb.exe.")

    if not issues and executable:
        try:
            sample_count = len(CalibreClient(path, calibredb=executable).scan(limit=1))
            readable = True
        except RuntimeError as exc:
            issues.append(str(exc))
            hints.append("Close Calibre if it is locking the library, then retry.")

    return {
        "healthy": not issues,
        "calibre_library": str(path),
        "library_exists": path.exists(),
        "is_dir": path.is_dir(),
        "metadata_db": str(metadata_db),
        "metadata_db_exists": metadata_db.exists(),
        "suggested_library": suggested_library,
        "candidate_libraries": candidate_libraries,
        "source_file_candidates": source_file_candidates,
        "source_file_candidate_count": len(source_file_candidates),
        "calibredb": executable or "",
        "readable": readable,
        "sample_count": sample_count,
        "issues": issues,
        "hints": hints,
    }


def find_calibre_libraries(
    roots: list[Path] | None = None,
    *,
    limit: int = 8,
    max_depth: int = 4,
    environ: dict[str, str] | None = None,
) -> list[str]:
    search_roots = roots or _calibre_search_roots(environ or os.environ)
    found: list[str] = []
    seen: set[str] = set()
    for root in search_roots:
        root = Path(root).expanduser()
        if not root.exists() or not root.is_dir():
            continue
        candidates = [str(root)] if (root / "metadata.db").exists() else []
        candidates.extend(_calibre_library_candidates(root, limit=limit, max_depth=max_depth))
        for candidate in candidates:
            key = str(Path(candidate).resolve()).lower()
            if key in seen:
                continue
            seen.add(key)
            found.append(candidate)
            if len(found) >= limit:
                return found
    return found


def _calibre_search_roots(environ: dict[str, str]) -> list[Path]:
    raw_roots: list[str] = []
    for key in ("CALIBRE_LIBRARY", "CALIBRE_LIBRARY_DIRECTORY"):
        value = environ.get(key)
        if value:
            raw_roots.append(value)

    userprofile = environ.get("USERPROFILE")
    if userprofile:
        raw_roots.extend(
            [
                str(Path(userprofile) / "Calibre Library"),
                str(Path(userprofile) / "Documents"),
                str(Path(userprofile) / "OneDrive" / "Documents"),
            ]
        )
    for key in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        value = environ.get(key)
        if value:
            raw_roots.extend([str(Path(value) / "Calibre Library"), str(Path(value) / "Documents")])

    roots: list[Path] = []
    seen: set[str] = set()
    for raw in raw_roots:
        path = Path(raw)
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            roots.append(path)
    return roots


def _calibre_library_candidates(path: Path, limit: int = 8, max_depth: int = 4) -> list[str]:
    if not path.is_dir():
        return []
    candidates: list[str] = []
    try:
        root_depth = len(path.parts)
        for current, dirs, files in os_walk_sorted(path):
            if len(candidates) >= limit:
                break
            current_path = Path(current)
            depth = len(current_path.parts) - root_depth
            if depth > max_depth:
                dirs[:] = []
                continue
            if "metadata.db" in files:
                candidates.append(str(current_path))
                dirs[:] = []
                continue
            if depth >= max_depth:
                dirs[:] = []
    except OSError:
        return []
    return candidates


def _supported_source_files(path: Path, limit: int = 8, max_depth: int = 4) -> list[str]:
    if not path.is_dir():
        return []
    candidates: list[str] = []
    try:
        root_depth = len(path.parts)
        for current, dirs, files in os_walk_sorted(path):
            if len(candidates) >= limit:
                break
            current_path = Path(current)
            depth = len(current_path.parts) - root_depth
            if depth > max_depth:
                dirs[:] = []
                continue
            for name in files:
                if len(candidates) >= limit:
                    break
                if Path(name).suffix.lower() in SUPPORTED_IMPORT_SUFFIXES:
                    candidates.append(str(current_path / name))
            if depth >= max_depth:
                dirs[:] = []
    except OSError:
        return []
    return candidates


def os_walk_sorted(path: Path):
    import os

    for current, dirs, files in os.walk(path):
        dirs[:] = sorted([name for name in dirs if not name.startswith(".")], key=str.lower)
        files[:] = sorted(files, key=str.lower)
        yield current, dirs, files


def find_calibredb() -> str | None:
    found = shutil.which("calibredb")
    if found:
        return found
    for candidate in [*_calibredb_registry_paths(), *_calibredb_candidate_paths(os.environ)]:
        if candidate.exists():
            return str(candidate)
    return None


def _calibredb_candidate_paths(environ: dict[str, str]) -> list[Path]:
    raw_bases = [
        environ.get("ProgramFiles", "C:/Program Files"),
        environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"),
        environ.get("LOCALAPPDATA", ""),
        environ.get("APPDATA", ""),
        environ.get("USERPROFILE", ""),
        environ.get("ChocolateyInstall", ""),
    ]
    bases = [Path(base) for base in raw_bases if base]
    candidates: list[Path] = []
    for base in bases:
        candidates.extend(
            [
                base / "Calibre2" / "calibredb.exe",
                base / "calibre" / "calibredb.exe",
                base / "Programs" / "Calibre2" / "calibredb.exe",
                base / "Programs" / "calibre" / "calibredb.exe",
                base / "scoop" / "apps" / "calibre" / "current" / "calibredb.exe",
                base / "bin" / "calibredb.exe",
            ]
        )
    return list(dict.fromkeys(candidates))


def _calibredb_registry_paths() -> list[Path]:
    try:
        import winreg  # type: ignore[import-not-found]
    except ImportError:
        return []

    paths: list[Path] = []
    roots = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
    keys = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\calibre",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Calibre2",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\calibre",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Calibre2",
    ]
    for root in roots:
        for key in keys:
            try:
                with winreg.OpenKey(root, key) as handle:
                    install_location, _ = winreg.QueryValueEx(handle, "InstallLocation")
            except OSError:
                continue
            if install_location:
                paths.append(Path(str(install_location)) / "calibredb.exe")
    return list(dict.fromkeys(paths))


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
