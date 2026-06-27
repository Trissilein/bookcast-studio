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
- Windows SAPI and configurable `audio.cpp` TTS chunk rendering through `audiocpp_cli`.
- Piper local TTS via the existing Trispr-Flow Piper binary/voices when present.
- ffmpeg assembly to Opus, MP3, WAV, or M4B.
- Ollama-assisted character suggestions, static podcast scripts, and podcast render.
- Interactive podcast sessions with resident Ollama and live follow-ups.
- Text cleanup and stable chunk hashes.
- Editable cleanup profiles and chapter review in the Python UI.
- Character and podcast workbench views in the Rust UI.

Planned later:

- Additional TTS providers beyond Windows SAPI, Piper, and `audio.cpp`.
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
TTS Studio shows a render plan and blocks obvious bad jobs before they hit the
Python bridge: missing book id, unsupported output format, missing Piper exe, or
missing `audio.cpp` executable/model.
Render jobs emit chunk/turn-level progress for TTS and assembly so the queue can
show where long audiobook or podcast renders currently are.
Imports emit the first book preview automatically and the Rust workbench switches
back to TTS Studio, reducing manual book-id copy/paste after file or Calibre import.
`Refresh Books` in the Rust workbench also asks the bridge for a first-book
preview, so reopening a library lands on a renderable book faster.
Output history is shown in TTS Studio, Library, and Podcast views; renders emit
fresh output lists automatically and `Refresh Outputs` reloads them on demand.
TTS Studio hides irrelevant engine fields: Windows SAPI shows no paths, Piper
shows only Piper paths, and `audio.cpp` shows only its executable/model/backend
configuration.
The Library view can load cleanup profiles and apply one to the selected book;
that rechunks the book and refreshes the preview before rendering.
Path fields for library, imports, Calibre, Piper, and `audio.cpp` have native
Browse buttons so first setup does not depend on manual Windows path typing.
After `Refresh Books`, TTS Studio and Library can switch books with
`Previous Book` / `Next Book` and reload the preview automatically.

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
.\.venv\Scripts\bookcast bridge voices --provider piper --piper-exe D:\GIT\Trispr_Flow\src-tauri\bin\piper\piper.exe --piper-voice-dir D:\GIT\Trispr_Flow\src-tauri\bin\piper\voices
.\.venv\Scripts\bookcast bridge audio-cpp-health --audio-cpp-model D:\path\to\model
.\.venv\Scripts\bookcast bridge book-preview <book-id> --library .\library
.\.venv\Scripts\bookcast bridge cleanup-profiles --library .\library
.\.venv\Scripts\bookcast bridge set-cleanup-profile <book-id> --library .\library --cleanup-profile standard
.\.venv\Scripts\bookcast bridge characters <book-id> --library .\library --model qwen3:8b
.\.venv\Scripts\bookcast bridge podcast-script <book-id> --library .\library --mode educational --model qwen3:8b
.\.venv\Scripts\bookcast bridge podcast-render <book-id> --library .\library --mode controversial --voice host=Narrator
.\.venv\Scripts\bookcast bridge sample-render <book-id> --library .\library
.\.venv\Scripts\bookcast bridge sample-render <book-id> --library .\library --provider piper --voice D:\GIT\Trispr_Flow\src-tauri\bin\piper\voices\de_DE-thorsten-medium.onnx
.\.venv\Scripts\bookcast bridge outputs --library .\library --book-id <book-id>
.\.venv\Scripts\bookcast bridge calibre-diagnose "C:\Users\you\Calibre Library"
.\.venv\Scripts\bookcast bridge calibre-scan "C:\Users\you\Calibre Library"
.\.venv\Scripts\bookcast bridge calibre-import "C:\Users\you\Calibre Library" --library .\library --id 42
.\.venv\Scripts\bookcast bridge render <book-id> --library .\library --provider audio_cpp --audio-cpp-model D:\path\to\model --audio-cpp-family <family>
```

## audio.cpp

BookCast treats `audio.cpp` as an external process. The Rust workbench can check
the pinned upstream revision and shows `Update Available` if GitHub HEAD differs.
The default Windows CLI path is:

```powershell
D:\GIT\audio.cpp\build\windows-cpu-release\bin\audiocpp_cli.exe
```

Rendering through `audio.cpp` requires a model path/name and usually a family
name. The provider calls `audiocpp_cli --task tts --mode offline`; a voice value
that points to an existing WAV file is passed as `--voice-ref`, otherwise it is
passed as `--speaker`. Use `Check audio.cpp` in the Rust workbench to validate
both the upstream pin and the local executable/model configuration.

## Import From Calibre

BookCast reads Calibre through the official `calibredb` CLI and copies exported
files into its own library. It does not write back to Calibre.
The Rust Import Wizard diagnoses wrong folders, missing `metadata.db`, missing
`calibredb`, and locked/unreadable libraries before scanning.
It exposes this as an explicit `Diagnose Calibre` step before `Scan Calibre`.
Local import accepts either a single supported file or a folder; folder import
recursively imports TXT, MD, EPUB, DOCX, and PDF files while skipping unrelated files.

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
