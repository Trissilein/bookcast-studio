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

## M2 Text Pipeline

- Add PDF and DOCX extraction.
- Add editable cleanup profiles.
- Add chapter and chunk review UI.

## M3 Audiobook Render

- Add TTS provider interface implementation.
- Render resumable chunks.
- Assemble Opus, MP3, M4B with ffmpeg.

## M4 Voices + Characters

- Add narrator and speaker tables in UI.
- Add Ollama-assisted character extraction.
- Require manual confirmation before rendering character voices.

## M5 Static Podcast Generator

- Generate educational, controversial, and interview scripts from sources.
- Render multi-speaker episodes.

## M6 Interactive Podcast

- Keep local LLM resident.
- Support user interruptions and generated follow-up segments.
- Stream partial render/playback.

