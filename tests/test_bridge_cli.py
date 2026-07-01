from __future__ import annotations

import json
from pathlib import Path

from bookcast.calibre import CalibreBook
from bookcast.cli import main
from bookcast.library import BookLibrary
from bookcast.tts import TtsProvider, TtsVoice


def _events(output: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in output.splitlines() if line.strip()]


def test_bridge_diagnose_uses_configured_media_tool_paths(tmp_path: Path, capsys) -> None:
    result = main(
        [
            "bridge",
            "diagnose",
            "--library",
            str(tmp_path / "library"),
            "--ffmpeg",
            r"D:\Tools\ffmpeg.exe",
            "--ffprobe",
            r"D:\Tools\ffprobe.exe",
        ]
    )
    events = _events(capsys.readouterr().out)

    assert result == 0
    assert events[0]["event"] == "diagnostic"
    assert events[0]["ffmpeg"] == r"D:\Tools\ffmpeg.exe"
    assert events[0]["ffprobe"] == r"D:\Tools\ffprobe.exe"


def test_bridge_import_and_list_emit_jsonl(tmp_path: Path, capsys) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Bridge Book.md"
    source.write_text("# Bridge Book\n\nBody.", encoding="utf-8")

    result = main(["bridge", "import", str(source), "--library", str(library_root)])
    import_events = _events(capsys.readouterr().out)

    assert result == 0
    assert [event["event"] for event in import_events] == [
        "job_started",
        "source_imported",
        "job_progress",
        "job_done",
        "book_preview",
    ]
    assert import_events[3]["book_id"]
    assert import_events[4]["book"]["title"] == "Bridge Book"
    assert import_events[4]["chunk_count"] >= 1

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


def test_bridge_import_folder_imports_supported_files(tmp_path: Path, capsys) -> None:
    library_root = tmp_path / "library"
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    (source_dir / "Ada Author - First Book.txt").write_text("First body.", encoding="utf-8")
    (source_dir / "Bea Author - Second Book.md").write_text("# Second\n\nSecond body.", encoding="utf-8")
    (source_dir / "skip.jpg").write_bytes(b"not a book")

    result = main(["bridge", "import", str(source_dir), "--library", str(library_root)])
    events = _events(capsys.readouterr().out)

    assert result == 0
    assert [event["event"] for event in events].count("source_imported") == 2
    assert events[-2]["count"] == 2
    assert events[-1]["event"] == "book_preview"


def test_bridge_import_folder_marks_duplicate_sources(tmp_path: Path, capsys) -> None:
    library_root = tmp_path / "library"
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    (source_dir / "Ada Author - One.txt").write_text("Same body.", encoding="utf-8")
    (source_dir / "Ada Author - One Copy.txt").write_text("Same body.", encoding="utf-8")

    result = main(["bridge", "import", str(source_dir), "--library", str(library_root)])
    events = _events(capsys.readouterr().out)
    imported = [event for event in events if event.get("event") == "source_imported"]

    assert result == 0
    assert [event["duplicate"] for event in imported] == [False, True]
    assert imported[0]["book_id"] == imported[1]["book_id"]
    assert events[-2]["count"] == 2


def test_bridge_source_probe_file_and_folder(tmp_path: Path, capsys) -> None:
    source = tmp_path / "Ada Author - Probe Book.md"
    source.write_text("# Probe Book\n\nPreview body.", encoding="utf-8")
    folder = tmp_path / "sources"
    folder.mkdir()
    (folder / "Ada Author - One.txt").write_text("One.", encoding="utf-8")
    (folder / "skip.jpg").write_bytes(b"skip")
    expected_text = "# Probe Book\n\nPreview body."
    expected_chapter_text = "Preview body."

    result = main(["bridge", "source-probe", str(source)])
    file_events = _events(capsys.readouterr().out)

    assert result == 0
    assert file_events == [
        {
            "event": "source_probe",
            "source": str(source),
            "kind": "file",
            "format": "md",
            "title": "Probe Book",
            "author": "Ada Author",
            "language": "",
            "chapter_count": 1,
            "chars": len(expected_text),
            "chapters": [{"index": 0, "title": "Probe Book", "chars": len(expected_chapter_text)}],
            "preview": expected_text,
        }
    ]

    result = main(["bridge", "source-probe", str(folder)])
    folder_events = _events(capsys.readouterr().out)

    assert result == 0
    assert folder_events[0]["event"] == "source_probe"
    assert folder_events[0]["kind"] == "folder"
    assert folder_events[0]["supported_count"] == 1
    assert folder_events[0]["files"][0]["name"] == "Ada Author - One.txt"


