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
- Interactive podcast sessions with resident Ollama, follow-up prompts, and rendered output.
- Confirmed speaker-to-voice mapping before podcast or character-style multi-voice rendering.
- Text cleanup and stable chunk hashes.
- Editable cleanup profiles and chapter review/editing in the Python UI and Rust Library view.
- Character and podcast workbench views in the Rust UI.
- Header readiness guidance and queue summary for the next safe action.

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

The Rust workbench has separate views for Start, TTS Studio, Import, Library,
Characters, Podcast, and Settings. The Start view guides the first run through
diagnostics, import, text preparation, and sample render, with a fast-path box
and direct Settings escape hatch for setup fixes. `Save Settings` writes
`.bookcast-workbench.json` in the repo root;
the file is ignored by Git.
TTS Studio shows a render plan and blocks obvious bad jobs before they hit the
Python bridge: missing book id, unsupported output format, missing Piper exe, or
missing `audio.cpp` executable/model.
Render jobs emit chunk/turn-level progress for TTS and assembly so the queue can
show where long audiobook or podcast renders currently are; queue cards also
show elapsed time and ETA for long-running jobs.
Queue summaries keep elapsed time for completed, cancelled, and failed jobs, so
the last outcome stays readable after a long render.
Queue summaries also show compact job counts by status for quick backlog reading.
The header shows the next safe action from current book, engine-check, output,
and queue state; the queue footer highlights the active or failed job before the
raw job log.
Podcast render requires explicit `speaker=voice` entries plus confirmation after
manual review; the Rust checkbox is intentionally not persisted.
Imports emit the first book preview automatically and the Rust workbench switches
back to TTS Studio, reducing manual book-id copy/paste after file or Calibre import.
`Refresh Books` in the Rust workbench also asks the bridge for a first-book
preview, so reopening a library lands on a renderable book faster.
Output history is shown in TTS Studio, Library, and Podcast views; renders emit
fresh output lists automatically and `Refresh Outputs` reloads them on demand.
Rendered output can be opened as a file for playback or as a folder for manual
inspection from each output view.
The Rust queue runs one bridge job at a time so cancel targets the correct
process. `Retry Last` repeats the previous bridge job after a failure or manual
cancel.
Empty states point to the next useful click for imports, books, previews,
voices, outputs, characters, podcasts, and queue work.
TTS Studio hides irrelevant engine fields: Windows SAPI shows no paths, Piper
shows only Piper paths, and `audio.cpp` shows only its executable/model/backend
configuration.
Use `Check Engine` before rendering; it validates the selected engine and shows
the exact missing executable/model path when configuration is incomplete.
TTS Studio also has a free-text TTS test that writes a WAV through the selected
engine without needing a book.
The Library view can load cleanup profiles and apply one to the selected book;
that rechunks the book and refreshes the preview before rendering.
The Library view can also load one chapter, edit its title/text, then save and
rechunk the book before rendering.
Path fields for library, imports, Calibre, ffmpeg/ffprobe, Piper, and
`audio.cpp` have native Browse buttons so first setup does not depend on manual
Windows path typing.
Settings are grouped into library/render defaults, media tools, voice engines,
and AI/Ollama instead of one flat technical list.
Calibre discovery checks PATH, common Windows install folders, portable/local
app folders, Scoop, Chocolatey, and registry install locations before asking
for a manual `calibredb.exe` path.
After `Refresh Books`, TTS Studio and Library can switch books with
`Previous Book` / `Next Book` and reload the preview automatically.
The Import Wizard uses the selected cleanup profile for both local and Calibre
imports, so chunking can be chosen before text enters the library.
Use `Probe Source` before local import to inspect metadata, chapter sizes, and
the first text preview without writing anything into the library.
Book previews now show chapter summaries plus the first chunk hashes, lengths,
statuses, and text excerpts, which makes cleanup/chunking verifiable before TTS.
Full renders can be limited to the first N chunks from TTS Studio for controlled
batch testing; sample render still renders exactly one chunk.

