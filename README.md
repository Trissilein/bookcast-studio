# BookCast Studio

Local-first audiobook and podcast generation studio.

Current slice:

- Desktop shell with a library table.
- SQLite library database.
- CLI import smoke command.
- TXT, MD, EPUB, DOCX, and PDF import.
- Read-only Calibre library import via `calibredb`.
- Windows SAPI TTS chunk rendering.
- ffmpeg assembly to Opus, MP3, WAV, or M4B.
- Ollama-assisted character suggestions, static podcast scripts, and podcast render.
- Interactive podcast sessions with resident Ollama and live follow-ups.
- Text cleanup and stable chunk hashes.
- Editable cleanup profiles, chapter review, and speaker mapping in the UI.

Planned later:

- Additional TTS providers beyond Windows SAPI.
- Better UI polish and batch job management.
- Optional cloud sync / collaboration layer.

## Setup

```powershell
cd D:\GIT\bookcast-studio
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install -e .[dev,ui]
```

## Run UI

```powershell
.\.venv\Scripts\bookcast-ui --library .\library
```

## Import From CLI

```powershell
.\.venv\Scripts\bookcast import .\samples\book.epub --library .\library
.\.venv\Scripts\bookcast list --library .\library
.\.venv\Scripts\bookcast render <book-id> --library .\library --format opus
.\.venv\Scripts\bookcast render <book-id> --library .\library --format m4b
```

## Import From Calibre

BookCast reads Calibre through the official `calibredb` CLI and copies exported
files into its own library. It does not write back to Calibre.

```powershell
.\.venv\Scripts\bookcast calibre scan "C:\Users\you\Calibre Library"
.\.venv\Scripts\bookcast calibre import "C:\Users\you\Calibre Library" --library .\library --id 42
```

Only `EPUB`, `TXT`, and `MD` are imported from Calibre in this slice. Books
without those formats are skipped until conversion support lands.

## Ollama Tools

These commands require a running Ollama server.

```powershell
.\.venv\Scripts\bookcast characters suggest <book-id> --library .\library --model qwen3:8b
.\.venv\Scripts\bookcast podcast script <book-id> --library .\library --mode educational --model qwen3:8b
.\.venv\Scripts\bookcast podcast render <book-id> --library .\library --mode controversial --format opus --voice host=Narrator --voice explainer=Guest
.\.venv\Scripts\bookcast podcast interactive <book-id> --library .\library --mode interview --turns 4 --no-playback
```

Podcast modes: `educational`, `controversial`, `interview`.
