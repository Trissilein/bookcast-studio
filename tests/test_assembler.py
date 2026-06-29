from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from bookcast.assembler import assemble_audio, probe_duration


def test_assemble_audio_explains_missing_ffmpeg(tmp_path: Path, monkeypatch) -> None:
    chunk = tmp_path / "chunk.wav"
    chunk.write_bytes(b"RIFFfakeWAVE")

    def missing_tool(args, check=False, capture_output=True, text=True):
        raise FileNotFoundError(args[0])

    monkeypatch.setattr(subprocess, "run", missing_tool)

    with pytest.raises(RuntimeError) as error:
        assemble_audio([chunk], tmp_path / "out.opus", "opus", ffmpeg="missing-ffmpeg.exe")

    assert str(error.value) == (
        "ffmpeg not found: missing-ffmpeg.exe. Install ffmpeg and add it to PATH, "
        "or configure the full path to ffmpeg.exe."
    )


def test_probe_duration_explains_missing_ffprobe(tmp_path: Path, monkeypatch) -> None:
    audio = tmp_path / "chunk.wav"
    audio.write_bytes(b"RIFFfakeWAVE")

    def missing_tool(args, check=False, capture_output=True, text=True):
        raise FileNotFoundError(args[0])

    monkeypatch.setattr(subprocess, "run", missing_tool)

    with pytest.raises(RuntimeError) as error:
        probe_duration(audio, ffprobe="missing-ffprobe.exe")

    assert str(error.value) == (
        "ffprobe not found: missing-ffprobe.exe. Install ffmpeg and add it to PATH, "
        "or configure the full path to ffprobe.exe."
    )
