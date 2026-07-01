from __future__ import annotations

from pathlib import Path

from bookcast.cli import main
from bookcast.llm import LlmProvider
from bookcast.podcast import PodcastScript, PodcastTurn
from bookcast.library import BookLibrary
from bookcast.tts import TtsProvider, TtsVoice


def test_library_import_stores_book_chapters_chunks_and_source(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Plain Book.txt"
    source.write_text("Chapter text.\n\nMore text.", encoding="utf-8")

    library = BookLibrary(library_root)
    try:
        book_id = library.import_source(source)
        books = library.list_books()
    finally:
        library.close()

    assert book_id
    assert books[0]["title"] == "Plain Book"
    assert books[0]["author"] == "Ada Author"
    assert books[0]["chapter_count"] == 1
    assert books[0]["chunk_count"] == 1
    assert (library_root / "books" / book_id / "source" / source.name).exists()


def test_library_import_source_reuses_same_file_hash(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    first = tmp_path / "Ada Author - Duplicate One.txt"
    second = tmp_path / "Ada Author - Duplicate Two.txt"
    first.write_text("Same book text.", encoding="utf-8")
    second.write_text("Same book text.", encoding="utf-8")

    library = BookLibrary(library_root)
    try:
        first_id = library.import_source(first)
        second_id = library.import_source(second)
        books = library.list_books()
    finally:
        library.close()

    assert second_id == first_id
    assert len(books) == 1


def test_cli_import_smoke(tmp_path: Path, capsys) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - CLI Book.md"
    source.write_text("# Heading\n\nBody.", encoding="utf-8")

    result = main(["import", str(source), "--library", str(library_root)])

    assert result == 0
    assert "Imported Ada Author - CLI Book" in capsys.readouterr().out


def test_render_book_marks_chunks_and_outputs(tmp_path: Path, monkeypatch) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Audio Book.txt"
    source.write_text("First chunk.\n\nSecond chunk.", encoding="utf-8")

    def fake_assemble(chunk_wavs, output_path, output_format, ffmpeg="ffmpeg"):
        assert output_format == "opus"
        assert chunk_wavs
        output_path.write_bytes(b"audio")
        return output_path

    monkeypatch.setattr("bookcast.library.assemble_audio", fake_assemble)
    progress: list[dict[str, object]] = []

    library = BookLibrary(library_root)
    try:
        book_id = library.import_source(source)
        output = library.render_book(
            book_id,
            provider=_FakeTtsProvider(),
            output_format="opus",
            progress_callback=progress.append,
        )
        chunks = library.get_chunks(book_id)
    finally:
        library.close()

    assert output.exists()
    assert all(chunk["status"] == "Rendered" for chunk in chunks)
    assert all(Path(chunk["audio_path"]).exists() for chunk in chunks)
    assert progress[0] == {"phase": "tts", "progress": 10, "chunk": 0, "total": len(chunks)}
    assert progress[-1] == {"phase": "assemble", "progress": 92, "chunk": len(chunks), "total": len(chunks)}
    assert any(event.get("phase") == "tts" and event.get("chunk") == len(chunks) for event in progress)


def test_render_book_cache_key_includes_voice(tmp_path: Path, monkeypatch) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Voice Cache.txt"
    source.write_text("One reusable chunk.", encoding="utf-8")

    def fake_assemble(chunk_wavs, output_path, output_format, ffmpeg="ffmpeg", chapters=None):
        output_path.write_bytes(b"audio")
        return output_path

    monkeypatch.setattr("bookcast.library.assemble_audio", fake_assemble)
    provider = _RecordingTtsProvider()

    library = BookLibrary(library_root)
    try:
        book_id = library.import_source(source)
        library.render_book(book_id, provider=provider, voice="Voice A", output_format="opus")
        first_path = Path(str(library.get_chunks(book_id)[0]["audio_path"]))
        library.render_book(book_id, provider=provider, voice="Voice B", output_format="opus")
        second_path = Path(str(library.get_chunks(book_id)[0]["audio_path"]))
    finally:
        library.close()

    assert len(provider.calls) == 2
    assert first_path != second_path
    assert first_path.exists()
    assert second_path.exists()


def test_render_book_long_run_progress_and_resume_cache(tmp_path: Path, monkeypatch) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Long Queue.txt"
    source.write_text(
        "\n\n".join(
            f"Section {index}. This paragraph exists to force several render chunks for queue stress."
            for index in range(60)
        ),
        encoding="utf-8",
    )

    assemble_calls: list[list[Path]] = []

    def fake_assemble(chunk_wavs, output_path, output_format, ffmpeg="ffmpeg", chapters=None):
        assemble_calls.append(list(chunk_wavs))
        output_path.write_bytes(b"audio")
        return output_path

    monkeypatch.setattr("bookcast.library.assemble_audio", fake_assemble)
    provider = _RecordingTtsProvider()
    first_progress: list[dict[str, object]] = []
    second_progress: list[dict[str, object]] = []

    library = BookLibrary(library_root)
    try:
        library.upsert_cleanup_profile(
            "queue-stress",
            {
                "max_chars": 80,
                "join_hyphenated_lines": True,
                "collapse_blank_lines": True,
                "collapse_spaces": True,
                "remove_soft_hyphens": True,
                "strip_trailing_whitespace": True,
                "trim": True,
                "max_blank_lines": 2,
            },
        )
        book_id = library.import_source(source, cleanup_profile="queue-stress")
        chunks = library.get_chunks(book_id)
        assert len(chunks) >= 50

        first_output = library.render_book(
            book_id,
            provider=provider,
            voice="Narrator",
            output_format="opus",
            progress_callback=first_progress.append,
        )
        calls_after_first = len(provider.calls)
        second_output = library.render_book(
            book_id,
            provider=provider,
            voice="Narrator",
            output_format="opus",
            progress_callback=second_progress.append,
        )
    finally:
        library.close()

    assert first_output.exists()
    assert second_output.exists()
    assert calls_after_first == len(chunks)
    assert len(provider.calls) == calls_after_first
    assert len(assemble_calls) == 2
    assert len(assemble_calls[0]) == len(chunks)
    assert first_progress[-1] == {"phase": "assemble", "progress": 92, "chunk": len(chunks), "total": len(chunks)}
    assert second_progress[-1] == {"phase": "assemble", "progress": 92, "chunk": len(chunks), "total": len(chunks)}
    assert any(event.get("phase") == "tts" and event.get("chunk") == len(chunks) for event in first_progress)
    assert all(event.get("cached") is True for event in second_progress if event.get("phase") == "tts" and event.get("chunk"))


def test_render_book_uses_confirmed_speaker_voice_map_for_prefixed_chunks(tmp_path: Path, monkeypatch) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Cast Book.txt"
    source.write_text(
        "Ada: First line.\n\nBob: Second line.\n\nNarrator: Third line.",
        encoding="utf-8",
    )

    def fake_assemble(chunk_wavs, output_path, output_format, ffmpeg="ffmpeg", chapters=None):
        output_path.write_bytes(b"audio")
        return output_path

    monkeypatch.setattr("bookcast.library.assemble_audio", fake_assemble)
    provider = _RecordingTtsProvider()

    library = BookLibrary(library_root)
    try:
        library.upsert_cleanup_profile(
            "speaker-lines",
            {
                "max_chars": 30,
                "join_hyphenated_lines": True,
                "collapse_blank_lines": True,
                "collapse_spaces": True,
                "remove_soft_hyphens": True,
                "strip_trailing_whitespace": True,
                "trim": True,
                "max_blank_lines": 2,
            },
        )
        book_id = library.import_source(source, cleanup_profile="speaker-lines")
        output = library.render_book(
            book_id,
            provider=provider,
            voice="Narrator Voice",
            voice_map={"Ada": "Ada Voice", "Bob": "Bob Voice"},
            output_format="opus",
        )
        chunks = library.get_chunks(book_id)
    finally:
        library.close()

    assert output.exists()
    assert [voice for _, voice in provider.calls[:3]] == ["Ada Voice", "Bob Voice", "Narrator Voice"]
    assert len({Path(chunk["audio_path"]).name for chunk in chunks}) == len(chunks)


def test_render_book_guesses_dialogue_voice_from_said_tags(tmp_path: Path, monkeypatch) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Dialogue Book.txt"
    source.write_text(
        '"Hello there," said Ada.\n\n'
        '"Hallo", sagte Bob.\n\n'
        '"Nicht jetzt", erwiderte Ada leise.\n\n'
        'Bob fragte: "Warum nicht?"\n\n'
        '"Stop!" Alice cried.\n\n'
        "Narrator continues.",
        encoding="utf-8",
    )

    def fake_assemble(chunk_wavs, output_path, output_format, ffmpeg="ffmpeg", chapters=None):
        output_path.write_bytes(b"audio")
        return output_path

    monkeypatch.setattr("bookcast.library.assemble_audio", fake_assemble)
    provider = _RecordingTtsProvider()

    library = BookLibrary(library_root)
    try:
        library.upsert_cleanup_profile(
            "dialogue-lines",
            {
                "max_chars": 35,
                "join_hyphenated_lines": True,
                "collapse_blank_lines": True,
                "collapse_spaces": True,
                "remove_soft_hyphens": True,
                "strip_trailing_whitespace": True,
                "trim": True,
                "max_blank_lines": 2,
            },
        )
        book_id = library.import_source(source, cleanup_profile="dialogue-lines")
        output = library.render_book(
            book_id,
            provider=provider,
            voice="Narrator Voice",
            voice_map={"Ada": "Ada Voice", "Bob": "Bob Voice", "Alice": "Alice Voice"},
            output_format="opus",
        )
    finally:
        library.close()

    assert output.exists()
    assert [voice for _, voice in provider.calls] == [
        "Ada Voice",
        "Bob Voice",
        "Ada Voice",
        "Bob Voice",
        "Alice Voice",
        "Narrator Voice",
    ]


def test_render_book_m4b_passes_chapters(tmp_path: Path, monkeypatch) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Audio Book.txt"
    source.write_text("First chunk.\n\nSecond chunk.", encoding="utf-8")

    chapter_calls: list[tuple[list[tuple[int, Path]], dict[int, str]]] = []

    def fake_chapter_timeline(rendered_chunks, chapter_titles, ffprobe="ffprobe"):
        assert ffprobe == "custom-ffprobe.exe"
        chapter_calls.append((rendered_chunks, chapter_titles))
        return [("Chapter 1", 0.0)]

    def fake_assemble(chunk_wavs, output_path, output_format, ffmpeg="ffmpeg", chapters=None):
        assert output_format == "m4b"
        assert chapters == [("Chapter 1", 0.0)]
        output_path.write_bytes(b"audio")
        return output_path

    monkeypatch.setattr("bookcast.library.chapter_timeline", fake_chapter_timeline)
    monkeypatch.setattr("bookcast.library.assemble_audio", fake_assemble)

    library = BookLibrary(library_root)
    try:
        book_id = library.import_source(source)
        output = library.render_book(
            book_id,
            provider=_FakeTtsProvider(),
            output_format="m4b",
            ffprobe="custom-ffprobe.exe",
        )
    finally:
        library.close()

    assert output.exists()
    assert chapter_calls
    assert chapter_calls[0][1] == {0: "Audio Book"}


def test_cleanup_profile_applies_to_import_and_rechunk(tmp_path: Path, monkeypatch) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Cleanup Book.txt"
    source.write_text("One long paragraph that should split into several smaller chunks for the tight profile.", encoding="utf-8")

    library = BookLibrary(library_root)
    try:
        library.upsert_cleanup_profile(
            "tight",
            {
                "max_chars": 20,
                "join_hyphenated_lines": True,
                "collapse_blank_lines": True,
                "collapse_spaces": True,
                "remove_soft_hyphens": True,
                "strip_trailing_whitespace": True,
                "trim": True,
                "max_blank_lines": 2,
            },
        )
        book_id = library.import_source(source, cleanup_profile="tight")
        books = library.list_books()
        chunks_before = library.get_chunks(book_id)
        library.update_chapter(book_id, 0, "Updated title", "This chapter got much longer and should still chunk cleanly.")
        chunks_after = library.get_chunks(book_id)
        updated_book = library.get_book(book_id)
    finally:
        library.close()

    assert books[0]["cleanup_profile"] == "tight"
    assert len(chunks_before) > 1
    assert len(chunks_after) > 1
    assert chunks_after[0]["text"].startswith("This chapter")
    assert updated_book["status"] == "Imported"


def test_render_podcast_script_uses_voice_map(tmp_path: Path, monkeypatch) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Podcast Book.txt"
    source.write_text("Podcast source.", encoding="utf-8")

    def fake_probe_duration(path: Path, ffprobe: str = "ffprobe") -> float:
        return 1.25

    def fake_assemble(chunk_wavs, output_path, output_format, ffmpeg="ffmpeg", chapters=None):
        assert output_format == "opus"
        output_path.write_bytes(b"audio")
        return output_path

    monkeypatch.setattr("bookcast.library.probe_duration", fake_probe_duration)
    monkeypatch.setattr("bookcast.library.assemble_audio", fake_assemble)

    library = BookLibrary(library_root)
    provider = _RecordingTtsProvider()
    try:
        book_id = library.import_source(source)
        script = PodcastScript(
            title="Episode",
            mode="educational",
            summary="Summary",
            speakers=["host", "explainer"],
            turns=[
                PodcastTurn(speaker="host", text="Welcome."),
                PodcastTurn(speaker="explainer", text="Here is the idea."),
            ],
        )
        output = library.render_podcast_script(
            book_id,
            script,
            provider=provider,
            voice_map={"host": "Narrator", "explainer": "Guest"},
            output_format="opus",
        )
        speakers = library.list_speakers(book_id)
    finally:
        library.close()

    assert output.exists()
    assert provider.calls == [("Welcome.", "Narrator"), ("Here is the idea.", "Guest")]
    assert [speaker["name"] for speaker in speakers] == ["explainer", "host"]
    assert {speaker["voice_name"] for speaker in speakers} == {"Guest", "Narrator"}


def test_cli_interactive_podcast_session(tmp_path: Path, monkeypatch, capsys) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Interactive Book.txt"
    source.write_text("Interactive source text.", encoding="utf-8")
    _InteractiveFakeProvider.calls = []
    played: list[Path] = []

    monkeypatch.setattr("bookcast.cli.OllamaProvider", lambda *args, **kwargs: _InteractiveFakeProvider())
    monkeypatch.setattr("bookcast.cli.WindowsSapiProvider", _InteractiveFakeTtsProvider)
    monkeypatch.setattr("bookcast.cli.play_wav", lambda path: played.append(path))
    monkeypatch.setattr("builtins.input", lambda prompt="": "follow up")

    def fake_assemble(chunk_wavs, output_path, output_format, ffmpeg="ffmpeg", chapters=None):
        output_path.write_bytes(b"audio")
        return output_path

    monkeypatch.setattr("bookcast.cli.assemble_audio", fake_assemble)

    main(["import", str(source), "--library", str(library_root)])
    library = BookLibrary(library_root)
    try:
        book_id = library.list_books()[0]["id"]
    finally:
        library.close()

    result = main(
        [
            "podcast",
            "interactive",
            str(book_id),
            "--library",
            str(library_root),
            "--turns",
            "2",
            "--model",
            "fake",
            "--voice",
            "host=Narrator",
            "--confirm-voices",
        ]
    )

    assert result == 0
    out = capsys.readouterr().out
    assert "Rendered interactive podcast" in out
    assert _InteractiveFakeProvider.calls[1][0].find("follow up") != -1
    assert len(played) == 2
    session_dir = library_root / "books" / book_id / "podcasts" / "interactive" / "Interactive Book"
    assert (session_dir / "session.json").exists()


def test_update_chapter_clears_render_artifacts(tmp_path: Path, monkeypatch) -> None:
    library_root = tmp_path / "library"
    source = tmp_path / "Ada Author - Render Book.txt"
    source.write_text("First chunk.\n\nSecond chunk.", encoding="utf-8")

    def fake_assemble(chunk_wavs, output_path, output_format, ffmpeg="ffmpeg", chapters=None):
        output_path.write_bytes(b"audio")
        return output_path

    monkeypatch.setattr("bookcast.library.assemble_audio", fake_assemble)

    library = BookLibrary(library_root)
    try:
        book_id = library.import_source(source)
        output = library.render_book(book_id, provider=_FakeTtsProvider(), output_format="opus")
        assert output.exists()
        library.update_chapter(book_id, 0, "Changed", "A much longer replacement chapter that should invalidate the render output.")
        updated_chunks = library.get_chunks(book_id)
    finally:
        library.close()

    assert not output.exists()
    assert updated_chunks[0]["text"].startswith("A much longer")
    assert len(updated_chunks) >= 1


class _FakeTtsProvider(TtsProvider):
    id = "fake"

    def health(self) -> bool:
        return True

    def list_voices(self):
        return []

    def synthesize(self, text: str, output_wav: Path, voice: str | None = None, rate: int = 0) -> None:
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        output_wav.write_bytes(b"RIFFfakeWAVE")


class _RecordingTtsProvider(TtsProvider):
    id = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    def health(self) -> bool:
        return True

    def list_voices(self) -> list[TtsVoice]:
        return [TtsVoice(id="Narrator", label="Narrator"), TtsVoice(id="Guest", label="Guest")]

    def synthesize(self, text: str, output_wav: Path, voice: str | None = None, rate: int = 0) -> None:
        self.calls.append((text, voice))
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        output_wav.write_bytes(b"RIFFfakeWAVE")


class _InteractiveFakeProvider(LlmProvider):
    calls: list[tuple[str, str]] = []

    def __init__(self) -> None:
        self.responses = [
            '{"speaker":"host","text":"Opening segment.","follow_up":"What should we emphasize next?"}',
            '{"speaker":"host","text":"Response to the interruption.","follow_up":""}',
        ]

    def health(self) -> bool:
        return True

    def generate(self, prompt: str, mode: str = "json") -> str:
        assert mode == "json"
        self.__class__.calls.append((prompt, mode))
        return self.responses.pop(0)


class _InteractiveFakeTtsProvider(TtsProvider):
    id = "fake-tts"

    def health(self) -> bool:
        return True

    def list_voices(self) -> list[TtsVoice]:
        return [TtsVoice(id="Narrator", label="Narrator")]

    def synthesize(self, text: str, output_wav: Path, voice: str | None = None, rate: int = 0) -> None:
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        output_wav.write_bytes(b"RIFFfakeWAVE")
