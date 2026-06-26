from __future__ import annotations

from pathlib import Path

from bookcast.cli import main
from bookcast.library import BookLibrary
from bookcast.tts import TtsProvider


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

    library = BookLibrary(library_root)
    try:
        book_id = library.import_source(source)
        output = library.render_book(book_id, provider=_FakeTtsProvider(), output_format="opus")
        chunks = library.get_chunks(book_id)
    finally:
        library.close()

    assert output.exists()
    assert all(chunk["status"] == "Rendered" for chunk in chunks)
    assert all(Path(chunk["audio_path"]).exists() for chunk in chunks)


class _FakeTtsProvider(TtsProvider):
    id = "fake"

    def health(self) -> bool:
        return True

    def list_voices(self):
        return []

    def synthesize(self, text: str, output_wav: Path, voice: str | None = None, rate: int = 0) -> None:
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        output_wav.write_bytes(b"RIFFfakeWAVE")
