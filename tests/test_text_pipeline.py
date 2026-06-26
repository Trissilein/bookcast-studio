from bookcast.models import Chapter
from bookcast.text_pipeline import chunk_chapters, clean_text


def test_clean_text_repairs_hyphenated_line_breaks() -> None:
    assert clean_text("Ein Bei-\nspiel\n\n\nmit   Abstand") == "Ein Beispiel\n\nmit Abstand"


def test_chunk_hash_is_stable() -> None:
    chapters = [Chapter(index=0, title="One", text="First paragraph.\n\nSecond paragraph.")]
    first = chunk_chapters(chapters, max_chars=500)
    second = chunk_chapters(chapters, max_chars=500)

    assert len(first) == 1
    assert first[0].text_hash == second[0].text_hash


def test_chunking_respects_max_chars() -> None:
    chapters = [Chapter(index=0, title="One", text="A sentence. " * 100)]
    chunks = chunk_chapters(chapters, max_chars=120)

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 120 for chunk in chunks)

