from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_VERSION = 1


class Database:
    def __init__(self, library_root: Path) -> None:
        self.library_root = Path(library_root)
        self.library_root.mkdir(parents=True, exist_ok=True)
        self.path = self.library_root / "bookcast.sqlite3"
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.migrate()

    def close(self) -> None:
        self.conn.close()

    def migrate(self) -> None:
        version = self.conn.execute("PRAGMA user_version").fetchone()[0]
        if version < 1:
            self._migrate_v1()
        self.conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        self.conn.commit()

    def _migrate_v1(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS books (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                language TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY,
                book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
                original_path TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                source_sha256 TEXT NOT NULL,
                format TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chapters (
                id TEXT PRIMARY KEY,
                book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
                chapter_index INTEGER NOT NULL,
                title TEXT NOT NULL,
                text TEXT NOT NULL,
                UNIQUE(book_id, chapter_index)
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
                chapter_index INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                text_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                UNIQUE(book_id, chapter_index, chunk_index)
            );

            CREATE TABLE IF NOT EXISTS voices (
                id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                name TEXT NOT NULL,
                locale TEXT,
                config_json TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS speakers (
                id TEXT PRIMARY KEY,
                book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                voice_id TEXT REFERENCES voices(id)
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                book_id TEXT REFERENCES books(id) ON DELETE CASCADE,
                kind TEXT NOT NULL,
                status TEXT NOT NULL,
                detail_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS outputs (
                id TEXT PRIMARY KEY,
                book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
                format TEXT NOT NULL,
                path TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS podcast_projects (
                id TEXT PRIMARY KEY,
                source_book_id TEXT REFERENCES books(id) ON DELETE SET NULL,
                title TEXT NOT NULL,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )

