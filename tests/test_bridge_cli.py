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
    assert [event["event"] for event in import_events] == ["job_started", "job_progress", "job_done"]
    assert import_events[-1]["book_id"]

    result = main(["bridge", "list", "--library", str(library_root)])
    list_events = _events(capsys.readouterr().out)

    assert result == 0
    assert list_events[0]["event"] == "books"
    assert list_events[0]["books"][0]["title"] == "Bridge Book"


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
        "job_started",
        "calibre_imported",
        "job_progress",
        "job_done",
    ]
    assert events[-1]["imported"][0]["calibre_id"] == "7"


def test_bridge_book_preview_and_sample_render(tmp_path: Path, capsys, monkeypatch) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Preview Book.txt"
    source.write_text("First sample chunk.\n\nSecond sample chunk.", encoding="utf-8")

    main(["bridge", "import", str(source), "--library", str(library_root)])
    import_events = _events(capsys.readouterr().out)
    book_id = str(import_events[-1]["book_id"])

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


def test_bridge_characters_emit_candidates(tmp_path: Path, capsys, monkeypatch) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Character Book.txt"
    source.write_text("Ada said hello. Narrator explains.", encoding="utf-8")

    main(["bridge", "import", str(source), "--library", str(library_root)])
    book_id = str(_events(capsys.readouterr().out)[-1]["book_id"])

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
    book_id = str(_events(capsys.readouterr().out)[-1]["book_id"])

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
    assert render_events[2]["event"] == "podcast_script"
    assert render_events[-1]["event"] == "job_done"
    assert render_events[-1]["output"].endswith(".opus")
