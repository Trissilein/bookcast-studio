from __future__ import annotations

import subprocess
from pathlib import Path

from bookcast.tts import AudioCppProvider, audio_cpp_tts_families


def test_audio_cpp_provider_uses_real_cli_voice_ref(tmp_path: Path, monkeypatch) -> None:
    calls: list[list[str]] = []
    voice_ref = tmp_path / "voice.wav"
    voice_ref.write_bytes(b"RIFFvoiceWAVE")

    def fake_run(args, check=False, capture_output=True, text=True):
        calls.append(args)
        Path(args[args.index("--out") + 1]).write_bytes(b"RIFFoutWAVE")
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr("bookcast.tts.subprocess.run", fake_run)

    provider = AudioCppProvider("audiocpp_cli.exe", model="model.gguf", backend="cpu", family="kokoro")
    provider.synthesize("hello", tmp_path / "out.wav", voice=str(voice_ref), rate=2)

    args = calls[0]
    assert "--mode" in args
    assert args[args.index("--mode") + 1] == "offline"
    assert "--voice-ref" in args
    assert args[args.index("--voice-ref") + 1] == str(voice_ref)
    assert "--speaking-rate" in args
    assert args.count("--family") == 1
    assert args[args.index("--family") + 1] == "kokoro"
    assert "--voice" not in args
    assert "--rate" not in args


def test_audio_cpp_provider_maps_named_voice_to_voice_id(tmp_path: Path, monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(args, check=False, capture_output=True, text=True):
        calls.append(args)
        Path(args[args.index("--out") + 1]).write_bytes(b"RIFFoutWAVE")
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr("bookcast.tts.subprocess.run", fake_run)

    provider = AudioCppProvider("audiocpp_cli.exe", model="model.gguf", family="pocket_tts")
    provider.synthesize("hello", tmp_path / "out.wav", voice="Narrator")

    args = calls[0]
    assert "--voice-id" in args
    assert args[args.index("--voice-id") + 1] == "Narrator"
    assert "--voice-ref" not in args
    assert args.count("--family") == 1
    assert args[args.index("--family") + 1] == "pocket_tts"


def test_audio_cpp_provider_requires_family(tmp_path: Path) -> None:
    provider = AudioCppProvider("audiocpp_cli.exe", model="model.gguf")

    try:
        provider.synthesize("hello", tmp_path / "out.wav")
    except RuntimeError as error:
        assert str(error) == "audio.cpp family is required"
    else:
        raise AssertionError("expected missing family to fail")


def test_audio_cpp_tts_families_parse_help(monkeypatch) -> None:
    def fake_run(args, check=False, capture_output=True, text=True):
        assert args == ["audiocpp_cli.exe", "--help", "--task", "tts"]
        return subprocess.CompletedProcess(
            args,
            0,
            "task=tts\n  Registered families:\n    chatterbox\n    pocket_tts\n    qwen3_tts\n",
            "",
        )

    monkeypatch.setattr("bookcast.tts.subprocess.run", fake_run)

    assert audio_cpp_tts_families("audiocpp_cli.exe") == ["chatterbox", "pocket_tts", "qwen3_tts"]
