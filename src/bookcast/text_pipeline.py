from __future__ import annotations

import hashlib
import re

from .models import Chapter, Chunk


def clean_text(text: str, profile: dict | None = None) -> str:
    profile = profile or {}
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if profile.get("remove_soft_hyphens", True):
        text = text.replace("\u00ad", "")
    if profile.get("join_hyphenated_lines", True):
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    if profile.get("collapse_spaces", True):
        text = re.sub(r"[ \t]+", " ", text)
    if profile.get("collapse_blank_lines", True):
        max_blank_lines = int(profile.get("max_blank_lines", 2))
        text = re.sub(rf"\n{{{max_blank_lines + 1},}}", "\n" * max_blank_lines, text)
    if profile.get("strip_trailing_whitespace", True):
        text = "\n".join(line.rstrip() for line in text.splitlines())
    if profile.get("trim", True):
        text = text.strip()
    return text


def chunk_chapters(chapters: list[Chapter], max_chars: int = 1800, profile: dict | None = None) -> list[Chunk]:
    profile = profile or {}
    max_chars = int(profile.get("max_chars", max_chars))
    chunks: list[Chunk] = []
    for chapter in chapters:
        paragraphs = [p.strip() for p in clean_text(chapter.text, profile).split("\n\n") if p.strip()]
        pending = ""
        chunk_index = 0
        for paragraph in paragraphs:
            parts = _split_long_paragraph(paragraph, max_chars)
            for part in parts:
                if not pending:
                    pending = part
                elif len(pending) + 2 + len(part) <= max_chars:
                    pending = f"{pending}\n\n{part}"
                else:
                    chunks.append(_chunk(chapter.index, chunk_index, pending))
                    chunk_index += 1
                    pending = part
        if pending:
            chunks.append(_chunk(chapter.index, chunk_index, pending))
    return chunks


def _split_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    if len(paragraph) <= max_chars:
        return [paragraph]

    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    parts: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > max_chars:
            if current:
                parts.append(current)
                current = ""
            parts.extend(sentence[i : i + max_chars] for i in range(0, len(sentence), max_chars))
        elif not current:
            current = sentence
        elif len(current) + 1 + len(sentence) <= max_chars:
            current = f"{current} {sentence}"
        else:
            parts.append(current)
            current = sentence
    if current:
        parts.append(current)
    return parts


def _chunk(chapter_index: int, chunk_index: int, text: str) -> Chunk:
    text = clean_text(text)
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return Chunk(chapter_index=chapter_index, chunk_index=chunk_index, text=text, text_hash=text_hash)
