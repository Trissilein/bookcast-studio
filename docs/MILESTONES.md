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
- Add editable cleanup profiles.
- Add chapter and chunk review UI.

## M3 Audiobook Render

- Add TTS provider interface implementation. Windows SAPI baseline done.
- Render resumable chunks. Done.
- Assemble Opus, MP3, WAV with ffmpeg. Done.
- Add M4B chaptered export.

## M4 Voices + Characters

- Add narrator and speaker tables in UI.
- Add Ollama-assisted character extraction. CLI foundation done.
- Require manual confirmation before rendering character voices.

## M5 Static Podcast Generator

- Generate educational, controversial, and interview scripts from sources. CLI foundation done.
- Render multi-speaker episodes.

## M6 Interactive Podcast

- Keep local LLM resident.
- Support user interruptions and generated follow-up segments.
- Stream partial render/playback.