def test_bridge_cleanup_profiles_and_rechunk(tmp_path: Path, capsys) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Cleanup Book.txt"
    source.write_text("One. Two. Three. Four.", encoding="utf-8")

    main(["bridge", "import", str(source), "--library", str(library_root)])
    book_id = str(
        next(event["book_id"] for event in _events(capsys.readouterr().out) if event.get("event") == "job_done")
    )

    library = BookLibrary(library_root)
    try:
        library.upsert_cleanup_profile("tiny", {"max_chars": 8})
    finally:
        library.close()

    result = main(["bridge", "cleanup-profiles", "--library", str(library_root)])
    profile_events = _events(capsys.readouterr().out)

    assert result == 0
    assert profile_events[0]["event"] == "cleanup_profiles"
    assert any(profile["name"] == "tiny" for profile in profile_events[0]["profiles"])

    result = main(
        [
            "bridge",
            "set-cleanup-profile",
            book_id,
            "--library",
            str(library_root),
            "--cleanup-profile",
            "tiny",
        ]
    )
    events = _events(capsys.readouterr().out)

    assert result == 0
    assert [event["event"] for event in events] == [
        "job_started",
        "job_progress",
        "job_done",
        "book_preview",
    ]
    assert events[-2]["book"]["cleanup_profile"] == "tiny"
    assert events[-1]["book"]["cleanup_profile"] == "tiny"
    assert events[-1]["chunk_count"] >= 1


def test_bridge_chapter_detail_and_update_rechunks(tmp_path: Path, capsys) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Chapter Edit.txt"
    source.write_text("Original text.", encoding="utf-8")

    main(["bridge", "import", str(source), "--library", str(library_root)])
    book_id = str(next(event["book_id"] for event in _events(capsys.readouterr().out) if event.get("event") == "job_done"))

    result = main(["bridge", "chapter-detail", book_id, "--library", str(library_root), "--chapter-index", "0"])
    detail_events = _events(capsys.readouterr().out)

    assert result == 0
    assert detail_events == [
        {
            "event": "chapter_detail",
            "book_id": book_id,
            "chapter_index": 0,
            "title": "Chapter Edit",
            "text": "Original text.",
            "chars": len("Original text."),
        }
    ]

    result = main(
        [
            "bridge",
            "update-chapter",
            book_id,
            "--library",
            str(library_root),
            "--chapter-index",
            "0",
            "--title",
            "Edited",
            "--text",
            "Updated text for rendering.",
        ]
    )
    update_events = _events(capsys.readouterr().out)

    assert result == 0
    assert [event["event"] for event in update_events] == [
        "job_started",
        "job_progress",
        "chapter_updated",
        "book_preview",
        "job_done",
    ]
    assert update_events[2]["title"] == "Edited"
    assert update_events[3]["preview_context"] == "update_chapter"
    assert "Updated text" in update_events[3]["preview"]


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
    assert preview_events[0]["chunks"][0]["chars"] >= len("First sample chunk")
    assert preview_events[0]["chunks"][0]["text_hash"]
    assert "First sample chunk" in preview_events[0]["chunks"][0]["preview"]
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
    assert any(event.get("event") == "outputs" and event.get("outputs") for event in sample_events)
    assert sample_events[-1]["event"] == "job_done"
    assert sample_events[-1]["output"]

    result = main(["bridge", "outputs", "--library", str(library_root), "--book-id", book_id])
    output_events = _events(capsys.readouterr().out)

    assert result == 0
    assert output_events[0]["event"] == "outputs"
    assert output_events[0]["outputs"][0]["path"] == sample_events[-1]["output"]

    result = main(
        [
            "bridge",
            "sample-render",
            book_id,
            "--library",
            str(library_root),
            "--speaker-voice",
            "Ada=Ada Voice",
        ]
    )
    guard_events = _events(capsys.readouterr().out)

    assert result == 1
    assert guard_events[-1]["event"] == "error"
    assert "Confirm speaker voices" in guard_events[-1]["message"]


def test_bridge_startup_snapshot_emits_books_selected_preview_and_outputs(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    library_root = tmp_path / "library"
    first_source = tmp_path / "Ada Author - First Book.txt"
    second_source = tmp_path / "Ada Author - Second Book.txt"
    first_source.write_text("First book text.", encoding="utf-8")
    second_source.write_text("Second book text.", encoding="utf-8")

    main(["bridge", "import", str(first_source), "--library", str(library_root)])
    _events(capsys.readouterr().out)
    main(["bridge", "import", str(second_source), "--library", str(library_root)])
    import_events = _events(capsys.readouterr().out)
    second_id = str(next(event["book_id"] for event in import_events if event.get("event") == "job_done"))

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
    main(["bridge", "sample-render", second_id, "--library", str(library_root)])
    _events(capsys.readouterr().out)

    result = main(["bridge", "startup-snapshot", "--library", str(library_root), "--book-id", second_id])
    events = _events(capsys.readouterr().out)

    assert result == 0
    assert [event["event"] for event in events] == ["books", "book_preview", "outputs"]
    assert len(events[0]["books"]) == 2
    assert events[1]["book"]["id"] == second_id
    assert events[1]["book"]["title"] == "Second Book"
    assert events[2]["outputs"]


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


def test_bridge_tts_test_writes_wav(tmp_path: Path, capsys, monkeypatch) -> None:
    class FakeProvider(TtsProvider):
        id = "fake"

        def health(self) -> bool:
            return True

        def list_voices(self) -> list[TtsVoice]:
            return []

        def synthesize(self, text: str, output_wav: Path, voice: str | None = None, rate: int = 0) -> None:
            output_wav.parent.mkdir(parents=True, exist_ok=True)
            output_wav.write_bytes(f"{text}|{voice}|{rate}".encode("utf-8"))

    monkeypatch.setattr("bookcast.bridge.WindowsSapiProvider", FakeProvider)

    result = main(
        [
            "bridge",
            "tts-test",
            "--library",
            str(tmp_path / "library"),
            "--text",
            "Engine smoke.",
            "--voice",
            "Voice A",
            "--rate",
            "1",
        ]
    )
    events = _events(capsys.readouterr().out)

    assert result == 0
    assert [event["event"] for event in events] == [
        "job_started",
        "job_progress",
        "job_progress",
        "tts_test",
        "job_done",
    ]
    output = Path(str(events[-1]["output"]))
    assert output.exists()
    assert output.read_bytes() == b"Engine smoke.|Voice A|1"


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
                "audio.cpp family is not configured",
            ],
            "hints": [
                "Build audio.cpp, then set audiocpp_cli.exe with Browse in TTS Studio or Settings.",
                "Choose a compatible local TTS model before using the audio.cpp engine.",
                "audio.cpp CLI requires --family for TTS, for example pocket_tts or qwen3_tts.",
            ],
            "tts_families": [],
        }
    ]


def test_bridge_calibre_find_libraries_emits_candidates(tmp_path: Path, capsys) -> None:
    library = tmp_path / "Books" / "Calibre Library"
    library.mkdir(parents=True)
    (library / "metadata.db").write_text("", encoding="utf-8")

    result = main(["bridge", "calibre-find-libraries", "--root", str(tmp_path), "--limit", "4"])
    events = _events(capsys.readouterr().out)

    assert result == 0
    assert events == [
        {
            "event": "calibre_libraries",
            "candidates": [str(library)],
            "count": 1,
        }
    ]


