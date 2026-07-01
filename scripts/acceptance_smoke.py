from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


DEFAULT_PIPER_EXE = Path(r"D:\GIT\Trispr_Flow\src-tauri\bin\piper\piper.exe")
DEFAULT_PIPER_VOICE_DIR = Path(r"D:\GIT\Trispr_Flow\src-tauri\bin\piper\voices")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run BookCast end-to-end acceptance smoke.")
    parser.add_argument("--library", type=Path, default=None)
    parser.add_argument("--keep", action="store_true", help="Keep temporary library/source files.")
    parser.add_argument("--skip-render", action="store_true", help="Stop before TTS/ffmpeg render.")
    parser.add_argument("--long", action="store_true", help="Generate a longer synthetic German EPUB for manual queue tests.")
    parser.add_argument("--chapters", type=int, default=24, help="Chapter count for --long.")
    parser.add_argument("--render-limit", type=int, default=None, help="Limit full renders to the first N chunks.")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    temp_dir = Path(tempfile.mkdtemp(prefix="bookcast-acceptance-"))
    library = args.library or temp_dir / "library"
    source = temp_dir / ("Ada Autor - Langer Warteschlangen Test.epub" if args.long else "Ada Autor - Akzeptanz Rauchtest.epub")
    chapters = long_chapters(args.chapters) if args.long else [
        (
            "Kapitel Eins",
            "Das erste Kapitel beginnt hier. Dies ist ein kurzer deutscher EPUB-Rauchtest.",
        ),
        (
            "Kapitel Zwei",
            "Das zweite Kapitel ist kurz, muss aber eine echte M4B-Kapitelmarke erzeugen.",
        ),
    ]
    write_acceptance_epub(
        source,
        title="Langer Warteschlangen Test" if args.long else "Akzeptanz Rauchtest",
        author="Ada Autor",
        chapters=chapters,
    )

    try:
        diagnose = run_bridge(repo, ["diagnose", "--library", str(library)])
        assert_event(diagnose, "diagnostic")
        require(diagnose[0].get("ffmpeg"), "ffmpeg missing from PATH")
        require(diagnose[0].get("ffprobe"), "ffprobe missing from PATH")
        require(diagnose[0].get("windows_sapi"), "Windows SAPI unavailable")

        voices = run_bridge(repo, ["voices"])
        assert_event(voices, "voices")
        require(voices[0].get("voices"), "No TTS voices discovered")
        voice = str(voices[0]["voices"][0]["id"])

        imported = run_bridge(repo, ["import", str(source), "--library", str(library)])
        assert_event(imported, "job_done")
        book_id = str(first_event(imported, "job_done")["book_id"])

        preview = first_event(imported, "book_preview")
        require("Das erste Kapitel beginnt" in str(preview.get("preview", "")), "Import preview missing expected text")
        chunk_count = int(preview.get("chunk_count", 0) or 0)

        if not args.skip_render:
            sample = run_bridge(
                repo,
                ["sample-render", book_id, "--library", str(library), "--format", "opus", "--voice", voice],
            )
            assert_event(sample, "job_done")
            sample_path = Path(str(first_event(sample, "job_done")["output"]))
            require_audio_file(repo, sample_path, "Sample output")

            rendered = run_bridge(
                repo,
                render_args(book_id, library, "opus", voice, args.render_limit),
            )
            assert_event(rendered, "job_done")
            output_path = Path(str(first_event(rendered, "job_done")["output"]))
            require_audio_file(repo, output_path, "Render output")

            rendered_m4b = run_bridge(
                repo,
                render_args(book_id, library, "m4b", voice, args.render_limit),
            )
            assert_event(rendered_m4b, "job_done")
            m4b_path = Path(str(first_event(rendered_m4b, "job_done")["output"]))
            require_audio_file(repo, m4b_path, "M4B render output")
            require_chapters(repo, m4b_path, 1 if args.render_limit else 2)

            outputs = run_bridge(repo, ["outputs", "--library", str(library), "--book-id", book_id])
            assert_event(outputs, "outputs")
            require(outputs[0].get("outputs"), "Outputs list is empty after render")

            if DEFAULT_PIPER_EXE.exists() and DEFAULT_PIPER_VOICE_DIR.exists():
                piper_voices = run_bridge(
                    repo,
                    [
                        "voices",
                        "--provider",
                        "piper",
                        "--piper-exe",
                        str(DEFAULT_PIPER_EXE),
                        "--piper-voice-dir",
                        str(DEFAULT_PIPER_VOICE_DIR),
                    ],
                )
                assert_event(piper_voices, "voices")
                require(piper_voices[0].get("voices"), "No Piper voices discovered")
                piper_voice = str(piper_voices[0]["voices"][0]["id"])
                piper_sample = run_bridge(
                    repo,
                    [
                        "sample-render",
                        book_id,
                        "--library",
                        str(library),
                        "--format",
                        "opus",
                        "--provider",
                        "piper",
                        "--piper-exe",
                        str(DEFAULT_PIPER_EXE),
                        "--piper-voice-dir",
                        str(DEFAULT_PIPER_VOICE_DIR),
                        "--voice",
                        piper_voice,
                    ],
                )
                assert_event(piper_sample, "job_done")
                piper_path = Path(str(first_event(piper_sample, "job_done")["output"]))
                require_audio_file(repo, piper_path, "Piper sample output")

        print(json.dumps({"ok": True, "library": str(library), "book_id": book_id, "chunk_count": chunk_count}, indent=2))
        return 0
    finally:
        if args.library is None and not args.keep:
            shutil.rmtree(temp_dir, ignore_errors=True)


