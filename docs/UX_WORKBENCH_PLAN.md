# BookCast Studio UX Workbench Plan

Stand: 2026-06-26

## Product Shape

BookCast is a production workbench, not a toolbar around a database table.
The app should guide a user from source material to audiobook output with clear
state, visible jobs, and explainable failure modes.

## Core Layout

- Left rail: Library, Import Wizard, TTS Studio, Queue, Settings.
- Center pane: the selected working surface.
- Right inspector: diagnostics, next recommended step, selected item details.
- Bottom queue: active and completed jobs, progress, logs, retry, cancel.

## Required Guidance

- Empty library: show diagnostics and import action.
- Missing `ffmpeg`: disable render and explain install/PATH issue.
- Missing Calibre: still allow file import; show Calibre setup issue only in Calibre flow.
- Missing `audio.cpp`: keep Windows SAPI/Python bridge usable; mark `audio.cpp` unavailable.
- audio.cpp upstream changed: show `Update Available`; never auto-update.
- No selected book: render action disabled or blocked with explicit message.
- No chunks: send user to cleanup/chunking step.

## Main Flows

### First Run

1. Pick or create library root.
2. Run diagnostics.
3. Show status chips for Python bridge, ffmpeg, Calibre, Windows SAPI, Ollama, audio.cpp.
4. Recommend next step based on missing pieces.

### Import Wizard

1. Select source: file, folder, Calibre.
2. Probe source.
3. Preview title, author, language, chapters, rough word count.
4. Select cleanup profile.
5. Import and enqueue chunking.
6. Open book preparation screen.

### TTS Studio

1. Select book or chapter range.
2. Select engine.
3. Select voice and output format.
4. Render short sample.
5. Queue full render.
6. Open output folder after completion.

### Queue

Every long-running operation must be a job:

- import
- Calibre scan
- cleanup
- chunking
- TTS render
- assembly
- podcast script generation
- podcast render

Each job needs:

- state
- progress
- last log line
- cancel
- retry
- output path when done

## Engine Strategy

- `windows_sapi`: existing Python provider, default fallback.
- `audio_cpp`: external process provider, configured by executable, model, backend, family.
- Future engines: add only after queue and diagnostics are stable.

## Bridge Contract

Rust calls the Python backend through:

```powershell
python -m bookcast bridge <command> ...
```

Output is JSONL. Events:

- `diagnostic`
- `books`
- `job_started`
- `job_progress`
- `job_done`
- `calibre_books`
- `error`

Rust should never parse old human-readable CLI output.

## Near-Term Implementation Order

1. Rust Slint workbench shell.
2. JSONL Python bridge.
3. Queue runtime with child-process ownership and cancel.
4. Diagnostics screen.
5. Import wizard preview.
6. TTS Studio sample render.
7. audio.cpp adapter hardening.
8. Calibre error diagnosis.

