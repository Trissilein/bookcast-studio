from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Metadata:
    title: str
    author: str
    language: str | None = None


@dataclass(frozen=True)
class Chapter:
    index: int
    title: str
    text: str


@dataclass(frozen=True)
class Document:
    source_path: Path
    metadata: Metadata
    chapters: list[Chapter]
    raw_text: str


@dataclass(frozen=True)
class Chunk:
    chapter_index: int
    chunk_index: int
    text: str
    text_hash: str

