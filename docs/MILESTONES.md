# BookCast Studio Milestones

Status legend:

- Done: implemented and covered by smoke/unit checks.
- Mostly done: usable, but needs real-world hardening.
- Partial: core exists, UX or workflow still incomplete.
- Open: not production-usable yet.

## Product Readiness

- Current state: Alpha / manual-test ready.
- Interface state: not final.
- Best current test path: run `scripts\start_manual_test.ps1`, then test one real EPUB, one Calibre import, and one short render.
- Latest readiness evidence: `scripts\readiness_check.ps1` passed on 2026-07-01 with 68 Python tests, 34 Rust tests, release build, acceptance smoke, and UI launch smoke.
- Main risk: real `audio.cpp` model setup and long-book UX have not had enough hands-on validation.

## M0 Repo Bootstrap

Status: Done.

- Python package, CLI entrypoint, and legacy PySide UI entrypoint exist.
- SQLite migration harness exists.
- Rust workspace and Slint client exist.
- README, setup notes, smoke scripts, and tests exist.

## M1 Library + Import

Status: Mostly done.

- TXT, MD, EPUB, DOCX, and PDF import exist.
- Source copies are stored in the BookCast library root.
- Books, sources, chapters, chunks, outputs, jobs, voices, speakers, and podcast data are persisted.
- Rust Library view can show books, previews, chapters, outputs, and selected book state.
- Folder import is recursive and reuses already imported file hashes instead of creating duplicate books.
- Remaining: real-world import quality pass with large EPUBs and messy PDFs.

## M1.5 Calibre Import

Status: Mostly done.

- Calibre import is read-only through `calibredb`.
- Calibre scan/import supports bounded batches.
- Calibre ID based import exists.
- Diagnostics explain wrong folder, missing `metadata.db`, missing `calibredb`, and unreadable/locked library cases.
- Wizard can suggest nested/parent library folders and source-folder fallback.
- Rust Calibre wizard can browse and persist a custom `calibredb.exe` path when Calibre is not in PATH.
- Rust Calibre wizard can search common Windows user folders for candidate libraries and apply the first candidate for diagnosis.
- `calibredb.exe` discovery checks PATH, common Windows install folders, portable/local app folders, Scoop, Chocolatey, and registry install locations.
- Remaining: validate against the user's real Calibre library and polish real-world failure cases.

## M2 Text Pipeline

Status: Mostly done.

- TXT, MD, EPUB, DOCX, and PDF extraction exist.
- Cleanup profiles exist.
- Chapter and chunk review exist.
- Stable chunk hashes exist.
- Chapter title/text editing and rechunking exist in the Rust Library view.
- Golden generated EPUB tests cover German and English metadata, language, spine order, headings, and entity decoding.
- Golden generated messy PDF tests cover page extraction, filename metadata, whitespace cleanup, and hyphenated line joining.
- TXT/MD import now detects Markdown headings and English/German chapter heading lines.
- Remaining: real-world tuning of chapter detection heuristics for problematic books.

## M3 Audiobook Render

Status: Mostly done.

- TTS provider interface exists.
- Windows SAPI fallback exists.
- Piper provider using local Trispr-Flow binaries/voices exists.
- Configurable `audio.cpp` external-process provider exists.
- `audio.cpp` health validates configured family against CLI-reported TTS families.
- `audio.cpp` setup can search bounded local model folders and fill the first model candidate before health check.
- Render cache keys include provider, voice, rate, and engine options.
- Resumable chunk rendering exists.
- ffmpeg assembly to Opus, MP3, WAV, and M4B exists.
- Rust settings can use custom `ffmpeg.exe` and `ffprobe.exe` paths for export and M4B chapter timing.
- Manual test launcher can prefill ffmpeg/ffprobe and real `audio.cpp` engine paths.
- Manual test launcher can generate a synthetic long book and prefill a bounded chunk limit for queue/cancel/retry validation.
- Beta readiness report marks synthetic readiness, real Calibre readiness, and real `audio.cpp` readiness as OK/TODO/BLOCKED.
- Beta readiness report reuses the app Calibre diagnosis for parent-folder suggestions, nested-library candidates, and source-folder fallback.
- Beta readiness report searches for Calibre library candidates when no real Calibre path is supplied.
- Beta readiness report lists local `audio.cpp` TTS families and blocks invalid configured families in strict mode.
- Beta readiness report can search a supplied `-AudioCppModelRoot` for likely model files without scanning broad cache folders.
- Chaptered export exists.
- Queue progress, cancel, retry, and output refresh exist.
- Queue cards show elapsed runtime, ETA, and chunks/min for long renders.
- Queue summary retains elapsed duration for completed, cancelled, and failed jobs.
- Queue summary shows compact counts by job status.
- Cancelled jobs stay marked as cancelled instead of being overwritten as failed after process exit.
- Audiobook render can use confirmed `speaker=voice` mappings for chunks that start with `Speaker:`.
- Rust TTS Studio can cycle discovered voice IDs without manual copy/paste.
- Synthetic long-render stress covers many chunks, progress, assemble, and cache resume behavior.
- Acceptance smoke imports a generated German EPUB, renders Opus plus M4B, and verifies chapter marks through `ffprobe`.
- Remaining: validate real `audio.cpp` model/family combinations end-to-end and stress-test real full-book renders.

## M4 Voices + Characters

Status: Partial.