def run_bridge(repo: Path, args: list[str]) -> list[dict[str, object]]:
    proc = subprocess.run(
        [python(repo), "-m", "bookcast", "bridge", *args],
        cwd=repo,
        env={**dict_environ(), "PYTHONPATH": str(repo / "src")},
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Bridge command failed: {' '.join(args)}\n{proc.stdout}\n{proc.stderr}")
    events = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    require(events, f"Bridge command emitted no events: {' '.join(args)}")
    return events


def render_args(book_id: str, library: Path, output_format: str, voice: str, limit: int | None) -> list[str]:
    args = ["render", book_id, "--library", str(library), "--format", output_format, "--voice", voice]
    if limit:
        args.extend(["--limit", str(limit)])
    return args


def long_chapters(count: int) -> list[tuple[str, str]]:
    count = max(4, count)
    paragraphs = []
    base = (
        "Das erste Kapitel beginnt hier. Dieser Abschnitt simuliert ein langes deutsches Sachbuch. "
        "Die Saetze sind absichtlich normal lang, damit BookCast viele stabile Chunks erzeugt. "
        "Ada erklaert den Plan, Bob stellt Rueckfragen, und die Erzaehlerin fasst den Fortschritt zusammen."
    )
    for index in range(1, count + 1):
        text = "\n\n".join(
            f"{base} Abschnitt {index}.{part} prueft Warteschlange, Fortschritt, Abbruch und Wiederaufnahme."
            for part in range(1, 7)
        )
        paragraphs.append((f"Kapitel {index:02d}", text))
    return paragraphs


def write_acceptance_epub(path: Path, *, title: str, author: str, chapters: list[tuple[str, str]]) -> None:
    manifest_items = "\n".join(
        f'<item id="c{index}" href="text/chapter{index}.xhtml" media-type="application/xhtml+xml"/>'
        for index, _chapter in enumerate(chapters, start=1)
    )
    spine_items = "\n".join(f'<itemref idref="c{index}"/>' for index, _chapter in enumerate(chapters, start=1))
    nav_points = "\n".join(
        f"""
        <navPoint id="navPoint-{index}" playOrder="{index}">
          <navLabel><text>{xml_escape(chapter_title)}</text></navLabel>
          <content src="text/chapter{index}.xhtml"/>
        </navPoint>"""
        for index, (chapter_title, _chapter_text) in enumerate(chapters, start=1)
    )
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
        )
        zf.writestr(
            "OEBPS/content.opf",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">bookcast-acceptance</dc:identifier>
    <dc:title>{xml_escape(title)}</dc:title>
    <dc:creator>{xml_escape(author)}</dc:creator>
    <dc:language>de</dc:language>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    {manifest_items}
  </manifest>
  <spine toc="ncx">
    {spine_items}
  </spine>
</package>""",
        )
        zf.writestr(
            "OEBPS/toc.ncx",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head><meta name="dtb:uid" content="bookcast-acceptance"/></head>
  <docTitle><text>{xml_escape(title)}</text></docTitle>
  <navMap>{nav_points}
  </navMap>
</ncx>""",
        )
        for index, (chapter_title, chapter_text) in enumerate(chapters, start=1):
            zf.writestr(
                f"OEBPS/text/chapter{index}.xhtml",
                f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <body>
    <h1>{xml_escape(chapter_title)}</h1>
    <p>{xml_escape(chapter_text)}</p>
  </body>
</html>""",
            )


def xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def python(repo: Path) -> str:
    venv = repo / ".venv" / "Scripts" / "python.exe"
    return str(venv) if venv.exists() else sys.executable


def dict_environ() -> dict[str, str]:
    import os

    return dict(os.environ)


def assert_event(events: list[dict[str, object]], name: str) -> None:
    require(any(event.get("event") == name for event in events), f"Missing event: {name}")


def first_event(events: list[dict[str, object]], name: str) -> dict[str, object]:
    for event in events:
        if event.get("event") == name:
            return event
    raise RuntimeError(f"Missing event: {name}")


def require_audio_file(repo: Path, path: Path, label: str) -> None:
    require(path.exists(), f"{label} missing: {path}")
    require(path.stat().st_size > 0, f"{label} is empty: {path}")
    duration = ffprobe_duration(repo, path)
    require(duration > 0.0, f"{label} has no positive duration: {path}")


def require_chapters(repo: Path, path: Path, minimum: int) -> None:
    count = ffprobe_chapter_count(repo, path)
    require(count >= minimum, f"Expected at least {minimum} chapter(s), found {count}: {path}")


def ffprobe_duration(repo: Path, path: Path) -> float:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"ffprobe failed for {path}: {detail}")
    try:
        return float(proc.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(f"ffprobe returned invalid duration for {path}: {proc.stdout!r}") from exc


def ffprobe_chapter_count(repo: Path, path: Path) -> int:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_chapters",
            str(path),
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"ffprobe chapter probe failed for {path}: {detail}")
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ffprobe returned invalid chapter JSON for {path}: {proc.stdout!r}") from exc
    return len(data.get("chapters") or [])


def require(value: object, message: str) -> None:
    if not value:
        raise RuntimeError(message)


if __name__ == "__main__":
    raise SystemExit(main())