Python fallback UI:

```powershell
.\.venv\Scripts\bookcast-ui --library .\library
```

Packaged Windows build:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\readiness_check.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_manual_test.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\ui_launch_smoke.ps1
.\dist\bookcast-studio-windows\bookcast-studio.exe
```

Fast smoke without packaging:

```powershell
.\.venv\Scripts\python .\scripts\acceptance_smoke.py
```

The smoke imports a generated German EPUB, renders sample + full Opus + M4B
through Windows SAPI, checks output registration, and validates rendered audio
duration plus M4B chapter marks with `ffprobe`.
If the local Trispr-Flow Piper install exists, it also renders a Piper sample.
The UI launch smoke starts the packaged desktop app briefly and fails if it exits
early.
`readiness_check.ps1` runs the full build, acceptance smoke, UI launch smoke, and
prints the packaged executable path for manual testing.
`start_manual_test.ps1` prepares a persistent `.manual-test` library, points the
workbench at that book, and launches the desktop app for hands-on testing.
For a real Calibre pass, prefill the wizard:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_manual_test.ps1 -CalibreLibrary "D:\Books\Calibre Library" -CalibredbExe "C:\Program Files\Calibre2\calibredb.exe"
```

For a real `audio.cpp` pass, prefill the engine setup:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_manual_test.ps1 -AudioCppExe "D:\GIT\audio.cpp\build\windows-cpu-release\bin\audiocpp_cli.exe" -AudioCppModel "D:\models\tts-model.gguf" -AudioCppFamily "pocket_tts"
```

On startup, the Rust workbench auto-loads the saved library snapshot: book list,
selected book preview, and outputs.

Manual beta pass checklist:

1. Start view: run Diagnose.
2. TTS Studio: Check Engine, then Render TTS Test.
3. Render Sample and play it with Open File.
4. Render M4B and inspect the output folder.
5. If Calibre is configured: Diagnose Calibre, Scan Calibre, Import selected IDs.
6. If audio.cpp is configured: Check audio.cpp, render a sample, then render a short chapter/full book.

## Import From CLI

```powershell
.\.venv\Scripts\bookcast import .\samples\book.epub --library .\library
.\.venv\Scripts\bookcast list --library .\library
.\.venv\Scripts\bookcast render <book-id> --library .\library --format opus
.\.venv\Scripts\bookcast render <book-id> --library .\library --format m4b
.\.venv\Scripts\bookcast bridge diagnose --library .\library
.\.venv\Scripts\bookcast bridge startup-snapshot --library .\library --book-id <book-id>
.\.venv\Scripts\bookcast bridge voices
.\.venv\Scripts\bookcast bridge voices --provider piper --piper-exe D:\GIT\Trispr_Flow\src-tauri\bin\piper\piper.exe --piper-voice-dir D:\GIT\Trispr_Flow\src-tauri\bin\piper\voices
.\.venv\Scripts\bookcast bridge tts-test --library .\library --text "Engine smoke test."
.\.venv\Scripts\bookcast bridge audio-cpp-health --audio-cpp-model D:\path\to\model --audio-cpp-family pocket_tts
.\.venv\Scripts\bookcast bridge source-probe .\samples\book.epub
.\.venv\Scripts\bookcast bridge book-preview <book-id> --library .\library
.\.venv\Scripts\bookcast bridge cleanup-profiles --library .\library
.\.venv\Scripts\bookcast bridge set-cleanup-profile <book-id> --library .\library --cleanup-profile standard
.\.venv\Scripts\bookcast bridge chapter-detail <book-id> --library .\library --chapter-index 0
.\.venv\Scripts\bookcast bridge update-chapter <book-id> --library .\library --chapter-index 0 --title "Fixed Chapter" --text "Corrected text."
.\.venv\Scripts\bookcast bridge characters <book-id> --library .\library --model qwen3:8b
.\.venv\Scripts\bookcast bridge podcast-script <book-id> --library .\library --mode educational --model qwen3:8b
.\.venv\Scripts\bookcast bridge podcast-render <book-id> --library .\library --mode controversial --voice host=Narrator --voice position_a=Guest --confirm-voices
.\.venv\Scripts\bookcast bridge podcast-interactive <book-id> --library .\library --mode interview --turns 4 --seed-prompt "Start with the core question" --voice host=Narrator --confirm-voices
.\.venv\Scripts\bookcast bridge sample-render <book-id> --library .\library
.\.venv\Scripts\bookcast bridge sample-render <book-id> --library .\library --provider piper --voice D:\GIT\Trispr_Flow\src-tauri\bin\piper\voices\de_DE-thorsten-medium.onnx
.\.venv\Scripts\bookcast bridge outputs --library .\library --book-id <book-id>
.\.venv\Scripts\bookcast bridge calibre-diagnose "C:\Users\you\Calibre Library"
.\.venv\Scripts\bookcast bridge calibre-scan "C:\Users\you\Calibre Library"
.\.venv\Scripts\bookcast bridge calibre-import "C:\Users\you\Calibre Library" --library .\library --id 42
.\.venv\Scripts\bookcast bridge render <book-id> --library .\library --provider audio_cpp --audio-cpp-model D:\path\to\model --audio-cpp-family <family>
```

## audio.cpp

BookCast treats `audio.cpp` as an external process. The Rust workbench checks
the pinned upstream revision at startup and on `Check audio.cpp`, then shows
`Update Available` if GitHub HEAD differs.
The default Windows CLI path is:

```powershell
D:\GIT\audio.cpp\build\windows-cpu-release\bin\audiocpp_cli.exe
```

Rendering through `audio.cpp` requires a model path/name and a family such as
`pocket_tts` or `qwen3_tts`. The provider calls
`audiocpp_cli --task tts --family <family> --mode offline`; a voice value that
points to an existing WAV file is passed as `--voice-ref`, otherwise it is
passed as `--voice-id`. Use `Check audio.cpp` in the Rust workbench to validate
the upstream pin, local executable/model/family configuration, and registered
TTS families.

## Import From Calibre

BookCast reads Calibre through the official `calibredb` CLI and copies exported
files into its own library. It does not write back to Calibre.
The Rust Import Wizard diagnoses wrong folders, missing `metadata.db`, missing
`calibredb`, and locked/unreadable libraries before scanning.
It searches PATH, common Windows install folders, portable/local app folders,
Scoop, Chocolatey, and registry install locations for `calibredb.exe`.
It exposes this as an explicit `Diagnose Calibre` step before `Scan Calibre`.
Calibre scan/import can be limited from the wizard, defaulting to 50 books, so
large libraries can be tested in bounded batches.
If the selected folder is too high or too deep, the wizard shows suggested
parent/child library folders. Scans fill visible Calibre IDs into the import
field; remove IDs you do not want before importing.
Local import accepts either a single supported file or a folder; folder import
recursively imports TXT, MD, EPUB, DOCX, and PDF files while skipping unrelated files.

```powershell
.\.venv\Scripts\bookcast calibre scan "C:\Users\you\Calibre Library"
.\.venv\Scripts\bookcast calibre import "C:\Users\you\Calibre Library" --library .\library --id 42
```

Calibre import accepts `EPUB`, `DOCX`, `TXT`, `MD`, and `PDF`, preferring better
structured formats before falling back to PDF.

## Ollama Tools

These commands require a running Ollama server.

```powershell
.\.venv\Scripts\bookcast characters suggest <book-id> --library .\library --model qwen3:8b
.\.venv\Scripts\bookcast podcast script <book-id> --library .\library --mode educational --model qwen3:8b
.\.venv\Scripts\bookcast podcast render <book-id> --library .\library --mode controversial --format opus --voice host=Narrator --voice explainer=Guest --confirm-voices
.\.venv\Scripts\bookcast podcast interactive <book-id> --library .\library --mode interview --turns 4 --voice host=Narrator --confirm-voices --no-playback
```

Podcast modes: `educational`, `controversial`, `interview`.
