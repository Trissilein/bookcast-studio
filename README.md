# BookCast Studio

Local-first audiobook and podcast generation studio.

Current slice:

- Desktop shell with a library table.
- SQLite library database.
- CLI import smoke command.
- TXT, MD, and EPUB import.
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
```

PDF and DOCX are intentionally blocked until the M2 extraction layer is built.

