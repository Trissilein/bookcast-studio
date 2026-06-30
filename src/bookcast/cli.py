from __future__ import annotations

import argparse
import json
from pathlib import Path

from .assembler import assemble_audio
from . import bridge
from .calibre import CalibreClient, find_calibredb
from .characters import suggest_characters
from .library import BookLibrary, safe_name
from .llm import OllamaProvider
from .podcast import PODCAST_MODES, PodcastTurn, generate_interactive_step, generate_podcast_script
from .tts import AudioCppProvider, PiperProvider, WindowsSapiProvider, play_wav


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bookcast")
    sub = parser.add_subparsers(dest="command", required=True)

    import_parser = sub.add_parser("import", help="Import a TXT, MD, or EPUB source into a library")
    import_parser.add_argument("file", type=Path)
    import_parser.add_argument("--library", type=Path, required=True)
    import_parser.add_argument("--cleanup-profile", default="standard")

    list_parser = sub.add_parser("list", help="List imported books")
    list_parser.add_argument("--library", type=Path, required=True)

    render_parser = sub.add_parser("render", help="Render a book to audio")
    render_parser.add_argument("book_id")
    render_parser.add_argument("--library", type=Path, required=True)
    render_parser.add_argument("--format", choices=["opus", "mp3", "wav", "m4b"], default="opus")
    render_parser.add_argument("--voice", default=None)
    render_parser.add_argument("--speaker-voice", action="append", default=[], help="Speaker=Voice mapping for chunks starting with Speaker:")
    render_parser.add_argument("--confirm-speaker-voices", action="store_true", help="Confirm reviewed audiobook speaker=voice mappings")
    render_parser.add_argument("--rate", type=int, default=0)
    render_parser.add_argument("--limit", type=int, default=None, help="Render only the first N chunks")
    render_parser.add_argument("--ffmpeg", default="ffmpeg")
    render_parser.add_argument("--ffprobe", default="ffprobe")
    render_parser.add_argument("--provider", choices=["windows_sapi", "piper", "audio_cpp"], default="windows_sapi")
    render_parser.add_argument("--audio-cpp-exe", default=None)
    render_parser.add_argument("--audio-cpp-model", default=None)
    render_parser.add_argument("--audio-cpp-backend", default="cpu")
    render_parser.add_argument("--audio-cpp-family", default=None)
    render_parser.add_argument("--piper-exe", default=None)
    render_parser.add_argument("--piper-voice-dir", default=None)
    render_parser.add_argument("--piper-model", default=None)

    characters_parser = sub.add_parser("characters", help="LLM-assisted character tools")
    characters_sub = characters_parser.add_subparsers(dest="characters_command", required=True)
    characters_suggest = characters_sub.add_parser("suggest", help="Suggest speakers/characters for a book")
    characters_suggest.add_argument("book_id")
    characters_suggest.add_argument("--library", type=Path, required=True)
    characters_suggest.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    characters_suggest.add_argument("--model", default="qwen3:8b")

    podcast_parser = sub.add_parser("podcast", help="Static podcast generation")
    podcast_sub = podcast_parser.add_subparsers(dest="podcast_command", required=True)
    podcast_script = podcast_sub.add_parser("script", help="Generate a static podcast script from a book")
    podcast_script.add_argument("book_id")
    podcast_script.add_argument("--library", type=Path, required=True)
    podcast_script.add_argument("--mode", choices=sorted(PODCAST_MODES), default="educational")
    podcast_script.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    podcast_script.add_argument("--model", default="qwen3:8b")

    podcast_render = podcast_sub.add_parser("render", help="Generate and render a podcast episode")
    podcast_render.add_argument("book_id")
    podcast_render.add_argument("--library", type=Path, required=True)
    podcast_render.add_argument("--mode", choices=sorted(PODCAST_MODES), default="educational")
    podcast_render.add_argument("--format", choices=["opus", "mp3", "wav", "m4b"], default="opus")
    podcast_render.add_argument("--voice", action="append", default=[], help="Speaker=Voice mapping")
    podcast_render.add_argument("--confirm-voices", action="store_true", help="Confirm reviewed speaker=voice mappings")
    podcast_render.add_argument("--rate", type=int, default=0)
    podcast_render.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    podcast_render.add_argument("--model", default="qwen3:8b")
    podcast_render.add_argument("--ffmpeg", default="ffmpeg")
    podcast_render.add_argument("--ffprobe", default="ffprobe")

    podcast_interactive = podcast_sub.add_parser("interactive", help="Run a live interactive podcast session")
    podcast_interactive.add_argument("book_id")
    podcast_interactive.add_argument("--library", type=Path, required=True)
    podcast_interactive.add_argument("--mode", choices=sorted(PODCAST_MODES), default="educational")
    podcast_interactive.add_argument("--format", choices=["opus", "mp3", "wav", "m4b"], default="opus")
    podcast_interactive.add_argument("--voice", action="append", default=[], help="Speaker=Voice mapping")
    podcast_interactive.add_argument("--confirm-voices", action="store_true", help="Confirm reviewed speaker=voice mappings")
    podcast_interactive.add_argument("--rate", type=int, default=0)
    podcast_interactive.add_argument("--turns", type=int, default=6)
    podcast_interactive.add_argument("--playback", action=argparse.BooleanOptionalAction, default=True)
    podcast_interactive.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    podcast_interactive.add_argument("--model", default="qwen3:8b")
    podcast_interactive.add_argument("--ffmpeg", default="ffmpeg")
    podcast_interactive.add_argument("--seed-prompt", default=None)

    calibre_parser = sub.add_parser("calibre", help="Import from a Calibre library")
    calibre_sub = calibre_parser.add_subparsers(dest="calibre_command", required=True)

    calibre_scan = calibre_sub.add_parser("scan", help="List supported Calibre books")
    calibre_scan.add_argument("calibre_library", type=Path)
    calibre_scan.add_argument("--calibredb", default=None)
    calibre_scan.add_argument("--search", default=None)
    calibre_scan.add_argument("--limit", type=int, default=None)

    calibre_import = calibre_sub.add_parser("import", help="Import selected Calibre books")
    calibre_import.add_argument("calibre_library", type=Path)
    calibre_import.add_argument("--library", type=Path, required=True)
    calibre_import.add_argument("--calibredb", default=None)
    calibre_import.add_argument("--id", action="append", dest="ids", default=[])
    calibre_import.add_argument("--search", default=None)
    calibre_import.add_argument("--limit", type=int, default=None)
    calibre_import.add_argument("--cleanup-profile", default="standard")

    bridge_parser = sub.add_parser("bridge", help="Machine-readable JSONL bridge for the Rust client")
    bridge_sub = bridge_parser.add_subparsers(dest="bridge_command", required=True)

    bridge_diagnose = bridge_sub.add_parser("diagnose", help="Emit local tool diagnostics as JSONL")
    bridge_diagnose.add_argument("--library", type=Path, required=True)
    bridge_diagnose.add_argument("--ffmpeg", default=None)
    bridge_diagnose.add_argument("--ffprobe", default=None)

    bridge_voices = bridge_sub.add_parser("voices", help="Emit TTS voices as JSONL")
    bridge_voices.add_argument("--provider", choices=["windows_sapi", "piper", "audio_cpp"], default="windows_sapi")
    bridge_voices.add_argument("--audio-cpp-exe", default=None)
    bridge_voices.add_argument("--audio-cpp-model", default=None)
    bridge_voices.add_argument("--audio-cpp-backend", default="cpu")
    bridge_voices.add_argument("--audio-cpp-family", default=None)
    bridge_voices.add_argument("--piper-exe", default=None)
    bridge_voices.add_argument("--piper-voice-dir", default=None)
    bridge_voices.add_argument("--piper-model", default=None)

    bridge_tts_test = bridge_sub.add_parser("tts-test", help="Synthesize free text through a TTS provider")
    bridge_tts_test.add_argument("--library", type=Path, required=True)
    bridge_tts_test.add_argument("--text", required=True)
    bridge_tts_test.add_argument("--voice", default=None)
    bridge_tts_test.add_argument("--rate", type=int, default=0)
    bridge_tts_test.add_argument("--provider", choices=["windows_sapi", "piper", "audio_cpp"], default="windows_sapi")
    bridge_tts_test.add_argument("--audio-cpp-exe", default=None)
    bridge_tts_test.add_argument("--audio-cpp-model", default=None)
    bridge_tts_test.add_argument("--audio-cpp-backend", default="cpu")
    bridge_tts_test.add_argument("--audio-cpp-family", default=None)
    bridge_tts_test.add_argument("--piper-exe", default=None)
    bridge_tts_test.add_argument("--piper-voice-dir", default=None)
    bridge_tts_test.add_argument("--piper-model", default=None)

    bridge_audio_cpp = bridge_sub.add_parser("audio-cpp-health", help="Validate local audio.cpp configuration")
    bridge_audio_cpp.add_argument("--audio-cpp-exe", default=None)
    bridge_audio_cpp.add_argument("--audio-cpp-model", default=None)
    bridge_audio_cpp.add_argument("--audio-cpp-backend", default="cpu")
    bridge_audio_cpp.add_argument("--audio-cpp-family", default=None)

    bridge_list = bridge_sub.add_parser("list", help="Emit imported books as JSONL")
    bridge_list.add_argument("--library", type=Path, required=True)
    bridge_list.add_argument("--preview-first", action="store_true")

    bridge_startup = bridge_sub.add_parser("startup-snapshot", help="Emit books, selected preview, and outputs")
    bridge_startup.add_argument("--library", type=Path, required=True)
    bridge_startup.add_argument("--book-id", default=None)

    bridge_outputs = bridge_sub.add_parser("outputs", help="Emit rendered outputs as JSONL")
    bridge_outputs.add_argument("--library", type=Path, required=True)
    bridge_outputs.add_argument("--book-id", default=None)

    bridge_cleanup_profiles = bridge_sub.add_parser("cleanup-profiles", help="Emit cleanup profiles as JSONL")
    bridge_cleanup_profiles.add_argument("--library", type=Path, required=True)

    bridge_set_cleanup = bridge_sub.add_parser("set-cleanup-profile", help="Set cleanup profile and rechunk a book")
    bridge_set_cleanup.add_argument("book_id")
    bridge_set_cleanup.add_argument("--library", type=Path, required=True)
    bridge_set_cleanup.add_argument("--cleanup-profile", required=True)

    bridge_preview = bridge_sub.add_parser("book-preview", help="Emit book chapters, chunks and text preview as JSONL")
    bridge_preview.add_argument("book_id")
    bridge_preview.add_argument("--library", type=Path, required=True)
    bridge_preview.add_argument("--max-chars", type=int, default=1400)

    bridge_chapter = bridge_sub.add_parser("chapter-detail", help="Emit one full chapter for editing")
    bridge_chapter.add_argument("book_id")
    bridge_chapter.add_argument("--library", type=Path, required=True)
    bridge_chapter.add_argument("--chapter-index", type=int, required=True)

    bridge_update_chapter = bridge_sub.add_parser("update-chapter", help="Update one chapter and rechunk")
    bridge_update_chapter.add_argument("book_id")
    bridge_update_chapter.add_argument("--library", type=Path, required=True)
    bridge_update_chapter.add_argument("--chapter-index", type=int, required=True)
    bridge_update_chapter.add_argument("--title", required=True)
    bridge_update_chapter.add_argument("--text", required=True)

    bridge_characters = bridge_sub.add_parser("characters", help="Suggest characters and emit JSONL")
    bridge_characters.add_argument("book_id")
    bridge_characters.add_argument("--library", type=Path, required=True)
    bridge_characters.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    bridge_characters.add_argument("--model", default="qwen3:8b")

    bridge_podcast_script = bridge_sub.add_parser("podcast-script", help="Generate a podcast script and emit JSONL")
    bridge_podcast_script.add_argument("book_id")
    bridge_podcast_script.add_argument("--library", type=Path, required=True)
    bridge_podcast_script.add_argument("--mode", choices=sorted(PODCAST_MODES), default="educational")
    bridge_podcast_script.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    bridge_podcast_script.add_argument("--model", default="qwen3:8b")
    bridge_podcast_script.add_argument("--focus", default=None)
    bridge_podcast_script.add_argument("--style", default=None)

    bridge_podcast_render = bridge_sub.add_parser("podcast-render", help="Generate and render a podcast as JSONL")
    bridge_podcast_render.add_argument("book_id")
    bridge_podcast_render.add_argument("--library", type=Path, required=True)
    bridge_podcast_render.add_argument("--mode", choices=sorted(PODCAST_MODES), default="educational")
    bridge_podcast_render.add_argument("--format", choices=["opus", "mp3", "wav", "m4b"], default="opus")
    bridge_podcast_render.add_argument("--voice", action="append", default=[], help="Speaker=Voice mapping")
    bridge_podcast_render.add_argument("--confirm-voices", action="store_true", help="Confirm reviewed speaker=voice mappings")
    bridge_podcast_render.add_argument("--rate", type=int, default=0)
    bridge_podcast_render.add_argument("--ffmpeg", default="ffmpeg")
    bridge_podcast_render.add_argument("--ffprobe", default="ffprobe")
    bridge_podcast_render.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    bridge_podcast_render.add_argument("--model", default="qwen3:8b")
    bridge_podcast_render.add_argument("--provider", choices=["windows_sapi", "piper", "audio_cpp"], default="windows_sapi")
    bridge_podcast_render.add_argument("--audio-cpp-exe", default=None)
    bridge_podcast_render.add_argument("--audio-cpp-model", default=None)
    bridge_podcast_render.add_argument("--audio-cpp-backend", default="cpu")
    bridge_podcast_render.add_argument("--audio-cpp-family", default=None)
    bridge_podcast_render.add_argument("--piper-exe", default=None)
    bridge_podcast_render.add_argument("--piper-voice-dir", default=None)
    bridge_podcast_render.add_argument("--piper-model", default=None)
    bridge_podcast_render.add_argument("--script-path", type=Path, default=None)
    bridge_podcast_render.add_argument("--focus", default=None)
    bridge_podcast_render.add_argument("--style", default=None)

    bridge_podcast_interactive = bridge_sub.add_parser("podcast-interactive", help="Generate and render a non-blocking interactive podcast as JSONL")
    bridge_podcast_interactive.add_argument("book_id")
    bridge_podcast_interactive.add_argument("--library", type=Path, required=True)
    bridge_podcast_interactive.add_argument("--mode", choices=sorted(PODCAST_MODES), default="educational")
    bridge_podcast_interactive.add_argument("--format", choices=["opus", "mp3", "wav", "m4b"], default="opus")
    bridge_podcast_interactive.add_argument("--voice", action="append", default=[], help="Speaker=Voice mapping")
    bridge_podcast_interactive.add_argument("--confirm-voices", action="store_true", help="Confirm reviewed speaker=voice mappings")
    bridge_podcast_interactive.add_argument("--rate", type=int, default=0)
    bridge_podcast_interactive.add_argument("--turns", type=int, default=4)
    bridge_podcast_interactive.add_argument("--seed-prompt", default=None)
    bridge_podcast_interactive.add_argument("--ffmpeg", default="ffmpeg")
    bridge_podcast_interactive.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    bridge_podcast_interactive.add_argument("--model", default="qwen3:8b")
    bridge_podcast_interactive.add_argument("--provider", choices=["windows_sapi", "piper", "audio_cpp"], default="windows_sapi")
    bridge_podcast_interactive.add_argument("--audio-cpp-exe", default=None)
    bridge_podcast_interactive.add_argument("--audio-cpp-model", default=None)
    bridge_podcast_interactive.add_argument("--audio-cpp-backend", default="cpu")
    bridge_podcast_interactive.add_argument("--audio-cpp-family", default=None)
    bridge_podcast_interactive.add_argument("--piper-exe", default=None)
    bridge_podcast_interactive.add_argument("--piper-voice-dir", default=None)
    bridge_podcast_interactive.add_argument("--piper-model", default=None)

    bridge_import = bridge_sub.add_parser("import", help="Import a source and emit JSONL job events")
    bridge_import.add_argument("file", type=Path)
    bridge_import.add_argument("--library", type=Path, required=True)
    bridge_import.add_argument("--cleanup-profile", default="standard")

    bridge_source_probe = bridge_sub.add_parser("source-probe", help="Probe a source file or folder before import")
    bridge_source_probe.add_argument("source", type=Path)
    bridge_source_probe.add_argument("--max-chars", type=int, default=1400)

    bridge_calibre = bridge_sub.add_parser("calibre-scan", help="Scan Calibre and emit JSONL results")
    bridge_calibre.add_argument("calibre_library", type=Path)
    bridge_calibre.add_argument("--calibredb", default=None)
    bridge_calibre.add_argument("--limit", type=int, default=None)

    bridge_calibre_diagnose = bridge_sub.add_parser("calibre-diagnose", help="Diagnose a Calibre library path")
    bridge_calibre_diagnose.add_argument("calibre_library", type=Path)
    bridge_calibre_diagnose.add_argument("--calibredb", default=None)

    bridge_calibre_import = bridge_sub.add_parser("calibre-import", help="Import Calibre books and emit JSONL results")
    bridge_calibre_import.add_argument("calibre_library", type=Path)
    bridge_calibre_import.add_argument("--library", type=Path, required=True)
    bridge_calibre_import.add_argument("--calibredb", default=None)
    bridge_calibre_import.add_argument("--id", action="append", dest="ids", default=[])
    bridge_calibre_import.add_argument("--limit", type=int, default=None)
    bridge_calibre_import.add_argument("--cleanup-profile", default="standard")

    bridge_render = bridge_sub.add_parser("render", help="Render a book and emit JSONL job events")
    bridge_render.add_argument("book_id")
    bridge_render.add_argument("--library", type=Path, required=True)
    bridge_render.add_argument("--format", choices=["opus", "mp3", "wav", "m4b"], default="opus")
    bridge_render.add_argument("--voice", default=None)
    bridge_render.add_argument("--speaker-voice", action="append", default=[])
    bridge_render.add_argument("--confirm-speaker-voices", action="store_true")
    bridge_render.add_argument("--rate", type=int, default=0)
    bridge_render.add_argument("--limit", type=int, default=None)
    bridge_render.add_argument("--ffmpeg", default="ffmpeg")
    bridge_render.add_argument("--ffprobe", default="ffprobe")
    bridge_render.add_argument("--provider", choices=["windows_sapi", "piper", "audio_cpp"], default="windows_sapi")
    bridge_render.add_argument("--audio-cpp-exe", default=None)
    bridge_render.add_argument("--audio-cpp-model", default=None)
    bridge_render.add_argument("--audio-cpp-backend", default="cpu")
    bridge_render.add_argument("--audio-cpp-family", default=None)
    bridge_render.add_argument("--piper-exe", default=None)
    bridge_render.add_argument("--piper-voice-dir", default=None)
    bridge_render.add_argument("--piper-model", default=None)

    bridge_sample = bridge_sub.add_parser("sample-render", help="Render the first chunk and emit JSONL job events")
    bridge_sample.add_argument("book_id")
    bridge_sample.add_argument("--library", type=Path, required=True)
    bridge_sample.add_argument("--format", choices=["opus", "mp3", "wav", "m4b"], default="opus")
    bridge_sample.add_argument("--voice", default=None)
    bridge_sample.add_argument("--speaker-voice", action="append", default=[])
    bridge_sample.add_argument("--confirm-speaker-voices", action="store_true")
    bridge_sample.add_argument("--rate", type=int, default=0)
    bridge_sample.add_argument("--ffmpeg", default="ffmpeg")
    bridge_sample.add_argument("--ffprobe", default="ffprobe")
    bridge_sample.add_argument("--provider", choices=["windows_sapi", "piper", "audio_cpp"], default="windows_sapi")
    bridge_sample.add_argument("--audio-cpp-exe", default=None)
    bridge_sample.add_argument("--audio-cpp-model", default=None)
    bridge_sample.add_argument("--audio-cpp-backend", default="cpu")
    bridge_sample.add_argument("--audio-cpp-family", default=None)
    bridge_sample.add_argument("--piper-exe", default=None)
    bridge_sample.add_argument("--piper-voice-dir", default=None)
    bridge_sample.add_argument("--piper-model", default=None)

    args = parser.parse_args(argv)
    if args.command == "bridge":
        if args.bridge_command == "diagnose":
            return bridge.run_safely(bridge.diagnose, args.library, args.ffmpeg, args.ffprobe)
        if args.bridge_command == "voices":
            return bridge.run_safely(
                bridge.voices,
                args.provider,
                args.audio_cpp_exe,
                args.audio_cpp_model,
                args.audio_cpp_backend,
                args.audio_cpp_family,
                args.piper_exe,
                args.piper_voice_dir,
                args.piper_model,
            )
        if args.bridge_command == "tts-test":
            return bridge.run_safely(
                bridge.tts_test,
                args.library,
                args.text,
                "wav",
                args.voice,
                args.rate,
                args.provider,
                args.audio_cpp_exe,
                args.audio_cpp_model,
                args.audio_cpp_backend,
                args.audio_cpp_family,
                args.piper_exe,
                args.piper_voice_dir,
                args.piper_model,
            )
        if args.bridge_command == "audio-cpp-health":
            return bridge.run_safely(
                bridge.audio_cpp_health,
                args.audio_cpp_exe,
                args.audio_cpp_model,
                args.audio_cpp_backend,
                args.audio_cpp_family,
            )
        if args.bridge_command == "list":
            return bridge.run_safely(bridge.list_books, args.library, args.preview_first)
        if args.bridge_command == "startup-snapshot":
            return bridge.run_safely(bridge.startup_snapshot, args.library, args.book_id)
        if args.bridge_command == "outputs":
            return bridge.run_safely(bridge.outputs, args.library, args.book_id)
        if args.bridge_command == "cleanup-profiles":
            return bridge.run_safely(bridge.cleanup_profiles, args.library)
        if args.bridge_command == "set-cleanup-profile":
            return bridge.run_safely(
                bridge.set_cleanup_profile,
                args.library,
                args.book_id,
                args.cleanup_profile,
            )
        if args.bridge_command == "book-preview":
            return bridge.run_safely(bridge.book_preview, args.library, args.book_id, args.max_chars)
        if args.bridge_command == "chapter-detail":
            return bridge.run_safely(bridge.chapter_detail, args.library, args.book_id, args.chapter_index)
        if args.bridge_command == "update-chapter":
            return bridge.run_safely(
                bridge.update_chapter,
                args.library,
                args.book_id,
                args.chapter_index,
                args.title,
                args.text,
            )
        if args.bridge_command == "characters":
            return bridge.run_safely(bridge.characters, args.library, args.book_id, args.ollama_url, args.model)
        if args.bridge_command == "podcast-script":
            return bridge.run_safely(
                bridge.podcast_script,
                args.library,
                args.book_id,
                args.mode,
                args.ollama_url,
                args.model,
                args.focus,
                args.style,
            )
        if args.bridge_command == "podcast-render":
            return bridge.run_safely(
                bridge.podcast_render,
                args.library,
                args.book_id,
                args.mode,
                args.format,
                args.voice,
                args.confirm_voices,
                args.rate,
                args.ffmpeg,
                args.ffprobe,
                args.ollama_url,
                args.model,
                args.provider,
                args.audio_cpp_exe,
                args.audio_cpp_model,
                args.audio_cpp_backend,
                args.audio_cpp_family,
                args.piper_exe,
                args.piper_voice_dir,
                args.piper_model,
                args.script_path,
                args.focus,
                args.style,
            )
        if args.bridge_command == "podcast-interactive":
            return bridge.run_safely(
                bridge.podcast_interactive,
                args.library,
                args.book_id,
                args.mode,
                args.format,
                args.voice,
                args.confirm_voices,
                args.rate,
                args.turns,
                args.seed_prompt,
                args.ffmpeg,
                args.ollama_url,
                args.model,
                args.provider,
                args.audio_cpp_exe,
                args.audio_cpp_model,
                args.audio_cpp_backend,
                args.audio_cpp_family,
                args.piper_exe,
                args.piper_voice_dir,
                args.piper_model,
            )
        if args.bridge_command == "import":
            return bridge.run_safely(bridge.import_file, args.library, args.file, args.cleanup_profile)
        if args.bridge_command == "source-probe":
            return bridge.run_safely(bridge.source_probe, args.source, args.max_chars)
        if args.bridge_command == "calibre-scan":
            return bridge.run_safely(bridge.calibre_scan, args.calibre_library, args.calibredb, args.limit)
        if args.bridge_command == "calibre-diagnose":
            return bridge.run_safely(bridge.calibre_diagnose, args.calibre_library, args.calibredb)
        if args.bridge_command == "calibre-import":
            return bridge.run_safely(
                bridge.calibre_import,
                args.library,
                args.calibre_library,
                args.ids,
                args.calibredb,
                args.limit,
                args.cleanup_profile,
            )
        if args.bridge_command == "render":
            return bridge.run_safely(
                bridge.render_book,
                args.library,
                args.book_id,
                args.format,
                args.voice,
                args.speaker_voice,
                args.confirm_speaker_voices,
                args.rate,
                args.limit,
                args.ffmpeg,
                args.ffprobe,
                args.provider,
                args.audio_cpp_exe,
                args.audio_cpp_model,
                args.audio_cpp_backend,
                args.audio_cpp_family,
                args.piper_exe,
                args.piper_voice_dir,
                args.piper_model,
            )
        if args.bridge_command == "sample-render":
            return bridge.run_safely(
                bridge.sample_render,
                args.library,
                args.book_id,
                args.format,
                args.voice,
                args.speaker_voice,
                args.confirm_speaker_voices,
                args.rate,
                args.ffmpeg,
                args.ffprobe,
                args.provider,
                args.audio_cpp_exe,
                args.audio_cpp_model,
                args.audio_cpp_backend,
                args.audio_cpp_family,
                args.piper_exe,
                args.piper_voice_dir,
                args.piper_model,
            )

    if args.command == "import":
        library = BookLibrary(args.library)
        try:
            book_id = library.import_source(args.file, cleanup_profile=args.cleanup_profile)
            book = library.get_book(book_id)
        finally:
            library.close()
        print(f"Imported {book['author']} - {book['title']} ({book_id})")
        return 0

    if args.command == "list":
        library = BookLibrary(args.library)
        try:
            for book in library.list_books():
                print(
                    f"{book['id']} | {book['author']} | {book['title']} | {book['cleanup_profile']} | "
                    f"{book['chapter_count']} chapters | {book['chunk_count']} chunks | {book['status']}"
                )
        finally:
            library.close()
        return 0

    if args.command == "calibre":
        calibredb = args.calibredb or find_calibredb() or "calibredb"
        client = CalibreClient(args.calibre_library, calibredb=calibredb)
        books = client.scan(search=args.search, limit=args.limit)
        supported = [book for book in books if book.preferred_format()]

        if args.calibre_command == "scan":
            for book in supported:
                print(f"{book.id} | {book.authors} | {book.title} | {', '.join(book.formats)}")
            skipped = len(books) - len(supported)
            if skipped:
                print(f"Skipped {skipped} books without EPUB/DOCX/TXT/MD/PDF")
            return 0

        if args.calibre_command == "import":
            selected = supported
            if args.ids:
                wanted = set(args.ids)
                selected = [book for book in supported if book.id in wanted]
            library = BookLibrary(args.library)
            try:
                for book in selected:
                    book_id = library.import_calibre_book(client, book, cleanup_profile=args.cleanup_profile)
                    print(f"Imported Calibre {book.id}: {book.authors} - {book.title} ({book_id})")
            finally:
                library.close()
            return 0

    if args.command == "render":
        library = BookLibrary(args.library)
        try:
            provider = _build_tts_provider(args)
            output = library.render_book(
                args.book_id,
                output_format=args.format,
                provider=provider,
                voice=args.voice,
                voice_map=_optional_confirmed_voice_map(args.speaker_voice, args.confirm_speaker_voices),
                rate=args.rate,
                limit=args.limit,
                ffmpeg=args.ffmpeg,
                ffprobe=args.ffprobe,
            )
        finally:
            library.close()
        print(f"Rendered {output}")
        return 0

    if args.command == "characters":
        library = BookLibrary(args.library)
        try:
            text = library.get_book_text(args.book_id)
        finally:
            library.close()
        provider = OllamaProvider(model=args.model, base_url=args.ollama_url)
        if not provider.health():
            raise SystemExit(f"Ollama is not reachable at {args.ollama_url}")
        candidates = suggest_characters(text, provider)
        print(json.dumps([candidate.__dict__ for candidate in candidates], ensure_ascii=False, indent=2))
        return 0

    if args.command == "podcast":
        library = BookLibrary(args.library)
        try:
            text = library.get_book_text(args.book_id)
            provider = OllamaProvider(model=args.model, base_url=args.ollama_url)
            if not provider.health():
                raise SystemExit(f"Ollama is not reachable at {args.ollama_url}")
            if args.podcast_command == "script":
                script = generate_podcast_script(text, provider, mode=args.mode)
                output = library.save_podcast_script(args.book_id, script.to_dict())
                print(f"Wrote podcast script {output}")
                return 0
            if args.podcast_command == "render":
                script = generate_podcast_script(text, provider, mode=args.mode)
                voice_map = _confirmed_voice_map(args.voice, args.confirm_voices)
                output = library.render_podcast_script(
                    args.book_id,
                    script,
                    output_format=args.format,
                    voice_map=voice_map,
                    ffmpeg=args.ffmpeg,
                    ffprobe=args.ffprobe,
                    rate=args.rate,
                )
                print(f"Rendered podcast {output}")
                return 0
            if args.podcast_command == "interactive":
                voice_map = _confirmed_voice_map(args.voice, args.confirm_voices)
                output = _run_interactive_podcast(
                    library=library,
                    book_id=args.book_id,
                    provider=provider,
                    mode=args.mode,
                    output_format=args.format,
                    voice_map=voice_map,
                    rate=args.rate,
                    turns=args.turns,
                    playback=args.playback,
                    ffmpeg=args.ffmpeg,
                    seed_prompt=args.seed_prompt,
                )
                print(f"Rendered interactive podcast {output}")
                return 0
        finally:
            library.close()

    parser.error("unknown command")
    return 2


