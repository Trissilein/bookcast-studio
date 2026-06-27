from __future__ import annotations

import json
from pathlib import Path

from bookcast.calibre import CalibreBook
from bookcast.cli import main
from bookcast.tts import TtsProvider, TtsVoice


def _events(output: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in output.splitlines() if line.strip()]


def test_bridge_import_and_list_emit_jsonl(tmp_path: Path, capsys) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Bridge Book.md"
    source.write_text("# Bridge Book\n\nBody.", encoding="utf-8")

    result = main(["bridge", "import", str(source), "--library", str(library_root)])
    import_events = _events(capsys.readouterr().out)

    assert result == 0
    assert [event["event"] for event in import_events] == ["job_started", "job_progress", "job_done", "book_preview"]
    assert import_events[2]["book_id"]
    assert import_events[3]["book"]["title"] == "Bridge Book"
    assert import_events[3]["chunk_count"] >= 1

    result = main(["bridge", "list", "--library", str(library_root)])
    list_events = _events(capsys.readouterr().out)

    assert result == 0
    assert list_events[0]["event"] == "books"
    assert list_events[0]["books"][0]["title"] == "Bridge Book"

    result = main(["bridge", "list", "--library", str(library_root), "--preview-first"])
    preview_events = _events(capsys.readouterr().out)

    assert result == 0
    assert [event["event"] for event in preview_events] == ["books", "book_preview"]
    assert preview_events[1]["book"]["title"] == "Bridge Book"


def test_bridge_errors_are_structured(tmp_path: Path, capsys) -> None:
    result = main(["bridge", "import", str(tmp_path / "missing.epub"), "--library", str(tmp_path / "library")])
    events = _events(capsys.readouterr().out)

    assert result == 1
    assert events[-1]["event"] == "error"
    assert events[-1]["error_type"] in {"FileNotFoundError", "ValueError"}


def test_bridge_calibre_import_emits_progress(tmp_path: Path, capsys, monkeypatch) -> None:
    exported = tmp_path / "Ada Author - Calibre Bridge.txt"
    exported.write_text("Calibre text.", encoding="utf-8")

    class FakeCalibreClient:
        def __init__(self, library_path: Path, calibredb: str = "calibredb") -> None:
            self.library_path = library_path

        def scan(self, search=None, limit=None):
            return [
                CalibreBook(id="7", title="Calibre Bridge", authors="Ada Author", formats=("TXT",), uuid="uuid-7")
            ]

        def export_book(self, book: CalibreBook, fmt: str) -> Path:
            assert book.id == "7"
            assert fmt == "TXT"
            return exported

    monkeypatch.setattr("bookcast.bridge.CalibreClient", FakeCalibreClient)
    monkeypatch.setattr(
        "bookcast.bridge.diagnose_calibre_library",
        lambda path, calibredb=None: {
            "healthy": True,
            "calibre_library": str(path),
            "library_exists": True,
            "is_dir": True,
            "metadata_db": str(Path(path) / "metadata.db"),
            "metadata_db_exists": True,
            "calibredb": "calibredb",
            "readable": True,
            "sample_count": 1,
            "issues": [],
            "hints": [],
        },
    )
    result = main(
        [
            "bridge",
            "calibre-import",
            str(tmp_path / "Calibre Library"),
            "--library",
            str(tmp_path / "library"),
            "--id",
            "7",
        ]
    )
    events = _events(capsys.readouterr().out)

    assert result == 0
    assert [event["event"] for event in events] == [
        "calibre_diagnostic",
        "job_started",
        "calibre_imported",
        "job_progress",
        "book_preview",
        "job_done",
    ]
    assert events[-1]["imported"][0]["calibre_id"] == "7"
    assert events[-2]["book"]["title"] == "Calibre Bridge"


def test_bridge_calibre_scan_explains_bad_library_path(tmp_path: Path, capsys, monkeypatch) -> None:
    wrong_folder = tmp_path / "Author Folder"
    wrong_folder.mkdir()
    monkeypatch.setattr("bookcast.calibre.find_calibredb", lambda: "calibredb.exe")

    result = main(["bridge", "calibre-scan", str(wrong_folder)])
    events = _events(capsys.readouterr().out)

    assert result == 1
    assert events[0]["event"] == "calibre_diagnostic"
    assert events[0]["healthy"] is False
    assert events[0]["issues"] == [f"metadata.db not found in: {wrong_folder}"]
    assert "Calibre library root" in events[0]["hints"][0]


