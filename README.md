# BookCast Studio

Local-first audiobook and podcast generation studio.

Current slice:

- Rust-first Slint workbench MVP with queue log, diagnostics, engine selection, cancel, and `audio.cpp` update check.
- JSONL Python bridge for the Rust client.
- Desktop shell with a library table.
- SQLite library database.
- CLI import smoke command.
- TXT, MD, EPUB, DOCX, and PDF import.
- Read-only Calibre library import via `calibredb`.
- Windows SAPI and configurable `audio.cpp` TTS chunk rendering.
- ffmpeg assembly to Opus, MP3, WAV, or M4B.
- Ollama-assisted character suggestions, static podcast scripts, and podcast render.
- Interactive podcast sessions with resident Ollama and live follow-ups.
- Text cleanup and stable chunk hashes.
- Editable cleanup profiles and chapter review in the Python UI.
- Character and podcast workbench views in the Rust UI.

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

Rust workbench:

```powershell
cargo run -p bookcast-rust
```

The Rust workbench has separate views for TTS Studio, Import, Library, and
Settings. `Save Settings` writes `.bookcast-workbench.json` in the repo root;
the file is ignored by Git.

Python fallback UI:

```powershell
.\.venv\Scripts\bookcast-ui --library .\library
```

Packaged Windows build:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
.\dist\bookcast-studio-windows\bookcast-studio.exe
```

Fast smoke without packaging:

```powershell
.\.venv\Scripts\python .\scripts\acceptance_smoke.py
```

## Import From CLI

```powershell
.\.venv\Scripts\bookcast import .\samples\book.epub --library .\library
.\.venv\Scripts\bookcast list --library .\library
.\.venv\Scripts\bookcast render <book-id> --library .\library --format opus
.\.venv\Scripts\bookcast render <book-id> --library .\library --format m4b
.\.venv\Scripts\bookcast bridge diagnose --library .\library
.\.venv\Scripts\bookcast bridge voices
.\.venv\Scripts\bookcast bridge audio-cpp-health --audio-cpp-exe D:\path\to\audiocpp_cli.exe --audio-cpp-model D:\path\to\model
.\.venv\Scripts\bookcast bridge book-preview <book-id> --library .\library
.\.venv\Scripts\bookcast bridge characters <book-id> --library .\library --model qwen3:8b
.\.venv\Scripts\bookcast bridge podcast-script <book-id> --library .\library --mode educational --model qwen3:8b
.\.venv\Scripts\bookcast bridge podcast-render <book-id> --library .\library --mode controversial --voice host=Narrator
.\.venv\Scripts\bookcast bridge sample-render <book-id> --library .\library
.\.venv\Scripts\bookcast bridge outputs --library .\library --book-id <book-id>
.\.venv\Scripts\bookcast bridge calibre-scan "C:\Users\you\Calibre Library"
.\.venv\Scripts\bookcast bridge calibre-import "C:\Users\you\Calibre Library" --library .\library --id 42
.\.venv\Scripts\bookcast bridge render <book-id> --library .\library --provider audio_cpp --audio-cpp-exe D:\path\to\audiocpp_cli.exe --audio-cpp-model D:\path\to\model
```

## audio.cpp

BookCast treats `audio.cpp` as an external process. The Rust workbench can check
the pinned upstream revision and shows `Update Available` if GitHub HEAD differs.
Rendering through `audio.cpp` requires the CLI executable and model path/name.
Use `Check audio.cpp` in the Rust workbench to validate both the upstream pin and
the local executable/model configuration.

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
