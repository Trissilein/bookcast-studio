from __future__ import annotations

import subprocess
from pathlib import Path


SUPPORTED_OUTPUT_FORMATS = {"opus", "mp3", "wav"}


def assemble_audio(chunk_wavs: list[Path], output_path: Path, output_format: str, ffmpeg: str = "ffmpeg") -> Path:
    output_format = output_format.lower()
    if output_format not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError(f"Unsupported output format: {output_format}")
    if not chunk_wavs:
        raise ValueError("No rendered chunks to assemble")

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
        proc = subprocess.run(args, check=False, capture_output=True, text=True)
        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip()
            raise RuntimeError(f"ffmpeg assembly failed: {detail}")
        return output_path
    finally:
        concat_file.unlink(missing_ok=True)


def _ffmpeg_path(path: Path) -> str:
    return str(Path(path).resolve()).replace("\\", "/").replace("'", "'\\''")