def test_bridge_audio_cpp_find_models_emits_candidates(tmp_path: Path, capsys) -> None:
    model = tmp_path / "models" / "voice.gguf"
    model.parent.mkdir()
    model.write_text("fake", encoding="utf-8")
    (tmp_path / "models" / "ignore.txt").write_text("nope", encoding="utf-8")

    result = main(["bridge", "audio-cpp-find-models", "--root", str(tmp_path), "--limit", "4"])
    events = _events(capsys.readouterr().out)

    assert result == 0
    assert events == [
        {
            "event": "audio_cpp_models",
            "candidates": [str(model)],
            "count": 1,
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
    monkeypatch.setattr("bookcast.bridge.audio_cpp_tts_families", lambda executable: ["pocket_tts", "qwen3_tts"])

    result = main(
        [
            "bridge",
            "audio-cpp-health",
            "--audio-cpp-exe",
            str(exe),
            "--audio-cpp-model",
            str(model),
            "--audio-cpp-family",
            "pocket_tts",
        ]
    )
    events = _events(capsys.readouterr().out)

    assert result == 0
    assert events[0]["event"] == "audio_cpp_health"
    assert events[0]["healthy"] is True
    assert events[0]["issues"] == []
    assert events[0]["hints"] == ["Installed audio.cpp TTS families: pocket_tts, qwen3_tts"]
    assert events[0]["tts_families"] == ["pocket_tts", "qwen3_tts"]


def test_bridge_audio_cpp_health_rejects_unknown_family(tmp_path: Path, capsys, monkeypatch) -> None:
    exe = tmp_path / "audio-cpp.exe"
    model = tmp_path / "model.gguf"
    exe.write_text("fake", encoding="utf-8")
    model.write_text("fake", encoding="utf-8")

    class FakeAudioCppProvider:
        def __init__(self, *args, **kwargs) -> None:
            raise AssertionError("invalid family should stop before provider health")

    monkeypatch.setattr("bookcast.bridge.AudioCppProvider", FakeAudioCppProvider)
    monkeypatch.setattr("bookcast.bridge.audio_cpp_tts_families", lambda executable: ["pocket_tts", "qwen3_tts"])

    result = main(
        [
            "bridge",
            "audio-cpp-health",
            "--audio-cpp-exe",
            str(exe),
            "--audio-cpp-model",
            str(model),
            "--audio-cpp-family",
            "qwen3_asr",
        ]
    )
    events = _events(capsys.readouterr().out)

    assert result == 1
    assert events[0]["healthy"] is False
    assert "audio.cpp family not found: qwen3_asr" in events[0]["issues"]
    assert "Use one of the installed TTS families: pocket_tts, qwen3_tts" in events[0]["hints"]


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
        calls: list[str] = []

        def __init__(self, model: str, base_url: str) -> None:
            self.model = model
            self.base_url = base_url

        def health(self) -> bool:
            return True

        def generate(self, prompt: str, mode: str = "json") -> str:
            assert '"confidence": 0.0' in prompt
            assert '"excerpt": "short source quote or paraphrase"' in prompt
            return '{"characters":[{"name":"Ada","role":"character","evidence":"dialogue","confidence":0.8,"excerpt":"Ada said hello."}]}'

    monkeypatch.setattr("bookcast.bridge.OllamaProvider", FakeOllama)

    result = main(["bridge", "characters", book_id, "--library", str(library_root)])
    events = _events(capsys.readouterr().out)

    assert result == 0
    assert [event["event"] for event in events] == ["job_started", "job_progress", "characters", "job_done"]
    assert events[2]["candidates"][0]["name"] == "Ada"
    assert events[2]["candidates"][0]["confidence"] == 0.8
    assert events[2]["candidates"][0]["excerpt"] == "Ada said hello."


def test_bridge_podcast_script_and_render_emit_jsonl(tmp_path: Path, capsys, monkeypatch) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Podcast Book.txt"
    source.write_text("A short article about careful engineering.", encoding="utf-8")

    main(["bridge", "import", str(source), "--library", str(library_root)])
    book_id = str(next(event["book_id"] for event in _events(capsys.readouterr().out) if event.get("event") == "job_done"))

    class FakeOllama:
        calls: list[str] = []

        def __init__(self, model: str, base_url: str) -> None:
            self.model = model
            self.base_url = base_url

        def health(self) -> bool:
            return True

        def generate(self, prompt: str, mode: str = "json") -> str:
            self.calls.append(prompt)
            if "continuing a live podcast" in prompt:
                speaker = "host" if len(self.calls) <= 3 else "explainer"
                return f'{{"speaker":"{speaker}","text":"Live turn {len(self.calls)}.","follow_up":"continue"}}'
            assert "Focus: practical tradeoffs" in prompt
            assert "Style: concise and calm" in prompt
            return (
                '{"title":"Engineering Cast","summary":"Short.",'
                '"speakers":["host","explainer"],'
                '"citations":["Careful engineering reduces rework."],'
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
    monkeypatch.setattr("bookcast.library.probe_duration", lambda path, ffprobe="ffprobe": 1.0)

    result = main(
        [
            "bridge",
            "podcast-script",
            book_id,
            "--library",
            str(library_root),
            "--focus",
            "practical tradeoffs",
            "--style",
            "concise and calm",
        ]
    )
    script_events = _events(capsys.readouterr().out)

    assert result == 0
    assert script_events[2]["event"] == "podcast_script"
    assert script_events[2]["script"]["title"] == "Engineering Cast"
    assert script_events[2]["script"]["citations"] == ["Careful engineering reduces rework."]
    assert script_events[-1]["path"].endswith("Engineering Cast.json")
    script_path = script_events[-1]["path"]
    FakeOllama.calls.clear()

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
            "--confirm-voices",
            "--script-path",
            script_path,
        ]
    )
    render_events = _events(capsys.readouterr().out)

    assert result == 0
    assert FakeOllama.calls == []
    rendered_script_events = [event for event in render_events if event.get("event") == "podcast_script"]
    assert rendered_script_events
    assert any(
        event.get("event") == "job_progress"
        and event.get("job") == "podcast_render"
        and event.get("phase") == "tts"
        for event in render_events
    )
    assert any(event.get("event") == "outputs" and event.get("outputs") for event in render_events)
    assert render_events[-1]["event"] == "job_done"
    assert render_events[-1]["output"].endswith(".opus")

    monkeypatch.setattr("bookcast.bridge.assemble_audio", fake_assemble)
    result = main(
        [
            "bridge",
            "podcast-interactive",
            book_id,
            "--library",
            str(library_root),
            "--turns",
            "2",
            "--seed-prompt",
            "start with a practical question",
            "--voice",
            "host=Narrator",
            "--confirm-voices",
        ]
    )
    interactive_events = _events(capsys.readouterr().out)

    assert result == 0
    assert [event["event"] for event in interactive_events].count("interactive_turn") == 2
    assert any(event.get("event") == "interactive_podcast" for event in interactive_events)
    assert interactive_events[-1]["event"] == "job_done"
    assert interactive_events[-1]["output"].endswith("_interactive.opus")


def test_bridge_podcast_render_requires_confirmed_voice_map(tmp_path: Path, capsys, monkeypatch) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Podcast Confirm.txt"
    source.write_text("A short article about careful engineering.", encoding="utf-8")

    main(["bridge", "import", str(source), "--library", str(library_root)])
    book_id = str(next(event["book_id"] for event in _events(capsys.readouterr().out) if event.get("event") == "job_done"))

    class FakeOllama:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def health(self) -> bool:
            return True

        def generate(self, prompt: str, mode: str = "json") -> str:
            return (
                '{"title":"Engineering Cast","summary":"Short.",'
                '"speakers":["host"],'
                '"turns":[{"speaker":"host","text":"Welcome."}]}'
            )

    monkeypatch.setattr("bookcast.bridge.OllamaProvider", FakeOllama)

    result = main(["bridge", "podcast-render", book_id, "--library", str(library_root), "--voice", "host=Narrator"])
    events = _events(capsys.readouterr().out)

    assert result == 1
    assert events[-1]["event"] == "error"
    assert "Confirm speaker voices" in events[-1]["message"]

    result = main(["bridge", "podcast-render", book_id, "--library", str(library_root), "--confirm-voices"])
    events = _events(capsys.readouterr().out)

    assert result == 1
    assert events[-1]["event"] == "error"
    assert "Speaker voice mapping is required" in events[-1]["message"]
