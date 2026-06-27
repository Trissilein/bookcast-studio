# BookCast Studio Milestones

## M0 Repo Bootstrap

- Python package, CLI entrypoint, PySide UI entrypoint.
- SQLite migration harness.
- Tests and README.

## M1 Library + Import

- Import TXT, MD, EPUB.
- Store source copies in library root.
- Persist books, sources, chapters, chunks.
- Show imported books in desktop library table.

## M1.5 Calibre Import

- Read Calibre libraries through `calibredb`.
- Scan books with `EPUB`, `TXT`, or `MD` formats.
- Import selected books into BookCast without writing back to Calibre.
- Store Calibre ID/UUID for duplicate-safe re-import.

## M2 Text Pipeline

- Add PDF and DOCX extraction. Done.
- Add editable cleanup profiles. Done.
- Add chapter and chunk review UI. Done.

## M3 Audiobook Render

- Add TTS provider interface implementation. Windows SAPI baseline done.
- Render resumable chunks. Done.
- Assemble Opus, MP3, WAV, and M4B with ffmpeg. Done.
- Add chaptered export. Done.

## M4 Voices + Characters

- Add narrator and speaker tables in UI. Done.
- Add Ollama-assisted character extraction. CLI and Rust workbench bridge done.
- Sync speaker to voice mappings for podcast render. Done.
- Require manual confirmation before rendering character voices.

## M5 Static Podcast Generator

- Generate educational, controversial, and interview scripts from sources. CLI and Rust workbench bridge done.
- Render multi-speaker episodes. Done.
- Expose static podcast script/render actions in Rust workbench. Done.

## M6 Interactive Podcast

- Keep local LLM resident. Done.
- Support user interruptions and generated follow-up segments. Done.
- Stream partial render/playback. Done.

## M7 Rust Workbench Migration

- Add Rust workspace and Slint workbench MVP. Done.
- Keep Python backend as JSONL bridge during migration. Done.
- Add queue log, cancel hook, diagnostics, import controls, TTS engine selection. Done.
- Add configurable `audio.cpp` external-process TTS provider. Done.
- Add `audio.cpp` upstream check with `Update Available` flag. Done.
- Replace queue log with structured job rows. Done.
- Add Calibre scan preview and ID-based import in Rust workbench. Done.
- Add source/chapter preview panes and render sample before full queue. Done.
- Add voice discovery/selection and output-open actions. Done.
- Persist Rust UI settings and add structured views instead of one-page workbench. Done.
- Add Rust views for character suggestions and static podcast generation. Done.
- Add a real build/package command and a final end-to-end acceptance script. Done.
- Next: validate real `audio.cpp` CLI arguments against an installed binary/model and polish visual design.