def test_bridge_book_preview_and_sample_render(tmp_path: Path, capsys, monkeypatch) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Preview Book.txt"
    source.write_text("First sample chunk.\n\nSecond sample chunk.", encoding="utf-8")

    main(["bridge", "import", str(source), "--library", str(library_root)])
    import_events = _events(capsys.readouterr().out)
    book_id = str(next(event["book_id"] for event in import_events if event.get("event") == "job_done"))

    result = main(["bridge", "book-preview", book_id, "--library", str(library_root)])
    preview_events = _events(capsys.readouterr().out)

    assert result == 0
    assert preview_events[0]["event"] == "book_preview"
    assert preview_events[0]["book"]["title"] == "Preview Book"
    assert preview_events[0]["chunk_count"] >= 1
    assert "First sample chunk" in preview_events[0]["preview"]

    class FakeProvider(TtsProvider):
        id = "fake"

        def health(self) -> bool:
            return True

        def list_voices(self):
            return []

        def synthesize(self, text: str, output_wav: Path, voice: str | None = None, rate: int = 0) -> None:
            output_wav.parent.mkdir(parents=True, exist_ok=True)
            output_wav.write_bytes(b"RIFFfakeWAVE")

    def fake_assemble(chunk_wavs, output_path, output_format, ffmpeg="ffmpeg", chapters=None):
        output_path.write_bytes(b"audio")
        return output_path

    monkeypatch.setattr("bookcast.bridge.WindowsSapiProvider", FakeProvider)
    monkeypatch.setattr("bookcast.library.assemble_audio", fake_assemble)

    result = main(["bridge", "sample-render", book_id, "--library", str(library_root)])
    sample_events = _events(capsys.readouterr().out)

    assert result == 0
    assert sample_events[0]["event"] == "job_started"
    assert any(
        event.get("event") == "job_progress"
        and event.get("phase") == "tts"
        and event.get("chunk") == event.get("total")
        for event in sample_events
    )
    assert any(event.get("event") == "job_progress" and event.get("phase") == "assemble" for event in sample_events)
    assert sample_events[-1]["event"] == "job_done"
    assert sample_events[-1]["output"]

    result = main(["bridge", "outputs", "--library", str(library_root), "--book-id", book_id])
    output_events = _events(capsys.readouterr().out)

    assert result == 0
    assert output_events[0]["event"] == "outputs"
    assert output_events[0]["outputs"][0]["path"] == sample_events[-1]["output"]


def test_bridge_voices_emit_provider_voices(capsys, monkeypatch) -> None:
    class FakeProvider(TtsProvider):
        id = "fake"

        def health(self) -> bool:
            return True

        def list_voices(self):
            return [TtsVoice(id="Voice A", label="Voice A", locale="en-US")]

        def synthesize(self, text: str, output_wav: Path, voice: str | None = None, rate: int = 0) -> None:
            raise AssertionError("not used")

    monkeypatch.setattr("bookcast.bridge.WindowsSapiProvider", FakeProvider)

    result = main(["bridge", "voices"])
    events = _events(capsys.readouterr().out)

    assert result == 0
    assert events == [
        {
            "event": "voices",
            "provider": "fake",
            "voices": [{"id": "Voice A", "label": "Voice A", "locale": "en-US"}],
        }
    ]


def test_bridge_audio_cpp_health_reports_missing_config(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.setattr("bookcast.bridge.DEFAULT_AUDIO_CPP_EXE", tmp_path / "missing.exe")

    result = main(["bridge", "audio-cpp-health"])
    events = _events(capsys.readouterr().out)

    assert result == 1
    assert events == [
        {
            "event": "audio_cpp_health",
            "healthy": False,
            "executable": "",
            "model": "",
            "backend": "cpu",
            "family": "",
            "issues": [
                "audio.cpp executable is not configured",
                "audio.cpp model is not configured",
            ],
        }
    ]


def test_bridge_audio_cpp_health_accepts_working_provider(tmp_path: Path, capsys, monkeypatch) -> None:
    exe = tmp_path / "audio-cpp.exe"
    model = tmp_path / "model.gguf"
    exe.write_text("fake", encoding="utf-8")
    model.write_text("fake", encoding="utf-8")

    class FakeAudioCppProvider:
        def __init__(self, executable: str, model: str, backend: str = "cpu", family: str | None = None) -> None:
            self.executable = executable
            self.model = model
            self.backend = backend
            self.family = family

        def health(self) -> bool:
            return True

    monkeypatch.setattr("bookcast.bridge.AudioCppProvider", FakeAudioCppProvider)

    result = main(
        [
            "bridge",
            "audio-cpp-health",
            "--audio-cpp-exe",
            str(exe),
            "--audio-cpp-model",
            str(model),
        ]
    )
    events = _events(capsys.readouterr().out)

    assert result == 0
    assert events[0]["event"] == "audio_cpp_health"
    assert events[0]["healthy"] is True
    assert events[0]["issues"] == []


def test_bridge_voices_can_use_piper_provider(capsys, monkeypatch) -> None:
    class FakePiperProvider:
        id = "piper"

        def __init__(self, executable: str, voice_dir: str | None = None, model: str | None = None) -> None:
            self.executable = executable
            self.voice_dir = voice_dir
            self.model = model

        def health(self) -> bool:
            return True

        def list_voices(self):
            return [TtsVoice(id="voice.onnx", label="Test Piper", locale="de_DE")]

        def synthesize(self, text: str, output_wav: Path, voice: str | None = None, rate: int = 0) -> None:
            raise AssertionError("not used")

    monkeypatch.setattr("bookcast.bridge.PiperProvider", FakePiperProvider)

    result = main(["bridge", "voices", "--provider", "piper", "--piper-exe", "piper.exe"])
    events = _events(capsys.readouterr().out)

    assert result == 0
    assert events == [
        {
            "event": "voices",
            "provider": "piper",
            "voices": [{"id": "voice.onnx", "label": "Test Piper", "locale": "de_DE"}],
        }
    ]


def test_bridge_characters_emit_candidates(tmp_path: Path, capsys, monkeypatch) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Character Book.txt"
    source.write_text("Ada said hello. Narrator explains.", encoding="utf-8")

    main(["bridge", "import", str(source), "--library", str(library_root)])
    book_id = str(next(event["book_id"] for event in _events(capsys.readouterr().out) if event.get("event") == "job_done"))

    class FakeOllama:
        def __init__(self, model: str, base_url: str) -> None:
            self.model = model
            self.base_url = base_url

        def health(self) -> bool:
            return True

        def generate(self, prompt: str, mode: str = "json") -> str:
            return '{"characters":[{"name":"Ada","role":"character","evidence":"dialogue"}]}'

    monkeypatch.setattr("bookcast.bridge.OllamaProvider", FakeOllama)

    result = main(["bridge", "characters", book_id, "--library", str(library_root)])
    events = _events(capsys.readouterr().out)

    assert result == 0
    assert [event["event"] for event in events] == ["job_started", "job_progress", "characters", "job_done"]
    assert events[2]["candidates"][0]["name"] == "Ada"


def test_bridge_podcast_script_and_render_emit_jsonl(tmp_path: Path, capsys, monkeypatch) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Podcast Book.txt"
    source.write_text("A short article about careful engineering.", encoding="utf-8")

    main(["bridge", "import", str(source), "--library", str(library_root)])
    book_id = str(next(event["book_id"] for event in _events(capsys.readouterr().out) if event.get("event") == "job_done"))

    class FakeOllama:
        def __init__(self, model: str, base_url: str) -> None:
            self.model = model
            self.base_url = base_url

        def health(self) -> bool:
            return True

        def generate(self, prompt: str, mode: str = "json") -> str:
            return (
                '{"title":"Engineering Cast","summary":"Short.",'
                '"speakers":["host","explainer"],'
                '"turns":[{"speaker":"host","text":"Welcome."},{"speaker":"explainer","text":"Care helps."}]}'
            )

    class FakeProvider(TtsProvider):
        id = "fake"

        def health(self) -> bool:
            return True

        def list_voices(self):
            return [TtsVoice(id="Narrator", label="Narrator")]

        def synthesize(self, text: str, output_wav: Path, voice: str | None = None, rate: int = 0) -> None:
            output_wav.parent.mkdir(parents=True, exist_ok=True)
            output_wav.write_bytes(b"RIFFfakeWAVE")

    def fake_assemble(chunk_wavs, output_path, output_format, ffmpeg="ffmpeg", chapters=None):
        output_path.write_bytes(b"podcast")
        return output_path

    monkeypatch.setattr("bookcast.bridge.OllamaProvider", FakeOllama)
    monkeypatch.setattr("bookcast.bridge.WindowsSapiProvider", FakeProvider)
    monkeypatch.setattr("bookcast.library.assemble_audio", fake_assemble)
    monkeypatch.setattr("bookcast.library.probe_duration", lambda path: 1.0)

    result = main(["bridge", "podcast-script", book_id, "--library", str(library_root)])
    script_events = _events(capsys.readouterr().out)

    assert result == 0
    assert script_events[2]["event"] == "podcast_script"
    assert script_events[2]["script"]["title"] == "Engineering Cast"
    assert script_events[-1]["path"].endswith("Engineering Cast.json")

    result = main(
        [
            "bridge",
            "podcast-render",
            book_id,
            "--library",
            str(library_root),
            "--voice",
            "host=Narrator",
            "--voice",
            "explainer=Narrator",
        ]
    )
    render_events = _events(capsys.readouterr().out)

    assert result == 0
    rendered_script_events = [event for event in render_events if event.get("event") == "podcast_script"]
    assert rendered_script_events
    assert any(
        event.get("event") == "job_progress"
        and event.get("job") == "podcast_render"
        and event.get("phase") == "tts"
        for event in render_events
    )
    assert render_events[-1]["event"] == "job_done"
    assert render_events[-1]["output"].endswith(".opus")