- Narrator/speaker data model exists.
- Ollama-assisted character suggestions exist.
- Speaker-to-voice mappings exist.
- Manual confirmation before multi-speaker podcast and audiobook render exists.
- Rust Characters view now seeds an editable `speaker=voice` review template from LLM candidates.
- Rust Characters view shows confidence and excerpt fields when the LLM returns them.
- Prefix-based per-character audiobook casting exists for reviewed `Speaker:` chunks.
- Basic dialogue-tag casting exists for reviewed voices when chunks contain patterns like `"..." said Ada` or `"..." sagte Ada`.
- Dialogue-tag casting checks multiple quoted spans and supports more English/German tags such as `asked`, `cried`, `erwiderte`, `fragte`, and `entgegnete`.
- Remaining: deeper automatic dialogue attribution and real-world tuning of confidence/excerpt quality.

## M5 Static Podcast Generator

Status: Partial / usable prototype.

- Educational, controversial, and interview modes exist.
- Script generation through Ollama bridge exists.
- Multi-speaker podcast render exists.
- Rust views expose static podcast generation and render.
- Rust Podcast view shows speaker/turn review guidance and requires confirmed `speaker=voice` mappings.
- Podcast render can reuse a saved reviewed script JSON instead of regenerating through Ollama.
- Rust Podcast view can browse, open, open folder for, reload, edit, validate, and save reviewed script JSON.
- Podcast scripts can include review citations and Rust preview displays them.
- Rust Podcast view exposes focus/style prompt controls for script generation.
- Rust Podcast view has one-click prompt presets for educational, controversial, and interview scripts.
- Remaining: richer citation linking and real smoke tests with user-selected models.

## M6 Interactive Podcast

Status: Prototype, not final.

- Interactive command path exists.
- Follow-up prompts and rendered output path exist.
- Rust Podcast view surfaces the saved interactive `session.json` path/transcript after render.
- Remaining: true live conversation UX, interruption while playback/rendering runs, partial audio streaming, cancellation, session memory, and resident Ollama lifecycle management.

## M7 Rust Workbench Migration

Status: Mostly done.

- Rust Slint client is the primary UI.
- Python backend remains as JSONL bridge.
- Structured views exist: TTS Studio, Import, Library, Characters, Podcast, Settings.
- Queue rows, diagnostics, import controls, TTS engine selection, output history, and startup snapshot exist.
- Guided Start view, persistent Inspector, Calibre action guidance, TTS engine setup checklist, and queue action guidance exist.
- `audio.cpp` upstream check shows update status at startup and on refresh.
- Local engine diagnostics exist.
- Settings persist in `.bookcast-workbench.json`.
- Settings view is grouped into library/render defaults, media tools, voice engines, and AI/Ollama.
- Empty states point to the next useful action instead of generic blank text.
- Start view includes a fast-path checklist and a direct Settings escape hatch for setup fixes.
- Remaining: visual polish and MediaEncoder-grade queue clarity.

## Interface / UX Checklist

Status: Partial.

- Left navigation exists.
- Guided Start view exists.
- Guided Start shows the first-run fast path from Diagnose to sample render.
- Persistent Inspector with next step, setup checklist, engine setup, guidance, and diagnostics exists.
- TTS Studio exists.
- Import Wizard exists.
- Library view exists.
- Character view exists.
- Podcast view exists.
- Settings view exists.
- Settings view uses clear setup groups instead of one flat technical list.
- Header guidance exists.
- Queue summary exists.
- Queue action guidance exists.
- Queue job cards show progress, status, detail, elapsed runtime, and ETA.
- Queue job cards add chunk throughput when chunk progress events provide enough timing data.
- Queue summary preserves duration after done/failed/cancelled outcomes.
- Queue summary includes compact running/done/failed/cancelled counts.
- Cancelled jobs show a Retry Last recovery action.
- Duplicate source imports are shown as reused duplicates in the queue/guide text.
- Render sample before full render exists.
- Native Browse buttons exist for important paths, including ffmpeg/ffprobe.
- Discovered TTS voices can be selected with First/Previous/Next controls.
- TTS Studio uses user-facing voice engine labels and inline guidance instead of raw provider/process wording.
- Common bridge failures are translated into next-action recovery guidance for ffmpeg, ffprobe, calibredb, Calibre libraries, audio.cpp, Piper, and Ollama.
- Podcast script review can happen in app through a JSON editor with validate/save actions.
- Podcast script preview shows source-backed citations when available.
- Podcast prompt presets reduce blank-state setup for educational, controversial, and interview scripts.
- Startup restores saved library snapshot.
- Empty states explain the next click for imports, books, previews, voices, outputs, characters, podcasts, and queue work.
- Manual test launcher prints a concrete beta pass checklist after preparing the library.
- Manual test launcher prints a beta readiness report for local blockers/TODOs.
- Manual test launcher has a long-book mode for queue progress, ETA, chunks/min, cancel, and retry validation.
- Remaining: final visual design and real-world error recovery polish.

## Current Definition Of Done Before Beta

- One real Calibre library imports predictably.
- One German EPUB renders full Opus and M4B with usable chapter structure.
- One real `audio.cpp` setup renders a sample and a short chapter.
- Queue remains readable during long render.
- Cancel/retry works during long render.
- Missing `ffmpeg`/`ffprobe` errors explain exact install/PATH/full-path fix.
- Interface can be used without copying IDs manually.
- User can understand next safe action from screen state alone.
