from __future__ import annotations

import subprocess
from pathlib import Path


SUPPORTED_OUTPUT_FORMATS = {"opus", "mp3", "wav", "m4b"}


def assemble_audio(
    chunk_wavs: list[Path],
    output_path: Path,
    output_format: str,
    ffmpeg: str = "ffmpeg",
    chapters: list[tuple[str, float]] | None = None,
) -> Path:
    output_format = output_format.lower()
    if output_format not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError(f"Unsupported output format: {output_format}")
    if not chunk_wavs:
        raise ValueError("No rendered chunks to assemble")
    if output_format == "m4b":
        return assemble_m4b(chunk_wavs, output_path, chapters=chapters or [], ffmpeg=ffmpeg)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    concat_file = output_path.parent / f"{output_path.stem}.concat.txt"
    concat_file.write_text(
        "\n".join(f"file '{_ffmpeg_path(path)}'" for path in chunk_wavs),
        encoding="utf-8",
    )
    try:
        if output_format == "opus":
            args = [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-ac",
                "1",
                "-c:a",
                "libopus",
                "-b:a",
                "32k",
                "-vbr",
                "on",
                str(output_path),
            ]
        elif output_format == "mp3":
            args = [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-ac",
                "1",
                "-c:a",
                "libmp3lame",
                "-b:a",
                "128k",
                str(output_path),
            ]
        else:
            args = [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-ac",
                "1",
                str(output_path),
            ]
        _run_ffmpeg(args)
        return output_path
    finally:
        concat_file.unlink(missing_ok=True)


def assemble_m4b(
    chunk_wavs: list[Path],
    output_path: Path,
    chapters: list[tuple[str, float]],
    ffmpeg: str = "ffmpeg",
) -> Path:
    if not chunk_wavs:
        raise ValueError("No rendered chunks to assemble")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    concat_file = output_path.parent / f"{output_path.stem}.concat.txt"
    metadata_file = output_path.parent / f"{output_path.stem}.chapters.ffmetadata"
    temp_audio = output_path.with_suffix(".m4a")
    concat_file.write_text(
        "\n".join(f"file '{_ffmpeg_path(path)}'" for path in chunk_wavs),
        encoding="utf-8",
    )
    try:
        _run_ffmpeg(
            [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-ac",
                "1",
                "-c:a",
                "aac",
                "-b:a",
                "64k",
                str(temp_audio),
            ]
        )
        metadata_file.write_text(_ffmetadata(chapters), encoding="utf-8")
        _run_ffmpeg(
            [
                ffmpeg,
                "-y",
                "-i",
                str(temp_audio),
                "-i",
                str(metadata_file),
                "-map_metadata",
                "1",
                "-codec",
                "copy",
                "-movflags",
                "+faststart",
                str(output_path),
            ]
        )
        return output_path
    finally:
        concat_file.unlink(missing_ok=True)
        metadata_file.unlink(missing_ok=True)
        temp_audio.unlink(missing_ok=True)


def probe_duration(path: Path, ffprobe: str = "ffprobe") -> float:
    try:
        proc = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(_missing_tool_message("ffprobe", ffprobe)) from exc
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"ffprobe duration failed: {detail}")
    return float(proc.stdout.strip())


def chapter_timeline(
    rendered_chunks: list[tuple[int, Path]],
    chapter_titles: dict[int, str],
    ffprobe: str = "ffprobe",
) -> list[tuple[str, float]]:
    timeline: list[tuple[str, float]] = []
    current_chapter: int | None = None
    elapsed = 0.0
    for chapter_index, path in rendered_chunks:
        if chapter_index != current_chapter:
            timeline.append((chapter_titles.get(chapter_index, f"Chapter {chapter_index + 1}"), elapsed))
            current_chapter = chapter_index
        elapsed += probe_duration(path, ffprobe=ffprobe)
    return timeline


def _ffmetadata(chapters: list[tuple[str, float]]) -> str:
    lines = [";FFMETADATA1"]
    for index, (title, start_sec) in enumerate(chapters):
        end_sec = chapters[index + 1][1] if index + 1 < len(chapters) else start_sec + 1
        lines.extend(
            [
                "[CHAPTER]",
                "TIMEBASE=1/1000",
                f"START={max(0, int(start_sec * 1000))}",
                f"END={max(int(start_sec * 1000) + 1, int(end_sec * 1000))}",
                f"title={_escape_metadata(title)}",
            ]
        )
    return "\n".join(lines) + "\n"


def _run_ffmpeg(args: list[str]) -> None:
    try:
        proc = subprocess.run(args, check=False, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError(_missing_tool_message("ffmpeg", args[0] if args else "ffmpeg")) from exc
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"ffmpeg assembly failed: {detail}")


def _missing_tool_message(tool: str, configured: str) -> str:
    return (
        f"{tool} not found: {configured}. Install ffmpeg and add it to PATH, "
        f"or configure the full path to {tool}.exe."
    )


def _ffmpeg_path(path: Path) -> str:
    return str(Path(path).resolve()).replace("\\", "/").replace("'", "'\\''")


def _escape_metadata(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace("=", "\\=")
