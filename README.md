# BookCast Studio

Local-first audiobook and podcast generation studio.

Current slice:

- Desktop shell with a library table.
- SQLite library database.
- CLI import smoke command.
- TXT, MD, EPUB, DOCX, and PDF import.
- Read-only Calibre library import via `calibredb`.
- Windows SAPI TTS chunk rendering.
- ffmpeg assembly to Opus, MP3, or WAV.
- Ollama-assisted character suggestions and static podcast scripts.
- Text cleanup and stable chunk hashes.

Planned later:

- PDF and DOCX extraction.
- Local TTS providers.
- Audiobook rendering to Opus, MP3, and M4B.
- Character voice assignment.
- Paper/article to scripted podcast generation with Ollama.

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
```

Podcast modes: `educational`, `controversial`, `interview`.