def _parse_voice_map(entries: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for entry in entries:
        if "=" not in entry:
            raise SystemExit(f"Invalid --voice mapping: {entry!r}; expected speaker=voice")
        speaker, voice = entry.split("=", 1)
        speaker = speaker.strip()
        voice = voice.strip()
        if not speaker or not voice:
            raise SystemExit(f"Invalid --voice mapping: {entry!r}; expected speaker=voice")
        mapping[speaker] = voice
    return mapping


def _confirmed_voice_map(entries: list[str], confirmed: bool) -> dict[str, str]:
    mapping = _parse_voice_map(entries)
    if not mapping:
        raise SystemExit("Speaker voice mapping is required before podcast rendering")
    if not confirmed:
        raise SystemExit("Confirm speaker voices before rendering: pass --confirm-voices after checking speaker=voice mappings")
    return mapping


def _optional_confirmed_voice_map(entries: list[str], confirmed: bool) -> dict[str, str]:
    mapping = _parse_voice_map(entries)
    if mapping and not confirmed:
        raise SystemExit("Confirm audiobook speaker voices before rendering: pass --confirm-speaker-voices after checking speaker=voice mappings")
    return mapping


def _build_tts_provider(args) -> WindowsSapiProvider | AudioCppProvider | PiperProvider:
    if getattr(args, "provider", "windows_sapi") == "audio_cpp":
        audio_cpp_exe = args.audio_cpp_exe or (
            str(bridge.DEFAULT_AUDIO_CPP_EXE) if bridge.DEFAULT_AUDIO_CPP_EXE.exists() else None
        )
        if not audio_cpp_exe:
            raise SystemExit("--audio-cpp-exe is required for --provider audio_cpp")
        if not args.audio_cpp_model:
            raise SystemExit("--audio-cpp-model is required for --provider audio_cpp")
        return AudioCppProvider(
            audio_cpp_exe,
            model=args.audio_cpp_model,
            backend=args.audio_cpp_backend,
            family=args.audio_cpp_family,
        )
    if getattr(args, "provider", "windows_sapi") == "piper":
        return PiperProvider(
            args.piper_exe or str(bridge.DEFAULT_PIPER_EXE),
            voice_dir=args.piper_voice_dir or str(bridge.DEFAULT_PIPER_VOICE_DIR),
            model=args.piper_model,
        )
    return WindowsSapiProvider()


def _run_interactive_podcast(
    *,
    library: BookLibrary,
    book_id: str,
    provider: OllamaProvider,
    mode: str,
    output_format: str,
    voice_map: dict[str, str],
    rate: int,
    turns: int,
    playback: bool,
    ffmpeg: str,
    seed_prompt: str | None,
) -> Path:
    book = library.get_book(book_id)
    if not book:
        raise SystemExit(f"Unknown book id: {book_id}")
    if not provider.health():
        raise SystemExit(f"Ollama is not reachable at {provider.base_url}")
    text = library.get_book_text(book_id)
    tts = WindowsSapiProvider()
    if not tts.health():
        raise SystemExit("Windows SAPI is not available")

    speaker_names = list(voice_map) or ["host"]
    library.sync_speakers(book_id, speaker_names, voice_map=voice_map, provider=tts.id)

    session_dir = library.root / "books" / book_id / "podcasts" / "interactive" / safe_name(str(book["title"]))
    session_dir.mkdir(parents=True, exist_ok=True)
    state_path = session_dir / "session.json"
    transcript: list[PodcastTurn] = []
    rendered_segments: list[Path] = []
    interruption = seed_prompt

    for turn_index in range(max(1, turns)):
        step = generate_interactive_step(text, provider, mode, transcript, interruption=interruption)
        wav_path = session_dir / f"turn_{turn_index:03d}_{safe_name(step.speaker)}.wav"
        tts.synthesize(step.text, wav_path, voice=voice_map.get(step.speaker), rate=rate)
        rendered_segments.append(wav_path)
        transcript.append(PodcastTurn(speaker=step.speaker, text=step.text))
        state_path.write_text(
            json.dumps(
                {
                    "book_id": book_id,
                    "mode": mode,
                    "turns": [turn.__dict__ for turn in transcript],
                    "follow_up": step.follow_up,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"[{turn_index + 1}] {step.speaker}: {step.text}")
        if step.follow_up:
            print(f"Follow-up: {step.follow_up}")
        if playback:
            play_wav(wav_path)

        if turn_index + 1 >= turns:
            break
        try:
            interruption = input("Interrupt / follow-up (Enter to continue, q to stop): ").strip()
        except EOFError:
            interruption = ""
        if interruption.lower() in {"q", "quit", "stop"}:
            break
        if not interruption:
            interruption = step.follow_up or None

    output_dir = session_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_name(str(book['author']))} - {safe_name(str(book['title']))}_interactive.{output_format.lower()}"
    assemble_audio(rendered_segments, output_path, output_format, ffmpeg=ffmpeg)
    library.add_output(book_id, output_format, output_path)
    return output_path
