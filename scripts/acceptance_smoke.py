from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


DEFAULT_PIPER_EXE = Path(r"D:\GIT\Trispr_Flow\src-tauri\bin\piper\piper.exe")
DEFAULT_PIPER_VOICE_DIR = Path(r"D:\GIT\Trispr_Flow\src-tauri\bin\piper\voices")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run BookCast end-to-end acceptance smoke.")
    parser.add_argument("--library", type=Path, default=None)
    parser.add_argument("--keep", action="store_true", help="Keep temporary library/source files.")
    parser.add_argument("--skip-render", action="store_true", help="Stop before TTS/ffmpeg render.")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    temp_dir = Path(tempfile.mkdtemp(prefix="bookcast-acceptance-"))
    library = args.library or temp_dir / "library"
    source = temp_dir / "Ada Author - Acceptance Smoke.txt"
    source.write_text(
        "Chapter one starts here. This is a short acceptance sample.\n\n"
        "Second paragraph exists so cleanup and chunking have real input.",
        encoding="utf-8",
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
        require("Acceptance Smoke" in str(preview.get("preview", "")), "Import preview missing expected text")

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
                ["render", book_id, "--library", str(library), "--format", "opus", "--voice", voice],
            )
            assert_event(rendered, "job_done")
            output_path = Path(str(first_event(rendered, "job_done")["output"]))
            require_audio_file(repo, output_path, "Render output")

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

        print(json.dumps({"ok": True, "library": str(library), "book_id": book_id}, indent=2))
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


def require(value: object, message: str) -> None:
    if not value:
        raise RuntimeError(message)


if __name__ == "__main__":
    raise SystemExit(main())
