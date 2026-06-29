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
- Latest readiness evidence: `scripts\readiness_check.ps1` passed on 2026-06-29 with 53 Python tests, 28 Rust tests, release build, acceptance smoke, and UI launch smoke.
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
- Remaining: real-world import quality pass with large EPUBs, messy PDFs, and duplicate edge cases.

## M1.5 Calibre Import

Status: Mostly done.

- Calibre import is read-only through `calibredb`.
- Calibre scan/import supports bounded batches.
- Calibre ID based import exists.
- Diagnostics explain wrong folder, missing `metadata.db`, missing `calibredb`, and unreadable/locked library cases.
- Wizard can suggest nested/parent library folders and source-folder fallback.
- Remaining: validate against the user's real Calibre library and improve copy around failure cases.

## M2 Text Pipeline

Status: Mostly done.

- TXT, MD, EPUB, DOCX, and PDF extraction exist.
- Cleanup profiles exist.
- Chapter and chunk review exist.
- Stable chunk hashes exist.
- Chapter title/text editing and rechunking exist in the Rust Library view.
- Golden generated EPUB tests cover German and English metadata, language, spine order, headings, and entity decoding.
- Remaining: messy PDF golden tests and better chapter detection heuristics for problematic books.

## M3 Audiobook Render

Status: Mostly done.

- TTS provider interface exists.
- Windows SAPI fallback exists.
- Piper provider using local Trispr-Flow binaries/voices exists.
- Configurable `audio.cpp` external-process provider exists.
- Render cache keys include provider, voice, rate, and engine options.
- Resumable chunk rendering exists.
- ffmpeg assembly to Opus, MP3, WAV, and M4B exists.
- Chaptered export exists.
- Queue progress, cancel, retry, and output refresh exist.
- Audiobook render can use confirmed `speaker=voice` mappings for chunks that start with `Speaker:`.
- Rust TTS Studio can cycle discovered voice IDs without manual copy/paste.
- Synthetic long-render stress covers many chunks, progress, assemble, and cache resume behavior.
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
- Remaining: automatic dialogue attribution and real-world tuning of confidence/excerpt quality.

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
- Remaining: richer citation linking, deeper prompt presets, and real smoke tests with user-selected models.

## M6 Interactive Podcast

Status: Prototype, not final.

- Interactive command path exists.
- Follow-up prompts and rendered output path exist.
- Remaining: true live conversation UX, interruption while playback/rendering runs, partial audio streaming, cancellation, session memory, and resident Ollama lifecycle management.

## M7 Rust Workbench Migration

Status: Mostly done.

- Rust Slint client is the primary UI.
- Python backend remains as JSONL bridge.
- Structured views exist: TTS Studio, Import, Library, Characters, Podcast, Settings.
- Queue rows, diagnostics, import controls, TTS engine selection, output history, and startup snapshot exist.
- Guided Start view, persistent Inspector, Calibre action guidance, TTS engine setup checklist, and queue action guidance exist.
- `audio.cpp` upstream check shows update status.
- Local engine diagnostics exist.
- Settings persist in `.bookcast-workbench.json`.
- Remaining: visual polish, smoother onboarding, better empty states, better grouped settings, and MediaEncoder-grade queue clarity.

## Interface / UX Checklist

Status: Partial.

- Left navigation exists.
- Guided Start view exists.
- Persistent Inspector with next step, setup checklist, engine setup, guidance, and diagnostics exists.
- TTS Studio exists.
- Import Wizard exists.
- Library view exists.
- Character view exists.
- Podcast view exists.
- Settings view exists.
- Header guidance exists.
- Queue summary exists.
- Queue action guidance exists.
- Render sample before full render exists.
- Native Browse buttons exist for important paths.
- Discovered TTS voices can be selected with First/Previous/Next controls.
- Podcast script review can happen in app through a JSON editor with validate/save actions.
- Podcast script preview shows source-backed citations when available.
- Startup restores saved library snapshot.
- Remaining: final visual design, stronger error recovery, and less technical engine terminology.

## Current Definition Of Done Before Beta

- One real Calibre library imports predictably.
- One German EPUB renders full Opus and M4B with usable chapter structure.
- One real `audio.cpp` setup renders a sample and a short chapter.
- Queue remains readable during long render.
- Cancel/retry works during long render.
- Missing dependency errors explain exact fix.
- Interface can be used without copying IDs manually.
- User can understand next safe action from screen state alone.
