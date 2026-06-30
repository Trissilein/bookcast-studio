use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};
use serde_json::Value;

slint::slint! {
import { Button, CheckBox, ComboBox, LineEdit, TextEdit } from "std-widgets.slint";

export component AppWindow inherits Window {
    title: "BookCast Studio";
    width: 1220px;
    height: 780px;

    in-out property <string> library-path: "library";
    in-out property <string> source-path: "";
    in-out property <string> source-probe-text: "No source probed yet. Choose a file/folder, then click Probe Source to preview before importing.";
    in-out property <string> calibre-path: "";
    in-out property <string> calibredb-path: "";
    in-out property <string> calibre-suggested-path: "";
    in-out property <string> source-suggested-path: "";
    in-out property <string> calibre-ids: "";
    in-out property <string> calibre-limit: "50";
    in-out property <string> calibre-action-text: "Select a Calibre library folder, then click Diagnose Calibre.";
    in-out property <string> calibre-preview-text: "No Calibre scan yet. Choose a Calibre library, run Diagnose Calibre, then Scan Calibre.";
    in-out property <string> book-id: "";
    in-out property <string> voice-name: "";
    in-out property <string> voice-list-text: "No voices loaded yet. Click Check Voice Engine or Discover Voices, then use First/Previous/Next Voice.";
    in-out property <string> output-format: "opus";
    in-out property <string> render-limit: "";
    in-out property <string> ffmpeg-path: "";
    in-out property <string> ffprobe-path: "";
    in-out property <string> tts-test-text: "BookCast engine test.";
    in-out property <string> last-output-path: "";
    in-out property <string> output-list-text: "No outputs yet. Render TTS Test or Render Sample, then use Open File or Open Folder.";
    in-out property <string> audio-cpp-exe: "";
    in-out property <string> audio-cpp-model: "";
    in-out property <string> audio-cpp-backend: "cpu";
    in-out property <string> audio-cpp-family: "";
    in-out property <string> audio-cpp-family-hint: "Run Check audio.cpp to list available TTS families.";
    in-out property <string> piper-exe: "";
    in-out property <string> piper-voice-dir: "";
    in-out property <int> engine-index: 0;
    in-out property <string> status-text: "Ready";
    in-out property <string> diagnostic-text: "Diagnostics not run yet. Click Run Diagnostics on Start or Import before importing/rendering.";
    in-out property <string> books-text: "No books in this BookCast library yet. Import a source file/folder or scan Calibre, then Refresh Books.";
    in-out property <string> book-selection-text: "No book selected yet. Import a source or click Refresh Books after importing.";
    in-out property <string> book-preview-text: "No preview yet. Select/import a book, then click Load Preview to inspect chapters and chunks.";
    in-out property <string> cleanup-profile-name: "standard";
    in-out property <string> cleanup-profiles-text: "Load cleanup profiles before changing chunking.";
    in-out property <string> chapter-edit-index: "0";
    in-out property <string> chapter-edit-title: "";
    in-out property <string> chapter-edit-text: "";
    in-out property <string> character-text: "No character suggestions yet. Load a book preview, start Ollama, then click Suggest Characters.";
    in-out property <string> character-review-text: "Review checklist: run suggestions, delete false positives, assign voices, then tick confirmation.";
    in-out property <string> podcast-text: "No podcast script yet. Choose a mode/preset, generate script, review voices, then render.";
    in-out property <string> podcast-review-text: "Review checklist: generate script, review speakers/turns, assign voices, tick confirmation, then render.";
    in-out property <string> podcast-script-path: "";
    in-out property <string> podcast-script-json: "";
    in-out property <string> podcast-focus: "";
    in-out property <string> podcast-style: "";
    in-out property <string> ollama-url: "http://127.0.0.1:11434";
    in-out property <string> ollama-model: "qwen3:8b";
    in-out property <string> speaker-voice-map: "host=; explainer=; skeptic=";
    in-out property <bool> speaker-voices-confirmed: false;
    in-out property <string> interactive-turns: "4";
    in-out property <string> interactive-seed-prompt: "";
    in-out property <int> podcast-mode-index: 0;
    in-out property <string> queue-text: "Queue idle. Start an import, engine check, TTS test, sample render, or full render.";
    in-out property <string> queue-summary: "No active jobs. Queue idle.";
    in-out property <string> queue-action-text: "Queue action: start an import, engine check, or render job.";
    in-out property <string> guide-text: "Next: run diagnostics, import a source or scan Calibre, then render from TTS Studio.";
    in-out property <string> setup-checklist-text: "[ ] Diagnostics\n[ ] Book selected\n[ ] Engine checked\n[ ] Sample rendered";
    in-out property <string> readiness-text: "Next: run diagnostics, import a source or scan Calibre, then render a sample.";
    in-out property <string> render-plan-text: "Render plan: choose a book, choose an engine, render a sample, then full book.";
    in-out property <string> engine-check-text: "Engine check: not run. Click Check Voice Engine before rendering.";
    in-out property <string> engine-setup-text: "Voice engine setup: choose a voice engine, then click Check Voice Engine.";
    in-out property <string> audio-cpp-status: "audio.cpp: not checked";
    in-out property <int> current-view: 6;

    callback save-settings();
    callback browse-library();
    callback browse-source-file();
    callback browse-source-folder();
    callback probe-source();
    callback browse-calibre();
    callback browse-calibredb();
    callback browse-ffmpeg();
    callback browse-ffprobe();
    callback browse-piper-exe();
    callback browse-piper-voice-dir();
    callback browse-audio-cpp-exe();
    callback browse-audio-cpp-model();
    callback diagnose();
    callback list-books();
    callback import-source();
    callback diagnose-calibre();
    callback use-suggested-calibre();
    callback use-source-suggestion();
    callback scan-calibre();
    callback import-calibre();
    callback load-preview();
    callback previous-book();
    callback next-book();
    callback load-chapter();
    callback save-chapter();
    callback load-cleanup-profiles();
    callback apply-cleanup-profile();
    callback sample-render();
    callback render-book();
    callback tts-test();
    callback check-engine();
    callback suggest-characters();
    callback podcast-script();
    callback podcast-render();
    callback podcast-interactive();
    callback use-educational-podcast-preset();
    callback use-controversial-podcast-preset();
    callback use-interview-podcast-preset();
    callback browse-podcast-script();
    callback open-podcast-script();
    callback open-podcast-script-folder();
    callback reload-podcast-script();
    callback validate-podcast-script();
    callback save-podcast-script();
    callback discover-voices();
    callback use-first-voice();
    callback use-previous-voice();
    callback use-next-voice();
    callback load-outputs();
    callback open-output();
    callback open-output-folder();
    callback refresh-audio-cpp();
    callback cancel-job();
    callback retry-job();

    Rectangle {
        background: rgb(245, 242, 234);

        HorizontalLayout {
            spacing: 0px;

            Rectangle {
                width: 220px;
                background: rgb(22, 34, 29);

                VerticalLayout {
                    padding: 18px;
                    spacing: 16px;

                    Text {
                        text: "BookCast";
                        color: rgb(248, 241, 222);
                        font-size: 28px;
                        font-weight: 800;
                    }

                    Button { text: "Start"; clicked => { root.current-view = 6; } }
                    Button { text: "TTS Studio"; clicked => { root.current-view = 0; } }
                    Button { text: "Import"; clicked => { root.current-view = 1; } }
                    Button { text: "Library"; clicked => { root.current-view = 2; } }
                    Button { text: "Characters"; clicked => { root.current-view = 3; } }
                    Button { text: "Podcast"; clicked => { root.current-view = 4; } }
                    Button { text: "Settings"; clicked => { root.current-view = 5; } }

                    Rectangle { height: 1px; background: rgb(48, 64, 57); }

                    Text {
                        text: root.audio-cpp-status;
                        color: rgb(242, 200, 121);
                        font-size: 13px;
                        wrap: word-wrap;
                    }
                }
            }

            VerticalLayout {
                padding: 18px;
                spacing: 14px;

                Rectangle {
                    height: 82px;
                    background: rgb(255, 255, 255);
                    border-color: rgb(215, 208, 191);
                    border-width: 1px;
                    border-radius: 6px;

                    HorizontalLayout {
                        padding: 14px;
                        spacing: 14px;

                        VerticalLayout {
                            spacing: 5px;
                            Text { text: "Workbench"; font-size: 24px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text { text: root.status-text; font-size: 14px; color: rgb(89, 99, 93); }
                            Text { text: root.readiness-text; font-size: 13px; color: rgb(45, 69, 58); wrap: word-wrap; }
                        }

                        Button { text: "Diagnose"; clicked => { root.diagnose(); } }
                        Button { text: "Refresh Books"; clicked => { root.list-books(); } }
                        Button { text: "Check audio.cpp"; clicked => { root.refresh-audio-cpp(); } }
                        Button { text: "Retry Last"; clicked => { root.retry-job(); } }
                        Button { text: "Cancel"; clicked => { root.cancel-job(); } }
                    }
                }

                HorizontalLayout {
                    spacing: 14px;

                    Rectangle {
                        width: 640px;
                        visible: root.current-view == 6;
                        background: rgb(255, 255, 255);
                        border-color: rgb(215, 208, 191);
                        border-width: 1px;
                        border-radius: 6px;

                        VerticalLayout {
                            padding: 20px;
                            spacing: 14px;

                            Text { text: "Start"; font-size: 24px; font-weight: 800; color: rgb(32, 36, 31); }
                            Text {
                                text: "Guided path from source file or Calibre library to first audiobook sample.";
                                color: rgb(89, 99, 93);
                                font-size: 14px;
                                wrap: word-wrap;
                            }
                            Rectangle {
                                background: rgb(250, 247, 238);
                                border-color: rgb(228, 221, 204);
                                border-width: 1px;
                                border-radius: 6px;
                                VerticalLayout {
                                    padding: 12px;
                                    spacing: 8px;
                                    Text { text: "Fast path"; font-size: 16px; font-weight: 700; color: rgb(32, 36, 31); }
                                    Text {
                                        text: "1. Run Diagnose -> 2. Open Import Wizard -> 3. Refresh Books / Load Preview -> 4. Render TTS Test -> 5. Render Sample.";
                                        color: rgb(45, 69, 58);
                                        font-size: 13px;
                                        wrap: word-wrap;
                                    }
                                    Text {
                                        text: "If a step fails, the Inspector and Queue action tell you the next fix.";
                                        color: rgb(89, 99, 93);
                                        font-size: 12px;
                                        wrap: word-wrap;
                                    }
                                }
                            }

                            Rectangle { height: 1px; background: rgb(228, 221, 204); }

                            Text { text: "1. Check setup"; font-size: 17px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text { text: "Validate Python bridge, ffmpeg, TTS fallback, and optional local engines."; color: rgb(89, 99, 93); font-size: 13px; wrap: word-wrap; }
                            HorizontalLayout {
                                spacing: 10px;
                                Button { text: "Run Diagnose"; clicked => { root.diagnose(); } }
                                Button { text: "Open Settings"; clicked => { root.current-view = 5; } }
                            }

                            Text { text: "2. Add a book"; font-size: 17px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text { text: "Import one file, one folder, or diagnose a Calibre library before scanning."; color: rgb(89, 99, 93); font-size: 13px; wrap: word-wrap; }
                            HorizontalLayout {
                                spacing: 10px;
                                Button { text: "Open Import Wizard"; clicked => { root.current-view = 1; } }
                                Button { text: "Refresh Books"; clicked => { root.list-books(); } }
                            }

                            Text { text: "3. Prepare text"; font-size: 17px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text { text: "Review chapters/chunks, change cleanup profile, and fix obvious extraction problems."; color: rgb(89, 99, 93); font-size: 13px; wrap: word-wrap; }
                            Button { text: "Open Library"; clicked => { root.current-view = 2; } }

                            Text { text: "4. Render audio"; font-size: 17px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text { text: "Pick a voice engine, check it, render a short sample, then queue the full book."; color: rgb(89, 99, 93); font-size: 13px; wrap: word-wrap; }
                            HorizontalLayout {
                                spacing: 10px;
                                Button { text: "Open TTS Studio"; clicked => { root.current-view = 0; } }
                                Button { text: "Check Voice Engine"; clicked => { root.check-engine(); } }
                            }

                            Rectangle { height: 1px; background: rgb(228, 221, 204); }
                            Text { text: "Current checklist"; font-size: 17px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text {
                                text: root.setup-checklist-text;
                                color: rgb(45, 69, 58);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                        }
                    }

                    Rectangle {
                        width: 640px;
                        visible: root.current-view == 0;
                        background: rgb(255, 255, 255);
                        border-color: rgb(215, 208, 191);
                        border-width: 1px;
                        border-radius: 6px;

                        VerticalLayout {
                            padding: 16px;
                            spacing: 10px;

                            Text { text: "TTS Studio"; font-size: 19px; font-weight: 700; color: rgb(32, 36, 31); }

                            Text { text: "Library root"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                spacing: 10px;
                                LineEdit { text <=> root.library-path; }
                                Button { text: "Browse"; clicked => { root.browse-library(); } }
                            }

                            Text { text: "Book id"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.book-id; }
                            HorizontalLayout {
                                spacing: 10px;
                                Button { text: "Previous Book"; clicked => { root.previous-book(); } }
                                Button { text: "Load Preview"; clicked => { root.load-preview(); } }
                                Button { text: "Next Book"; clicked => { root.next-book(); } }
                            }
                            Text {
                                text: root.book-selection-text;
                                color: rgb(89, 99, 93);
                                font-size: 13px;
                                wrap: word-wrap;
                            }

                            Text { text: "Voice engine"; color: rgb(89, 99, 93); }
                            ComboBox {
                                model: ["Windows voices (easy fallback)", "Piper local voices", "audio.cpp advanced voices"];
                                current-index <=> root.engine-index;
                            }
                            Text {
                                visible: root.engine-index == 0;
                                text: "Best first test. Uses installed Windows voices. No files needed.";
                                color: rgb(89, 99, 93);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Text {
                                visible: root.engine-index == 1;
                                text: "Local Piper voices. Use this when the Piper app and voice folder are configured.";
                                color: rgb(89, 99, 93);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Text {
                                visible: root.engine-index == 2;
                                text: "Advanced audio.cpp voice engine. Needs audiocpp_cli.exe, model, backend, and family.";
                                color: rgb(89, 99, 93);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Text {
                                text: root.render-plan-text;
                                color: rgb(45, 69, 58);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Text {
                                text: root.engine-check-text;
                                color: rgb(133, 82, 38);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Text {
                                text: root.engine-setup-text;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            HorizontalLayout {
                                spacing: 10px;
                                Button { text: "Check Voice Engine"; clicked => { root.check-engine(); } }
                                Button { text: "Discover Voices"; clicked => { root.discover-voices(); } }
                                Button { text: "First Voice"; clicked => { root.use-first-voice(); } }
                                Button { text: "Previous Voice"; clicked => { root.use-previous-voice(); } }
                                Button { text: "Next Voice"; clicked => { root.use-next-voice(); } }
                            }

                            HorizontalLayout {
                                spacing: 10px;
                                VerticalLayout {
                                    Text { text: "Output"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.output-format; }
                                    HorizontalLayout {
                                        spacing: 4px;
                                        Button { text: "Opus"; clicked => { root.output-format = "opus"; } }
                                        Button { text: "MP3"; clicked => { root.output-format = "mp3"; } }
                                        Button { text: "M4B"; clicked => { root.output-format = "m4b"; } }
                                        Button { text: "WAV"; clicked => { root.output-format = "wav"; } }
                                    }
                                }
                                VerticalLayout {
                                    Text { text: "Voice"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.voice-name; }
                                }
                                VerticalLayout {
                                    Text { text: "Full render chunk limit"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.render-limit; }
                                }
                            }
                            Text {
                                text: root.voice-list-text;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Text { text: "TTS test text"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.tts-test-text; }
                            Button { text: "Render TTS Test"; clicked => { root.tts-test(); } }

                            Text {
                                visible: root.engine-index == 0;
                                text: "Windows SAPI uses installed Windows voices. No engine path needed.";
                                color: rgb(89, 99, 93);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Text { visible: root.engine-index == 1; text: "Piper executable"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                visible: root.engine-index == 1;
                                spacing: 10px;
                                LineEdit { text <=> root.piper-exe; }
                                Button { text: "Browse"; clicked => { root.browse-piper-exe(); } }
                            }
                            Text { visible: root.engine-index == 1; text: "Piper voices folder"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                visible: root.engine-index == 1;
                                spacing: 10px;
                                LineEdit { text <=> root.piper-voice-dir; }
                                Button { text: "Browse"; clicked => { root.browse-piper-voice-dir(); } }
                            }
                            Text { visible: root.engine-index == 2; text: "audio.cpp executable"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                visible: root.engine-index == 2;
                                spacing: 10px;
                                LineEdit { text <=> root.audio-cpp-exe; }
                                Button { text: "Browse"; clicked => { root.browse-audio-cpp-exe(); } }
                            }
                            Text { visible: root.engine-index == 2; text: "audio.cpp model"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                visible: root.engine-index == 2;
                                spacing: 10px;
                                LineEdit { text <=> root.audio-cpp-model; }
                                Button { text: "Browse"; clicked => { root.browse-audio-cpp-model(); } }
                            }
                            HorizontalLayout {
                                visible: root.engine-index == 2;
                                spacing: 10px;
                                VerticalLayout {
                                    Text { text: "Backend"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.audio-cpp-backend; }
                                    Button { text: "Use CPU"; clicked => { root.audio-cpp-backend = "cpu"; } }
                                }
                                VerticalLayout {
                                    Text { text: "Family"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.audio-cpp-family; }
                                }
                            }
                            Text {
                                visible: root.engine-index == 2;
                                text: root.audio-cpp-family-hint;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }

                            Button { text: "Render Sample"; clicked => { root.sample-render(); } }
                            Button { text: "Add Render Job"; clicked => { root.render-book(); } }
                            Text { text: "Last Output"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.last-output-path; }
                            Button { text: "Refresh Outputs"; clicked => { root.load-outputs(); } }
                            HorizontalLayout {
                                spacing: 10px;
                                Button { text: "Open File"; clicked => { root.open-output(); } }
                                Button { text: "Open Folder"; clicked => { root.open-output-folder(); } }
                            }
                            Text {
                                text: root.output-list-text;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }

                            Text { text: "Preview"; font-size: 17px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text {
                                text: root.book-preview-text;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                        }
                    }

                    Rectangle {
                        visible: root.current-view == 1;
                        background: rgb(255, 255, 255);
                        border-color: rgb(215, 208, 191);
                        border-width: 1px;
                        border-radius: 6px;

                        VerticalLayout {
                            padding: 16px;
                            spacing: 12px;

                            Text { text: "Import Wizard"; font-size: 19px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text { text: "Step 1: import a local TXT, MD, EPUB, DOCX, or PDF file, or a folder containing them."; color: rgb(89, 99, 93); font-size: 13px; wrap: word-wrap; }
                            Text { text: "Source file or folder"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                spacing: 10px;
                                LineEdit { text <=> root.source-path; }
                                Button { text: "File"; clicked => { root.browse-source-file(); } }
                                Button { text: "Folder"; clicked => { root.browse-source-folder(); } }
                            }
                            Button { text: "Probe Source"; clicked => { root.probe-source(); } }
                            Text {
                                text: root.source-probe-text;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Text { text: "Cleanup profile for import"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                spacing: 10px;
                                LineEdit { text <=> root.cleanup-profile-name; }
                                Button { text: "Load Profiles"; clicked => { root.load-cleanup-profiles(); } }
                            }
                            Button { text: "Import Source"; clicked => { root.import-source(); } }

                            Rectangle { height: 1px; background: rgb(228, 221, 204); }

                            Text { text: "Step 2: or connect Calibre. Diagnose first, then scan, then import selected IDs."; color: rgb(89, 99, 93); font-size: 13px; wrap: word-wrap; }
                            Text { text: "Calibre library"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                spacing: 10px;
                                LineEdit { text <=> root.calibre-path; }
                                Button { text: "Browse"; clicked => { root.browse-calibre(); } }
                            }
                            Text { text: "calibredb executable (optional)"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                spacing: 10px;
                                LineEdit { text <=> root.calibredb-path; }
                                Button { text: "Browse"; clicked => { root.browse-calibredb(); } }
                            }
                            Text {
                                text: "Set this only if Calibre is installed but calibredb is not in PATH.";
                                color: rgb(70, 80, 74);
                                font-size: 12px;
                                wrap: word-wrap;
                            }
                            Button { text: "Diagnose Calibre"; clicked => { root.diagnose-calibre(); } }
                            Text {
                                text: root.calibre-action-text;
                                color: rgb(133, 82, 38);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Text {
                                visible: root.calibre-suggested-path != "";
                                text: "Suggested Calibre library: " + root.calibre-suggested-path;
                                color: rgb(45, 69, 58);
                                font-size: 12px;
                                wrap: word-wrap;
                            }
                            Text {
                                visible: root.source-suggested-path != "";
                                text: "Raw source folder: " + root.source-suggested-path;
                                color: rgb(45, 69, 58);
                                font-size: 12px;
                                wrap: word-wrap;
                            }
                            HorizontalLayout {
                                visible: root.calibre-suggested-path != "" || root.source-suggested-path != "";
                                spacing: 10px;
                                Button {
                                    visible: root.calibre-suggested-path != "";
                                    text: "Use suggested Calibre";
                                    clicked => { root.use-suggested-calibre(); }
                                }
                                Button {
                                    visible: root.source-suggested-path != "";
                                    text: "Use as Source Folder";
                                    clicked => { root.use-source-suggestion(); }
                                }
                            }
                            Button { text: "Scan Calibre"; clicked => { root.scan-calibre(); } }
                            Text { text: "Calibre IDs"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.calibre-ids; }
                            Text { text: "Calibre scan/import limit"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.calibre-limit; }
                            Button { text: "Import Calibre IDs"; clicked => { root.import-calibre(); } }
                            Text {
                                text: root.calibre-preview-text;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }

                            Rectangle { height: 1px; background: rgb(228, 221, 204); }

                            Text { text: "Guidance"; font-size: 17px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text {
                                text: root.guide-text;
                                color: rgb(70, 80, 74);
                                font-size: 14px;
                                wrap: word-wrap;
                            }

                            Text { text: "Diagnostics"; font-size: 17px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text {
                                text: root.diagnostic-text;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }

                            Text { text: "Books"; font-size: 17px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text {
                                text: root.books-text;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                        }
                    }

                    Rectangle {
                        visible: root.current-view == 2;
                        background: rgb(255, 255, 255);
                        border-color: rgb(215, 208, 191);
                        border-width: 1px;
                        border-radius: 6px;

                        VerticalLayout {
                            padding: 16px;
                            spacing: 12px;

                            Text { text: "Library"; font-size: 19px; font-weight: 700; color: rgb(32, 36, 31); }
                            Button { text: "Refresh Books"; clicked => { root.list-books(); } }
                            Text {
                                text: root.books-text;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Text { text: "Book id"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.book-id; }
                            HorizontalLayout {
                                spacing: 10px;
                                Button { text: "Previous Book"; clicked => { root.previous-book(); } }
                                Button { text: "Load Preview"; clicked => { root.load-preview(); } }
                                Button { text: "Next Book"; clicked => { root.next-book(); } }
                            }
                            Text {
                                text: root.book-selection-text;
                                color: rgb(89, 99, 93);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Text { text: "Cleanup profile"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.cleanup-profile-name; }
                            HorizontalLayout {
                                spacing: 10px;
                                Button { text: "Load Cleanup Profiles"; clicked => { root.load-cleanup-profiles(); } }
                                Button { text: "Apply + Rechunk"; clicked => { root.apply-cleanup-profile(); } }
                            }
                            Text {
                                text: root.cleanup-profiles-text;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Text {
                                text: root.book-preview-text;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Rectangle { height: 1px; background: rgb(228, 221, 204); }
                            Text { text: "Chapter Editor"; font-size: 17px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text {
                                text: "Load one chapter from the selected book, edit title/text, then Save + Rechunk before rendering.";
                                color: rgb(89, 99, 93);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            HorizontalLayout {
                                spacing: 10px;
                                VerticalLayout {
                                    Text { text: "Chapter index"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.chapter-edit-index; }
                                }
                                VerticalLayout {
                                    Text { text: "Chapter title"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.chapter-edit-title; }
                                }
                            }
                            HorizontalLayout {
                                spacing: 10px;
                                Button { text: "Load Chapter"; clicked => { root.load-chapter(); } }
                                Button { text: "Save + Rechunk"; clicked => { root.save-chapter(); } }
                            }
                            TextEdit {
                                height: 130px;
                                text <=> root.chapter-edit-text;
                            }
                            Text { text: "Last Output"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.last-output-path; }
                            Button { text: "Refresh Outputs"; clicked => { root.load-outputs(); } }
                            HorizontalLayout {
                                spacing: 10px;
                                Button { text: "Open File"; clicked => { root.open-output(); } }
                                Button { text: "Open Folder"; clicked => { root.open-output-folder(); } }
                            }
                            Text {
                                text: root.output-list-text;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                        }
                    }

                    Rectangle {
                        visible: root.current-view == 3;
                        background: rgb(255, 255, 255);
                        border-color: rgb(215, 208, 191);
                        border-width: 1px;
                        border-radius: 6px;

                        VerticalLayout {
                            padding: 16px;
                            spacing: 12px;

                            Text { text: "Characters"; font-size: 19px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text { text: "Book id"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.book-id; }
                            HorizontalLayout {
                                spacing: 10px;
                                VerticalLayout {
                                    Text { text: "Ollama URL"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.ollama-url; }
                                }
                                VerticalLayout {
                                    Text { text: "Model"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.ollama-model; }
                                }
                            }
                            Button { text: "Suggest Characters"; clicked => { root.suggest-characters(); } }
                            Text {
                                text: root.character-text;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Rectangle { height: 1px; background: rgb(228, 221, 204); }
                            Text { text: "Speaker voice map"; font-size: 17px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text { text: "Edit generated names into speaker=voice pairs. Example: Narrator=Microsoft Hedda; Ada=de_DE-thorsten-medium.onnx"; color: rgb(89, 99, 93); font-size: 13px; wrap: word-wrap; }
                            LineEdit { text <=> root.speaker-voice-map; }
                            CheckBox {
                                text: "I reviewed every character/speaker voice assignment";
                                checked <=> root.speaker-voices-confirmed;
                            }
                            Text {
                                text: root.character-review-text;
                                color: rgb(133, 82, 38);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                        }
                    }

                    Rectangle {
                        visible: root.current-view == 4;
                        background: rgb(255, 255, 255);
                        border-color: rgb(215, 208, 191);
                        border-width: 1px;
                        border-radius: 6px;

                        VerticalLayout {
                            padding: 16px;
                            spacing: 12px;

                            Text { text: "Podcast Studio"; font-size: 19px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text { text: "Book id"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.book-id; }
                            Text { text: "Mode"; color: rgb(89, 99, 93); }
                            ComboBox {
                                model: ["educational", "controversial", "interview"];
                                current-index <=> root.podcast-mode-index;
                            }
                            HorizontalLayout {
                                spacing: 10px;
                                Button { text: "Educational preset"; clicked => { root.use-educational-podcast-preset(); } }
                                Button { text: "Controversial preset"; clicked => { root.use-controversial-podcast-preset(); } }
                                Button { text: "Interview preset"; clicked => { root.use-interview-podcast-preset(); } }
                            }
                            HorizontalLayout {
                                spacing: 10px;
                                VerticalLayout {
                                    Text { text: "Ollama URL"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.ollama-url; }
                                }
                                VerticalLayout {
                                    Text { text: "Model"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.ollama-model; }
                                }
                            }
                            HorizontalLayout {
                                spacing: 10px;
                                VerticalLayout {
                                    Text { text: "Podcast focus"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.podcast-focus; }
                                }
                                VerticalLayout {
                                    Text { text: "Podcast style"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.podcast-style; }
                                }
                            }
                            Text { text: "Speaker voices: speaker=voice, separated by semicolon or comma"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.speaker-voice-map; }
                            CheckBox {
                                text: "I reviewed every speaker=voice assignment";
                                checked <=> root.speaker-voices-confirmed;
                            }
                            Text {
                                text: root.podcast-review-text;
                                color: rgb(133, 82, 38);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Text { text: "Reviewed script path"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.podcast-script-path; }
                            HorizontalLayout {
                                spacing: 10px;
                                Button { text: "Browse Script"; clicked => { root.browse-podcast-script(); } }
                                Button { text: "Reload Script"; clicked => { root.reload-podcast-script(); } }
                                Button { text: "Validate Editor"; clicked => { root.validate-podcast-script(); } }
                                Button { text: "Save Script"; clicked => { root.save-podcast-script(); } }
                                Button { text: "Open Script"; clicked => { root.open-podcast-script(); } }
                                Button { text: "Open Folder"; clicked => { root.open-podcast-script-folder(); } }
                            }
                            Text { text: "Reviewed script JSON"; color: rgb(89, 99, 93); }
                            TextEdit {
                                height: 170px;
                                text <=> root.podcast-script-json;
                            }
                            HorizontalLayout {
                                spacing: 10px;
                                VerticalLayout {
                                    Text { text: "Interactive turns"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.interactive-turns; }
                                }
                                VerticalLayout {
                                    Text { text: "Seed prompt / first interruption"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.interactive-seed-prompt; }
                                }
                            }
                            HorizontalLayout {
                                spacing: 10px;
                                Button { text: "Generate Script"; clicked => { root.podcast-script(); } }
                                Button { text: "Render Podcast"; clicked => { root.podcast-render(); } }
                                Button { text: "Render Interactive"; clicked => { root.podcast-interactive(); } }
                            }
                            Text {
                                text: root.podcast-text;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Text { text: "Last Output"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.last-output-path; }
                            Button { text: "Refresh Outputs"; clicked => { root.load-outputs(); } }
                            HorizontalLayout {
                                spacing: 10px;
                                Button { text: "Open File"; clicked => { root.open-output(); } }
                                Button { text: "Open Folder"; clicked => { root.open-output-folder(); } }
                            }
                            Text {
                                text: root.output-list-text;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                        }
                    }

                    Rectangle {
                        visible: root.current-view == 5;
                        background: rgb(255, 255, 255);
                        border-color: rgb(215, 208, 191);
                        border-width: 1px;
                        border-radius: 6px;

                        VerticalLayout {
                            padding: 16px;
                            spacing: 12px;

                            Text { text: "Settings"; font-size: 19px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text {
                                text: "Save paths and defaults here. Engine-specific fields stay available in TTS Studio for day-to-day rendering.";
                                color: rgb(89, 99, 93);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Rectangle { height: 1px; background: rgb(228, 221, 204); }
                            Text { text: "Library and render defaults"; font-size: 16px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text { text: "Library root"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                spacing: 10px;
                                LineEdit { text <=> root.library-path; }
                                Button { text: "Browse"; clicked => { root.browse-library(); } }
                            }
                            Text { text: "Default output format"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.output-format; }
                            HorizontalLayout {
                                spacing: 4px;
                                Button { text: "Opus"; clicked => { root.output-format = "opus"; } }
                                Button { text: "MP3"; clicked => { root.output-format = "mp3"; } }
                                Button { text: "M4B"; clicked => { root.output-format = "m4b"; } }
                                Button { text: "WAV"; clicked => { root.output-format = "wav"; } }
                            }
                            Text { text: "Full render chunk limit (empty = all)"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.render-limit; }
                            Text { text: "Default voice"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.voice-name; }

                            Rectangle { height: 1px; background: rgb(228, 221, 204); }
                            Text { text: "Media tools"; font-size: 16px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text {
                                text: "Leave empty when tools are in PATH. Set full paths only when BookCast cannot find them.";
                                color: rgb(89, 99, 93);
                                font-size: 12px;
                                wrap: word-wrap;
                            }
                            Text { text: "ffmpeg executable (optional)"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                spacing: 10px;
                                LineEdit { text <=> root.ffmpeg-path; }
                                Button { text: "Browse"; clicked => { root.browse-ffmpeg(); } }
                            }
                            Text { text: "ffprobe executable (optional, needed for M4B chapters)"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                spacing: 10px;
                                LineEdit { text <=> root.ffprobe-path; }
                                Button { text: "Browse"; clicked => { root.browse-ffprobe(); } }
                            }
                            Text { text: "calibredb executable (optional)"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                spacing: 10px;
                                LineEdit { text <=> root.calibredb-path; }
                                Button { text: "Browse"; clicked => { root.browse-calibredb(); } }
                            }

                            Rectangle { height: 1px; background: rgb(228, 221, 204); }
                            Text { text: "Voice engines"; font-size: 16px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text {
                                text: "Windows voices need no setup. Piper and audio.cpp are optional local engines.";
                                color: rgb(89, 99, 93);
                                font-size: 12px;
                                wrap: word-wrap;
                            }
                            Text { text: "audio.cpp executable"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                spacing: 10px;
                                LineEdit { text <=> root.audio-cpp-exe; }
                                Button { text: "Browse"; clicked => { root.browse-audio-cpp-exe(); } }
                            }
                            Text { text: "Piper executable"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                spacing: 10px;
                                LineEdit { text <=> root.piper-exe; }
                                Button { text: "Browse"; clicked => { root.browse-piper-exe(); } }
                            }
                            Text { text: "Piper voices folder"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                spacing: 10px;
                                LineEdit { text <=> root.piper-voice-dir; }
                                Button { text: "Browse"; clicked => { root.browse-piper-voice-dir(); } }
                            }
                            Text { text: "audio.cpp model"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                spacing: 10px;
                                LineEdit { text <=> root.audio-cpp-model; }
                                Button { text: "Browse"; clicked => { root.browse-audio-cpp-model(); } }
                            }
                            Text { text: "audio.cpp backend"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.audio-cpp-backend; }
                            Button { text: "Use CPU backend"; clicked => { root.audio-cpp-backend = "cpu"; } }
                            Text { text: "audio.cpp family"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.audio-cpp-family; }
                            Text {
                                text: root.audio-cpp-family-hint;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }

                            Rectangle { height: 1px; background: rgb(228, 221, 204); }
                            Text { text: "AI / Ollama"; font-size: 16px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text {
                                text: "Used for character suggestions and podcast scripts. Leave default if Ollama runs locally.";
                                color: rgb(89, 99, 93);
                                font-size: 12px;
                                wrap: word-wrap;
                            }
                            Text { text: "Ollama URL"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.ollama-url; }
                            Text { text: "Ollama model"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.ollama-model; }
                            Rectangle { height: 1px; background: rgb(228, 221, 204); }
                            Button { text: "Save Settings"; clicked => { root.save-settings(); } }
                        }
                    }

                    Rectangle {
                        width: 280px;
                        background: rgb(250, 247, 238);
                        border-color: rgb(215, 208, 191);
                        border-width: 1px;
                        border-radius: 6px;

                        VerticalLayout {
                            padding: 16px;
                            spacing: 12px;

                            Text { text: "Inspector"; font-size: 18px; font-weight: 700; color: rgb(32, 36, 31); }
                            Text { text: "Next step"; color: rgb(89, 99, 93); font-size: 13px; }
                            Text {
                                text: root.readiness-text;
                                color: rgb(45, 69, 58);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Rectangle { height: 1px; background: rgb(228, 221, 204); }
                            Text { text: "Setup checklist"; color: rgb(89, 99, 93); font-size: 13px; }
                            Text {
                                text: root.setup-checklist-text;
                                color: rgb(32, 36, 31);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Text { text: "Engine setup"; color: rgb(89, 99, 93); font-size: 13px; }
                            Text {
                                text: root.engine-setup-text;
                                color: rgb(32, 36, 31);
                                font-size: 12px;
                                wrap: word-wrap;
                            }
                            Rectangle { height: 1px; background: rgb(228, 221, 204); }
                            Text { text: "Guidance"; color: rgb(89, 99, 93); font-size: 13px; }
                            Text {
                                text: root.guide-text;
                                color: rgb(70, 80, 74);
                                font-size: 13px;
                                wrap: word-wrap;
                            }
                            Rectangle { height: 1px; background: rgb(228, 221, 204); }
                            Text { text: "Diagnostics"; color: rgb(89, 99, 93); font-size: 13px; }
                            Text {
                                text: root.diagnostic-text;
                                color: rgb(70, 80, 74);
                                font-size: 12px;
                                wrap: word-wrap;
                            }
                        }
                    }
                }

                Rectangle {
                    height: 210px;
                    background: rgb(17, 23, 19);
                    border-radius: 6px;

                    VerticalLayout {
                        padding: 14px;
                        spacing: 8px;
                        Text { text: "Queue"; color: rgb(248, 241, 222); font-size: 18px; font-weight: 700; }
                        Text { text: root.queue-summary; color: rgb(242, 200, 121); font-size: 13px; wrap: word-wrap; }
                        Text { text: root.queue-action-text; color: rgb(248, 241, 222); font-size: 13px; wrap: word-wrap; }
                        HorizontalLayout {
                            spacing: 8px;
                            Button { text: "Retry Last"; clicked => { root.retry-job(); } }
                            Button { text: "Cancel"; clicked => { root.cancel-job(); } }
                        }
                        Text {
                            text: root.queue-text;
                            color: rgb(203, 216, 207);
                            font-size: 13px;
                            wrap: word-wrap;
                        }
                    }
                }
            }
        }
    }
}
}

const AUDIO_CPP_REMOTE: &str = "https://github.com/0xShug0/audio.cpp";
const AUDIO_CPP_PINNED: &str = include_str!("../audio_cpp.lock");
const DEFAULT_PIPER_EXE: &str = r"D:\GIT\Trispr_Flow\src-tauri\bin\piper\piper.exe";
const DEFAULT_PIPER_VOICE_DIR: &str = r"D:\GIT\Trispr_Flow\src-tauri\bin\piper\voices";
const DEFAULT_AUDIO_CPP_EXE: &str =
    r"D:\GIT\audio.cpp\build\windows-cpu-release\bin\audiocpp_cli.exe";

#[derive(Clone)]
struct AppState {
    repo_root: PathBuf,
    active_pid: Arc<Mutex<Option<u32>>>,
    last_bridge_job: Arc<Mutex<Option<BridgeJobRequest>>>,
    jobs: Arc<Mutex<Vec<JobState>>>,
    book_ids: Arc<Mutex<Vec<String>>>,
    book_index: Arc<Mutex<usize>>,
}

#[derive(Clone)]
struct BridgeJobRequest {
    label: &'static str,
    args: Vec<String>,
}

#[derive(Clone)]
struct JobState {
    id: u64,
    label: String,
    status: String,
    progress: u8,
    detail: String,
    started_ms: u64,
    updated_ms: u64,
}

#[derive(Default, Serialize, Deserialize)]
#[serde(default)]
struct WorkbenchSettings {
    library_path: String,
    source_path: String,
    calibre_path: String,
    calibredb_path: String,
    calibre_ids: String,
    calibre_limit: String,
    book_id: String,
    voice_name: String,
    output_format: String,
    render_limit: String,
    ffmpeg_path: String,
    ffprobe_path: String,
    tts_test_text: String,
    last_output_path: String,
    audio_cpp_exe: String,
    audio_cpp_model: String,
    audio_cpp_backend: String,
    audio_cpp_family: String,
    piper_exe: String,
    piper_voice_dir: String,
    ollama_url: String,
    ollama_model: String,
    speaker_voice_map: String,
    interactive_turns: String,
    interactive_seed_prompt: String,
    podcast_script_path: String,
    podcast_focus: String,
    podcast_style: String,
    podcast_mode_index: i32,
    engine_index: i32,
    current_view: i32,
}

fn main() -> Result<(), slint::PlatformError> {
    let app = AppWindow::new()?;
    let state = AppState {
        repo_root: find_repo_root(),
        active_pid: Arc::new(Mutex::new(None)),
        last_bridge_job: Arc::new(Mutex::new(None)),
        jobs: Arc::new(Mutex::new(Vec::new())),
        book_ids: Arc::new(Mutex::new(Vec::new())),
        book_index: Arc::new(Mutex::new(0)),
    };

    app.set_library_path("library".into());
    if Path::new(DEFAULT_PIPER_EXE).exists() {
        app.set_piper_exe(DEFAULT_PIPER_EXE.into());
    }
    if Path::new(DEFAULT_PIPER_VOICE_DIR).exists() {
        app.set_piper_voice_dir(DEFAULT_PIPER_VOICE_DIR.into());
    }
    if Path::new(DEFAULT_AUDIO_CPP_EXE).exists() {
        app.set_audio_cpp_exe(DEFAULT_AUDIO_CPP_EXE.into());
    }
    app.set_guide_text("Run Diagnose. If ffmpeg and TTS are ready, import a file or scan Calibre. Render jobs go through the queue and can be cancelled.".into());
    load_settings(&app, &state.repo_root);
    refresh_readiness(app.as_weak());

    wire_callbacks(&app, state.clone());
    schedule_startup_snapshot(app.as_weak(), state.clone());
    schedule_startup_audio_cpp_check(app.as_weak(), state.repo_root.clone());
    app.run()
}

fn schedule_startup_snapshot(weak: slint::Weak<AppWindow>, state: AppState) {
    slint::Timer::single_shot(Duration::from_millis(300), move || {
        let Some(app) = weak.upgrade() else { return };
        let library = app.get_library_path().to_string();
        if library.trim().is_empty() {
            return;
        }
        app.set_status_text("Loading saved library snapshot...".into());
        run_bridge(
            app.as_weak(),
            state,
            "startup snapshot",
            startup_snapshot_args(&app),
        );
    });
}

fn schedule_startup_audio_cpp_check(weak: slint::Weak<AppWindow>, repo_root: PathBuf) {
    slint::Timer::single_shot(Duration::from_millis(900), move || {
        refresh_audio_cpp(weak, repo_root, false);
    });
}

fn wire_callbacks(app: &AppWindow, state: AppState) {
    let weak = app.as_weak();
    let settings_state = state.clone();
    app.on_save_settings(move || {
        let Some(app) = weak.upgrade() else { return };
        match save_settings(&app, &settings_state.repo_root) {
            Ok(path) => app.set_status_text(format!("Settings saved: {}", path.display()).into()),
            Err(error) => app.set_status_text(format!("Settings save failed: {error}").into()),
        }
    });

    let weak = app.as_weak();
    app.on_browse_library(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(path) = choose_folder("Choose BookCast library folder") {
            app.set_library_path(path_to_string(&path).into());
            app.set_status_text(format!("Library path selected: {}", path.display()).into());
        }
    });

    let weak = app.as_weak();
    app.on_browse_source_file(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(path) = choose_file(
            "Choose book source",
            &[("Books", &["txt", "md", "epub", "docx", "pdf"])],
        ) {
            app.set_source_path(path_to_string(&path).into());
            app.set_guide_text("Source file selected. Click Import Source next.".into());
        }
    });

    let weak = app.as_weak();
    app.on_browse_source_folder(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(path) = choose_folder("Choose folder with book sources") {
            app.set_source_path(path_to_string(&path).into());
            app.set_guide_text(
                "Source folder selected. Import will recursively use supported files.".into(),
            );
        }
    });

    let weak = app.as_weak();
    app.on_browse_calibre(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(path) = choose_folder("Choose Calibre library root") {
            app.set_calibre_path(path_to_string(&path).into());
            app.set_calibre_suggested_path("".into());
            app.set_source_suggested_path("".into());
            app.set_calibre_action_text(
                "Selected folder. Click Diagnose Calibre before scanning.".into(),
            );
            app.set_guide_text("Calibre folder selected. Click Diagnose Calibre next.".into());
        }
    });

    let weak = app.as_weak();
    app.on_browse_calibredb(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(path) = choose_file("Choose calibredb executable", &[("Executable", &["exe"])])
        {
            app.set_calibredb_path(path_to_string(&path).into());
            app.set_status_text("calibredb executable selected.".into());
            app.set_calibre_action_text("Click Diagnose Calibre again.".into());
            app.set_guide_text("calibredb path selected. Diagnose Calibre can now use it.".into());
        }
    });

    let weak = app.as_weak();
    app.on_browse_ffmpeg(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(path) = choose_file("Choose ffmpeg executable", &[("Executable", &["exe"])]) {
            app.set_ffmpeg_path(path_to_string(&path).into());
            app.set_status_text("ffmpeg executable selected.".into());
            app.set_guide_text("ffmpeg path selected. Save Settings, then render again.".into());
        }
    });

    let weak = app.as_weak();
    app.on_browse_ffprobe(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(path) = choose_file("Choose ffprobe executable", &[("Executable", &["exe"])]) {
            app.set_ffprobe_path(path_to_string(&path).into());
            app.set_status_text("ffprobe executable selected.".into());
            app.set_guide_text(
                "ffprobe path selected. Save Settings, then render M4B again.".into(),
            );
        }
    });

    let weak = app.as_weak();
    app.on_use_suggested_calibre(move || {
        let Some(app) = weak.upgrade() else { return };
        let suggested = app.get_calibre_suggested_path().to_string();
        if suggested.trim().is_empty() {
            app.set_status_text(
                "No Calibre suggestion available. Run Diagnose Calibre first.".into(),
            );
            return;
        }
        app.set_calibre_path(suggested.into());
        app.set_calibre_suggested_path("".into());
        app.set_source_suggested_path("".into());
        app.set_calibre_action_text(
            "Suggested library applied. Click Diagnose Calibre again, then Scan Calibre.".into(),
        );
        app.set_guide_text(
            "Suggested Calibre library applied. Click Diagnose Calibre again, then Scan Calibre."
                .into(),
        );
    });

    let weak = app.as_weak();
    app.on_use_source_suggestion(move || {
        let Some(app) = weak.upgrade() else { return };
        let suggested = app.get_source_suggested_path().to_string();
        if suggested.trim().is_empty() {
            app.set_status_text(
                "No source-folder suggestion available. Run Diagnose Calibre first.".into(),
            );
            return;
        }
        app.set_source_path(suggested.into());
        app.set_calibre_suggested_path("".into());
        app.set_source_suggested_path("".into());
        app.set_calibre_action_text(
            "Raw source folder applied. Use Probe Source, then Import Source.".into(),
        );
        app.set_guide_text(
            "Folder moved to Source import. Click Probe Source, then Import Source.".into(),
        );
    });

    let weak = app.as_weak();
    app.on_browse_piper_exe(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(path) = choose_file("Choose piper executable", &[("Executable", &["exe"])]) {
            app.set_piper_exe(path_to_string(&path).into());
            app.set_engine_setup_text(engine_setup_text(&app).into());
            app.set_status_text("Piper executable selected.".into());
        }
    });

    let weak = app.as_weak();
    app.on_browse_piper_voice_dir(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(path) = choose_folder("Choose Piper voices folder") {
            app.set_piper_voice_dir(path_to_string(&path).into());
            app.set_engine_setup_text(engine_setup_text(&app).into());
            app.set_status_text("Piper voices folder selected.".into());
        }
    });

    let weak = app.as_weak();
    app.on_browse_audio_cpp_exe(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(path) = choose_file("Choose audio.cpp executable", &[("Executable", &["exe"])])
        {
            app.set_audio_cpp_exe(path_to_string(&path).into());
            app.set_engine_setup_text(engine_setup_text(&app).into());
            app.set_status_text("audio.cpp executable selected.".into());
        }
    });

    let weak = app.as_weak();
    app.on_browse_audio_cpp_model(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(path) = choose_file(
            "Choose audio.cpp model",
            &[("Models", &["gguf", "bin", "onnx"])],
        ) {
            app.set_audio_cpp_model(path_to_string(&path).into());
            app.set_engine_setup_text(engine_setup_text(&app).into());
            app.set_guide_text("audio.cpp model selected. Click Check audio.cpp next.".into());
        }
    });

    let weak = app.as_weak();
    let diagnose_state = state.clone();
    app.on_diagnose(move || {
        let Some(app) = weak.upgrade() else { return };
        let library = app.get_library_path().to_string();
        if let Some(problem) = media_tool_path_problem(&app) {
            app.set_status_text(problem.clone().into());
            app.set_guide_text(problem.into());
            return;
        }
        let mut args = vec![
            "bridge".into(),
            "diagnose".into(),
            "--library".into(),
            library,
        ];
        args.extend(media_tool_args(&app, true));
        run_bridge(app.as_weak(), diagnose_state.clone(), "diagnose", args);
    });

    let weak = app.as_weak();
    let list_state = state.clone();
    app.on_list_books(move || {
        let Some(app) = weak.upgrade() else { return };
        let library = app.get_library_path().to_string();
        run_bridge(
            app.as_weak(),
            list_state.clone(),
            "list",
            vec![
                "bridge".into(),
                "list".into(),
                "--library".into(),
                library,
                "--preview-first".into(),
            ],
        );
    });

    let weak = app.as_weak();
    let source_probe_state = state.clone();
    app.on_probe_source(move || {
        let Some(app) = weak.upgrade() else { return };
        let source = app.get_source_path().to_string();
        if source.trim().is_empty() {
            app.set_status_text("Source probe needs a source path.".into());
            return;
        }
        run_bridge(
            app.as_weak(),
            source_probe_state.clone(),
            "source probe",
            vec!["bridge".into(), "source-probe".into(), source],
        );
    });

    let weak = app.as_weak();
    let import_state = state.clone();
    app.on_import_source(move || {
        let Some(app) = weak.upgrade() else { return };
        let library = app.get_library_path().to_string();
        let source = app.get_source_path().to_string();
        if source.trim().is_empty() {
            app.set_status_text("Import needs a source path.".into());
            return;
        }
        let mut args = vec![
            "bridge".into(),
            "import".into(),
            source,
            "--library".into(),
            library,
        ];
        let profile = app.get_cleanup_profile_name().to_string();
        if !profile.trim().is_empty() {
            args.extend(["--cleanup-profile".into(), profile]);
        }
        run_bridge(app.as_weak(), import_state.clone(), "import", args);
    });

    let weak = app.as_weak();
    let calibre_diagnose_state = state.clone();
    app.on_diagnose_calibre(move || {
        let Some(app) = weak.upgrade() else { return };
        let calibre = app.get_calibre_path().to_string();
        if calibre.trim().is_empty() {
            app.set_status_text("Calibre diagnose needs a library path.".into());
            app.set_calibre_action_text(
                "Select the folder that contains Calibre metadata.db, then Diagnose Calibre."
                    .into(),
            );
            return;
        }
        if let Some(problem) = calibredb_path_problem(&app) {
            app.set_status_text(problem.clone().into());
            app.set_calibre_action_text(problem.clone().into());
            app.set_guide_text(problem.into());
            return;
        }
        let mut args = vec!["bridge".into(), "calibre-diagnose".into(), calibre];
        append_calibredb_args(&mut args, &app);
        run_bridge(
            app.as_weak(),
            calibre_diagnose_state.clone(),
            "calibre diagnose",
            args,
        );
    });

    let weak = app.as_weak();
    let calibre_state = state.clone();
    app.on_scan_calibre(move || {
        let Some(app) = weak.upgrade() else { return };
        let calibre = app.get_calibre_path().to_string();
        if calibre.trim().is_empty() {
            app.set_status_text("Calibre scan needs a library path.".into());
            app.set_calibre_action_text(
                "Select and diagnose a Calibre library before scanning.".into(),
            );
            return;
        }
        if let Some(problem) =
            optional_positive_limit_problem(&app.get_calibre_limit().to_string(), "Calibre limit")
        {
            app.set_status_text(problem.into());
            return;
        }
        if let Some(problem) = calibredb_path_problem(&app) {
            app.set_status_text(problem.clone().into());
            app.set_calibre_action_text(problem.clone().into());
            app.set_guide_text(problem.into());
            return;
        }
        let mut args = vec!["bridge".into(), "calibre-scan".into(), calibre];
        append_calibredb_args(&mut args, &app);
        append_calibre_limit_args(&mut args, &app);
        run_bridge(app.as_weak(), calibre_state.clone(), "calibre scan", args);
    });

    let weak = app.as_weak();
    let calibre_import_state = state.clone();
    app.on_import_calibre(move || {
        let Some(app) = weak.upgrade() else { return };
        let calibre = app.get_calibre_path().to_string();
        if calibre.trim().is_empty() {
            app.set_status_text("Calibre import needs a library path.".into());
            app.set_calibre_action_text(
                "Select, diagnose, and scan a Calibre library before importing.".into(),
            );
            return;
        }
        if let Some(problem) =
            optional_positive_limit_problem(&app.get_calibre_limit().to_string(), "Calibre limit")
        {
            app.set_status_text(problem.into());
            return;
        }
        if let Some(problem) = calibredb_path_problem(&app) {
            app.set_status_text(problem.clone().into());
            app.set_calibre_action_text(problem.clone().into());
            app.set_guide_text(problem.into());
            return;
        }
        let ids = split_ids(&app.get_calibre_ids().to_string());
        if ids.is_empty() {
            app.set_status_text("Calibre import needs IDs. Run Scan Calibre, then remove IDs you do not want.".into());
            app.set_guide_text("Scan Calibre fills Calibre IDs with the visible importable books. Edit that field, then import.".into());
            app.set_calibre_action_text(
                "Run Scan Calibre first. It fills IDs for visible importable books.".into(),
            );
            return;
        }
        let mut args = vec![
            "bridge".into(),
            "calibre-import".into(),
            calibre,
            "--library".into(),
            app.get_library_path().to_string(),
        ];
        for id in ids {
            args.extend(["--id".into(), id]);
        }
        let profile = app.get_cleanup_profile_name().to_string();
        if !profile.trim().is_empty() {
            args.extend(["--cleanup-profile".into(), profile]);
        }
        append_calibredb_args(&mut args, &app);
        append_calibre_limit_args(&mut args, &app);
        run_bridge(
            app.as_weak(),
            calibre_import_state.clone(),
            "calibre import",
            args,
        );
    });

    let weak = app.as_weak();
    let engine_check_state = state.clone();
    app.on_check_engine(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(problem) = engine_check_problem(&app) {
            app.set_status_text(problem.clone().into());
            app.set_engine_check_text(problem.clone().into());
            app.set_engine_setup_text(engine_setup_text(&app).into());
            app.set_guide_text(problem.into());
            return;
        }
        if app.get_engine_index() == 2 {
            run_bridge(
                app.as_weak(),
                engine_check_state.clone(),
                "audio.cpp health",
                audio_cpp_health_args(&app),
            );
        } else {
            run_bridge(
                app.as_weak(),
                engine_check_state.clone(),
                "engine check",
                voice_args(&app),
            );
        }
    });

    let weak = app.as_weak();
    let voice_state = state.clone();
    app.on_discover_voices(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(problem) = engine_check_problem(&app) {
            app.set_status_text(problem.clone().into());
            app.set_engine_check_text(problem.clone().into());
            app.set_engine_setup_text(engine_setup_text(&app).into());
            app.set_guide_text(problem.into());
            return;
        }
        run_bridge(
            app.as_weak(),
            voice_state.clone(),
            "voices",
            voice_args(&app),
        );
    });

    let weak = app.as_weak();
    app.on_use_first_voice(move || {
        let Some(app) = weak.upgrade() else { return };
        apply_voice_choice(&app, VoiceChoice::First);
    });

    let weak = app.as_weak();
    app.on_use_previous_voice(move || {
        let Some(app) = weak.upgrade() else { return };
        apply_voice_choice(&app, VoiceChoice::Previous);
    });

    let weak = app.as_weak();
    app.on_use_next_voice(move || {
        let Some(app) = weak.upgrade() else { return };
        apply_voice_choice(&app, VoiceChoice::Next);
    });

    let weak = app.as_weak();
    let outputs_state = state.clone();
    app.on_load_outputs(move || {
        let Some(app) = weak.upgrade() else { return };
        run_bridge(
            app.as_weak(),
            outputs_state.clone(),
            "outputs",
            outputs_args(&app),
        );
    });

    let weak = app.as_weak();
    let cleanup_profiles_state = state.clone();
    app.on_load_cleanup_profiles(move || {
        let Some(app) = weak.upgrade() else { return };
        run_bridge(
            app.as_weak(),
            cleanup_profiles_state.clone(),
            "cleanup profiles",
            vec![
                "bridge".into(),
                "cleanup-profiles".into(),
                "--library".into(),
                app.get_library_path().to_string(),
            ],
        );
    });

    let weak = app.as_weak();
    let cleanup_state = state.clone();
    app.on_apply_cleanup_profile(move || {
        let Some(app) = weak.upgrade() else { return };
        let book_id = app.get_book_id().to_string();
        let profile = app.get_cleanup_profile_name().to_string();
        if book_id.trim().is_empty() {
            app.set_status_text("Cleanup needs a book id.".into());
            return;
        }
        if profile.trim().is_empty() {
            app.set_status_text("Cleanup needs a profile name.".into());
            return;
        }
        run_bridge(
            app.as_weak(),
            cleanup_state.clone(),
            "cleanup",
            vec![
                "bridge".into(),
                "set-cleanup-profile".into(),
                book_id,
                "--library".into(),
                app.get_library_path().to_string(),
                "--cleanup-profile".into(),
                profile,
            ],
        );
    });

    let weak = app.as_weak();
    app.on_open_output(move || {
        let Some(app) = weak.upgrade() else { return };
        let output = app.get_last_output_path().to_string();
        if output.trim().is_empty() {
            app.set_status_text("No output path to open.".into());
            return;
        }
        open_output(app.as_weak(), output, false);
    });

    let weak = app.as_weak();
    app.on_open_output_folder(move || {
        let Some(app) = weak.upgrade() else { return };
        let output = app.get_last_output_path().to_string();
        if output.trim().is_empty() {
            app.set_status_text("No output path to open.".into());
            return;
        }
        open_output(app.as_weak(), output, true);
    });

    let weak = app.as_weak();
    app.on_browse_podcast_script(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(path) = choose_file("Choose reviewed podcast script", &[("JSON", &["json"])]) {
            let path = path_to_string(&path);
            app.set_podcast_script_path(path.clone().into());
            load_podcast_script_preview(&app, &path, false);
        }
    });

    let weak = app.as_weak();
    app.on_reload_podcast_script(move || {
        let Some(app) = weak.upgrade() else { return };
        let path = app.get_podcast_script_path().to_string();
        load_podcast_script_preview(&app, &path, false);
    });

    let weak = app.as_weak();
    app.on_validate_podcast_script(move || {
        let Some(app) = weak.upgrade() else { return };
        match validate_podcast_script_json(&app.get_podcast_script_json().to_string()) {
            Ok(script) => {
                app.set_podcast_text(podcast_script_preview_text(&script).into());
                app.set_podcast_review_text(
                    podcast_review_text(&script, Some(&app.get_podcast_script_path().to_string()))
                        .into(),
                );
                app.set_status_text("Podcast script JSON is valid.".into());
                app.set_guide_text(
                    "Script valid. Save it, confirm voices, then Render Podcast.".into(),
                );
            }
            Err(error) => {
                app.set_status_text(format!("Podcast script JSON invalid: {error}").into());
                app.set_guide_text("Fix script JSON before saving or rendering.".into());
            }
        }
    });

    let weak = app.as_weak();
    app.on_save_podcast_script(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Err(error) = save_podcast_script_editor(&app) {
            app.set_status_text(error.clone().into());
            app.set_guide_text(error.into());
        }
    });

    let weak = app.as_weak();
    app.on_open_podcast_script(move || {
        let Some(app) = weak.upgrade() else { return };
        let path = app.get_podcast_script_path().to_string();
        if path.trim().is_empty() {
            app.set_status_text("No podcast script path to open.".into());
            return;
        }
        open_output(app.as_weak(), path, false);
    });

    let weak = app.as_weak();
    app.on_open_podcast_script_folder(move || {
        let Some(app) = weak.upgrade() else { return };
        let path = app.get_podcast_script_path().to_string();
        if path.trim().is_empty() {
            app.set_status_text("No podcast script folder to open.".into());
            return;
        }
        open_output(app.as_weak(), path, true);
    });

    let weak = app.as_weak();
    let render_state = state.clone();
    app.on_load_preview(move || {
        let Some(app) = weak.upgrade() else { return };
        let book_id = app.get_book_id().to_string();
        if book_id.trim().is_empty() {
            app.set_status_text("Preview needs a book id.".into());
            return;
        }
        run_bridge(
            app.as_weak(),
            render_state.clone(),
            "preview",
            preview_args(&app, book_id),
        );
    });

    let weak = app.as_weak();
    let previous_state = state.clone();
    app.on_previous_book(move || {
        let Some(app) = weak.upgrade() else { return };
        let Some(book_id) = select_book_id(
            &app,
            &previous_state.book_ids,
            &previous_state.book_index,
            -1,
        ) else {
            app.set_status_text("Refresh Books before using Previous/Next.".into());
            return;
        };
        app.set_book_id(book_id.clone().into());
        run_bridge(
            app.as_weak(),
            previous_state.clone(),
            "preview",
            preview_args(&app, book_id),
        );
    });

    let weak = app.as_weak();
    let next_state = state.clone();
    app.on_next_book(move || {
        let Some(app) = weak.upgrade() else { return };
        let Some(book_id) = select_book_id(&app, &next_state.book_ids, &next_state.book_index, 1)
        else {
            app.set_status_text("Refresh Books before using Previous/Next.".into());
            return;
        };
        app.set_book_id(book_id.clone().into());
        run_bridge(
            app.as_weak(),
            next_state.clone(),
            "preview",
            preview_args(&app, book_id),
        );
    });

    let weak = app.as_weak();
    let chapter_state = state.clone();
    app.on_load_chapter(move || {
        let Some(app) = weak.upgrade() else { return };
        let book_id = app.get_book_id().to_string();
        if book_id.trim().is_empty() {
            app.set_status_text("Chapter load needs a book id.".into());
            return;
        }
        let Ok(chapter_index) = parse_chapter_index(&app.get_chapter_edit_index().to_string())
        else {
            app.set_status_text("Chapter index must be zero or a positive whole number.".into());
            return;
        };
        run_bridge(
            app.as_weak(),
            chapter_state.clone(),
            "chapter",
            vec![
                "bridge".into(),
                "chapter-detail".into(),
                book_id,
                "--library".into(),
                app.get_library_path().to_string(),
                "--chapter-index".into(),
                chapter_index.to_string(),
            ],
        );
    });

    let weak = app.as_weak();
    let chapter_save_state = state.clone();
    app.on_save_chapter(move || {
        let Some(app) = weak.upgrade() else { return };
        let book_id = app.get_book_id().to_string();
        if book_id.trim().is_empty() {
            app.set_status_text("Chapter save needs a book id.".into());
            return;
        }
        let Ok(chapter_index) = parse_chapter_index(&app.get_chapter_edit_index().to_string())
        else {
            app.set_status_text("Chapter index must be zero or a positive whole number.".into());
            return;
        };
        let title = app.get_chapter_edit_title().to_string();
        let text = app.get_chapter_edit_text().to_string();
        if title.trim().is_empty() {
            app.set_status_text("Chapter save needs a title.".into());
            return;
        }
        if text.trim().is_empty() {
            app.set_status_text("Chapter save needs text.".into());
            return;
        }
        run_bridge(
            app.as_weak(),
            chapter_save_state.clone(),
            "chapter save",
            vec![
                "bridge".into(),
                "update-chapter".into(),
                book_id,
                "--library".into(),
                app.get_library_path().to_string(),
                "--chapter-index".into(),
                chapter_index.to_string(),
                "--title".into(),
                title,
                "--text".into(),
                text,
            ],
        );
    });

    let weak = app.as_weak();
    let tts_test_state = state.clone();
    app.on_tts_test(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(problem) = tts_test_preflight_problem(&app) {
            app.set_status_text(problem.clone().into());
            app.set_engine_check_text(problem.clone().into());
            app.set_engine_setup_text(engine_setup_text(&app).into());
            app.set_guide_text(problem.into());
            return;
        }
        run_bridge(
            app.as_weak(),
            tts_test_state.clone(),
            "tts test",
            tts_test_args(&app),
        );
    });

    let weak = app.as_weak();
    let sample_state = state.clone();
    app.on_sample_render(move || {
        let Some(app) = weak.upgrade() else { return };
        let book_id = app.get_book_id().to_string();
        if let Some(problem) = render_preflight_problem(&app, &book_id) {
            app.set_status_text(problem.clone().into());
            app.set_guide_text(problem.into());
            app.set_render_plan_text(render_plan_text(&app).into());
            app.set_engine_setup_text(engine_setup_text(&app).into());
            return;
        }
        if let Err(problem) = optional_audiobook_speaker_voice_entries(&app) {
            app.set_status_text(problem.clone().into());
            app.set_guide_text(problem.into());
            return;
        }
        app.set_render_plan_text(render_plan_text(&app).into());
        let args = render_args(&app, "sample-render", book_id);
        run_bridge(app.as_weak(), sample_state.clone(), "sample render", args);
    });

    let weak = app.as_weak();
    let render_state = state.clone();
    app.on_render_book(move || {
        let Some(app) = weak.upgrade() else { return };
        let book_id = app.get_book_id().to_string();
        if let Some(problem) = render_preflight_problem(&app, &book_id) {
            app.set_status_text(problem.clone().into());
            app.set_guide_text(problem.into());
            app.set_render_plan_text(render_plan_text(&app).into());
            app.set_engine_setup_text(engine_setup_text(&app).into());
            return;
        }
        if let Some(problem) = render_limit_problem(&app) {
            app.set_status_text(problem.clone().into());
            app.set_guide_text(problem.into());
            app.set_render_plan_text(render_plan_text(&app).into());
            return;
        }
        if let Err(problem) = optional_audiobook_speaker_voice_entries(&app) {
            app.set_status_text(problem.clone().into());
            app.set_guide_text(problem.into());
            return;
        }
        app.set_render_plan_text(render_plan_text(&app).into());
        let args = render_args(&app, "render", book_id);
        run_bridge(app.as_weak(), render_state.clone(), "render", args);
    });

    let weak = app.as_weak();
    let character_state = state.clone();
    app.on_suggest_characters(move || {
        let Some(app) = weak.upgrade() else { return };
        let book_id = app.get_book_id().to_string();
        if book_id.trim().is_empty() {
            app.set_status_text("Character extraction needs a book id.".into());
            return;
        }
        let mut args = vec![
            "bridge".into(),
            "characters".into(),
            book_id,
            "--library".into(),
            app.get_library_path().to_string(),
        ];
        args.extend(ollama_args(&app));
        run_bridge(app.as_weak(), character_state.clone(), "characters", args);
    });

    let weak = app.as_weak();
    let script_state = state.clone();
    app.on_podcast_script(move || {
        let Some(app) = weak.upgrade() else { return };
        let book_id = app.get_book_id().to_string();
        if book_id.trim().is_empty() {
            app.set_status_text("Podcast script needs a book id.".into());
            return;
        }
        let mut args = vec![
            "bridge".into(),
            "podcast-script".into(),
            book_id,
            "--library".into(),
            app.get_library_path().to_string(),
            "--mode".into(),
            podcast_mode(app.get_podcast_mode_index()).into(),
        ];
        args.extend(ollama_args(&app));
        args.extend(podcast_prompt_args(&app));
        run_bridge(app.as_weak(), script_state.clone(), "podcast script", args);
    });

    let weak = app.as_weak();
    app.on_use_educational_podcast_preset(move || {
        let Some(app) = weak.upgrade() else { return };
        apply_podcast_preset(&app, 0);
    });

    let weak = app.as_weak();
    app.on_use_controversial_podcast_preset(move || {
        let Some(app) = weak.upgrade() else { return };
        apply_podcast_preset(&app, 1);
    });

    let weak = app.as_weak();
    app.on_use_interview_podcast_preset(move || {
        let Some(app) = weak.upgrade() else { return };
        apply_podcast_preset(&app, 2);
    });

    let weak = app.as_weak();
    let podcast_render_state = state.clone();
    app.on_podcast_render(move || {
        let Some(app) = weak.upgrade() else { return };
        let book_id = app.get_book_id().to_string();
        if book_id.trim().is_empty() {
            app.set_status_text("Podcast render needs a book id.".into());
            return;
        }
        if let Err(problem) = confirmed_speaker_voice_entries(&app) {
            app.set_status_text(problem.clone().into());
            app.set_podcast_review_text(
                "Assign every speaker=voice pair and tick confirmation before rendering.".into(),
            );
            app.set_guide_text(problem.into());
            return;
        }
        if let Some(problem) = media_tool_path_problem(&app) {
            app.set_status_text(problem.clone().into());
            app.set_guide_text(problem.into());
            return;
        }
        let args = podcast_render_args(&app, book_id);
        run_bridge(
            app.as_weak(),
            podcast_render_state.clone(),
            "podcast render",
            args,
        );
    });

    let weak = app.as_weak();
    let podcast_interactive_state = state.clone();
    app.on_podcast_interactive(move || {
        let Some(app) = weak.upgrade() else { return };
        let book_id = app.get_book_id().to_string();
        if book_id.trim().is_empty() {
            app.set_status_text("Interactive podcast needs a book id.".into());
            return;
        }
        if let Some(problem) = optional_positive_limit_problem(
            &app.get_interactive_turns().to_string(),
            "Interactive turns",
        ) {
            app.set_status_text(problem.into());
            return;
        }
        if let Err(problem) = confirmed_speaker_voice_entries(&app) {
            app.set_status_text(problem.clone().into());
            app.set_podcast_review_text(
                "Assign every speaker=voice pair and tick confirmation before interactive render."
                    .into(),
            );
            app.set_guide_text(problem.into());
            return;
        }
        if let Some(problem) = media_tool_path_problem(&app) {
            app.set_status_text(problem.clone().into());
            app.set_guide_text(problem.into());
            return;
        }
        let args = podcast_interactive_args(&app, book_id);
        app.set_podcast_text("Interactive podcast running...".into());
        run_bridge(
            app.as_weak(),
            podcast_interactive_state.clone(),
            "interactive podcast",
            args,
        );
    });

    let weak = app.as_weak();
    let refresh_state = state.clone();
    let health_state = state.clone();
    app.on_refresh_audio_cpp(move || {
        if let Some(app) = weak.upgrade() {
            run_bridge(
                app.as_weak(),
                health_state.clone(),
                "audio.cpp health",
                audio_cpp_health_args(&app),
            );
        }
        refresh_audio_cpp(weak.clone(), refresh_state.repo_root.clone(), true);
    });

    let weak = app.as_weak();
    let retry_state = state.clone();
    app.on_retry_job(move || {
        let Some(app) = weak.upgrade() else { return };
        let last_job = retry_state
            .last_bridge_job
            .lock()
            .expect("last bridge job lock")
            .clone();
        let Some(last_job) = last_job else {
            app.set_status_text("No bridge job to retry yet.".into());
            return;
        };
        run_bridge(
            app.as_weak(),
            retry_state.clone(),
            last_job.label,
            last_job.args,
        );
    });

    let weak = app.as_weak();
    let cancel_state = state;
    app.on_cancel_job(move || {
        cancel_active_job(
            weak.clone(),
            cancel_state.active_pid.clone(),
            cancel_state.jobs.clone(),
        );
    });
}

fn run_bridge(
    weak: slint::Weak<AppWindow>,
    state: AppState,
    label: &'static str,
    args: Vec<String>,
) {
    if state.active_pid.lock().expect("pid lock").is_some() {
        set_status(
            weak.clone(),
            "Another job is running. Wait or cancel before starting a new job.",
        );
        push_log(
            weak,
            &format!("Skipped {label}: another job is already running."),
        );
        return;
    }
    *state.last_bridge_job.lock().expect("last bridge job lock") = Some(BridgeJobRequest {
        label,
        args: args.clone(),
    });
    let job_id = create_job(
        weak.clone(),
        state.jobs.clone(),
        label,
        "queued",
        0,
        "Waiting",
    );
    set_status(weak.clone(), &format!("Running {label}..."));
    thread::spawn(move || {
        update_job(
            weak.clone(),
            state.jobs.clone(),
            job_id,
            "running",
            1,
            "Process started",
        );
        let (program, mut base_args) = python_invocation(&state.repo_root);
        base_args.extend(["-m".into(), "bookcast".into()]);
        base_args.extend(args);

        let mut command = Command::new(program);
        command
            .args(base_args)
            .current_dir(&state.repo_root)
            .env("PYTHONPATH", state.repo_root.join("src"))
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        match command.spawn() {
            Ok(child) => {
                let pid = child.id();
                *state.active_pid.lock().expect("pid lock") = Some(pid);
                let output = child.wait_with_output();
                *state.active_pid.lock().expect("pid lock") = None;
                match output {
                    Ok(output) => {
                        let stdout = String::from_utf8_lossy(&output.stdout);
                        let stderr = String::from_utf8_lossy(&output.stderr);
                        let cancelled = job_has_status(&state.jobs, job_id, "cancelled");
                        if cancelled {
                            set_status(weak.clone(), &format!("{label} cancelled."));
                        } else if output.status.success() {
                            set_status(weak.clone(), &format!("{label} completed."));
                            update_job(
                                weak.clone(),
                                state.jobs.clone(),
                                job_id,
                                "done",
                                100,
                                "Completed",
                            );
                        } else {
                            set_status(weak.clone(), &format!("{label} failed."));
                            update_job(
                                weak.clone(),
                                state.jobs.clone(),
                                job_id,
                                "failed",
                                100,
                                "Process failed",
                            );
                        }
                        if !cancelled {
                            handle_bridge_events(
                                weak.clone(),
                                state.jobs.clone(),
                                state.book_ids.clone(),
                                state.book_index.clone(),
                                job_id,
                                &stdout,
                            );
                        }
                        let mut text = String::new();
                        if !stdout.trim().is_empty() {
                            text.push_str(stdout.trim());
                        }
                        if !stderr.trim().is_empty() {
                            if !text.is_empty() {
                                text.push_str("\n");
                            }
                            text.push_str(stderr.trim());
                        }
                        if text.is_empty() {
                            text = format!("{label} finished with no output.");
                        }
                        if !cancelled {
                            update_job_detail(
                                weak.clone(),
                                state.jobs.clone(),
                                job_id,
                                &summarize_output(&text),
                            );
                            if !output.status.success() {
                                set_guide(weak.clone(), &bridge_recovery_text(&text));
                            }
                        }
                        if label == "diagnose" && !cancelled {
                            set_diagnostics(weak.clone(), &text);
                        }
                    }
                    Err(error) => {
                        set_status(weak.clone(), &format!("{label} failed."));
                        update_job(
                            weak.clone(),
                            state.jobs.clone(),
                            job_id,
                            "failed",
                            100,
                            &format!("Failed to read process output: {error}"),
                        );
                    }
                }
            }
            Err(error) => {
                set_status(weak.clone(), &format!("{label} failed."));
                update_job(
                    weak.clone(),
                    state.jobs.clone(),
                    job_id,
                    "failed",
                    100,
                    &format!("Failed to start Python bridge: {error}"),
                );
            }
        }
    });
}

fn refresh_audio_cpp(weak: slint::Weak<AppWindow>, repo_root: PathBuf, announce: bool) {
    if announce {
        set_status(weak.clone(), "Checking audio.cpp upstream...");
    } else {
        set_audio_status(weak.clone(), "audio.cpp: checking upstream...");
    }
    thread::spawn(move || {
        let pinned = AUDIO_CPP_PINNED.trim();
        let output = Command::new("git")
            .args(["ls-remote", AUDIO_CPP_REMOTE, "HEAD"])
            .current_dir(repo_root)
            .output();
        match output {
            Ok(output) if output.status.success() => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                let remote = stdout.split_whitespace().next().unwrap_or("").trim();
                let status = audio_cpp_update_status(pinned, remote);
                set_audio_status(weak.clone(), &status);
                push_log(weak.clone(), &status);
                if announce {
                    set_status(weak, "audio.cpp check completed.");
                }
            }
            Ok(output) => {
                let stderr = String::from_utf8_lossy(&output.stderr);
                let detail = stderr.trim();
                set_audio_status(weak.clone(), "audio.cpp: check failed");
                push_log(
                    weak.clone(),
                    if detail.is_empty() {
                        "audio.cpp check failed."
                    } else {
                        detail
                    },
                );
                if announce {
                    set_status(weak, "audio.cpp check failed.");
                }
            }
            Err(error) => {
                set_audio_status(weak.clone(), "audio.cpp: git not available");
                push_log(weak.clone(), &format!("audio.cpp check failed: {error}"));
                if announce {
                    set_status(weak, "audio.cpp check failed.");
                }
            }
        }
    });
}

fn audio_cpp_update_status(pinned: &str, remote: &str) -> String {
    if remote.is_empty() {
        "audio.cpp: remote returned no HEAD".to_string()
    } else if remote == pinned {
        format!("audio.cpp: pinned {} is current", short_hash(pinned))
    } else {
        format!(
            "audio.cpp: Update Available, pinned {} remote {}",
            short_hash(pinned),
            short_hash(remote)
        )
    }
}

fn cancel_active_job(
    weak: slint::Weak<AppWindow>,
    active_pid: Arc<Mutex<Option<u32>>>,
    jobs: Arc<Mutex<Vec<JobState>>>,
) {
    let pid = *active_pid.lock().expect("pid lock");
    let Some(pid) = pid else {
        set_status(weak.clone(), "No active job to cancel.");
        return;
    };
    #[cfg(windows)]
    let result = Command::new("taskkill")
        .args(["/PID", &pid.to_string(), "/T", "/F"])
        .output();
    #[cfg(not(windows))]
    let result = Command::new("kill")
        .args(["-TERM", &pid.to_string()])
        .output();

    match result {
        Ok(output) if output.status.success() => {
            set_status(weak.clone(), "Cancel sent.");
            mark_latest_running_job_cancelled(
                weak.clone(),
                jobs,
                &format!("Cancel sent to process {pid}"),
            );
            push_log(weak, &format!("Cancel sent to process {pid}."));
        }
        Ok(output) => {
            let stderr = String::from_utf8_lossy(&output.stderr);
            set_status(weak.clone(), "Cancel failed.");
            push_log(weak, &format!("Cancel failed for {pid}: {}", stderr.trim()));
        }
        Err(error) => {
            set_status(weak.clone(), "Cancel failed.");
            push_log(weak, &format!("Cancel failed for {pid}: {error}"));
        }
    }
}

fn open_output(weak: slint::Weak<AppWindow>, output: String, folder: bool) {
    let target = output_open_target(&output, folder);
    #[cfg(windows)]
    let result = if folder {
        Command::new("explorer").arg(&target).output()
    } else {
        Command::new("cmd")
            .args(["/C", "start", ""])
            .arg(&target)
            .output()
    };
    #[cfg(not(windows))]
    let result = Command::new("xdg-open").arg(&target).output();

    match result {
        Ok(output) if output.status.success() => set_status(
            weak,
            if folder {
                "Output folder opened."
            } else {
                "Output file opened."
            },
        ),
        Ok(output) => {
            let detail = String::from_utf8_lossy(&output.stderr);
            set_status(weak, &format!("Open output failed: {}", detail.trim()));
        }
        Err(error) => set_status(weak, &format!("Open output failed: {error}")),
    }
}

fn output_open_target(output: &str, folder: bool) -> PathBuf {
    let path = PathBuf::from(output.trim());
    if folder && !path.is_dir() {
        return path.parent().map(Path::to_path_buf).unwrap_or(path);
    }
    path
}

fn load_podcast_script_preview(app: &AppWindow, path: &str, seed_voice_map: bool) {
    let trimmed = path.trim();
    if trimmed.is_empty() {
        app.set_status_text("Podcast script path is empty.".into());
        return;
    }
    let Ok(raw) = std::fs::read_to_string(trimmed) else {
        app.set_status_text(format!("Podcast script not readable: {trimmed}").into());
        return;
    };
    let Ok(script) = serde_json::from_str::<Value>(&raw) else {
        app.set_status_text(format!("Podcast script is not valid JSON: {trimmed}").into());
        return;
    };
    let pretty = serde_json::to_string_pretty(&script).unwrap_or(raw);
    let speaker_template = podcast_speaker_template(&script);
    if seed_voice_map && !speaker_template.is_empty() {
        app.set_speaker_voice_map(speaker_template.into());
        app.set_speaker_voices_confirmed(false);
    }
    app.set_podcast_script_json(pretty.into());
    app.set_podcast_text(podcast_script_preview_text(&script).into());
    app.set_podcast_review_text(podcast_review_text(&script, Some(trimmed)).into());
    app.set_status_text("Podcast script preview loaded.".into());
}

fn validate_podcast_script_json(raw: &str) -> Result<Value, String> {
    let script: Value = serde_json::from_str(raw.trim()).map_err(|error| error.to_string())?;
    if !script
        .get("turns")
        .and_then(Value::as_array)
        .is_some_and(|turns| !turns.is_empty())
    {
        return Err("script needs a non-empty turns array".to_string());
    }
    Ok(script)
}

fn save_podcast_script_editor(app: &AppWindow) -> Result<(), String> {
    let path = app.get_podcast_script_path().to_string();
    let trimmed = path.trim();
    if trimmed.is_empty() {
        return Err("Set Reviewed script path before saving script JSON.".to_string());
    }
    let script = validate_podcast_script_json(&app.get_podcast_script_json().to_string())?;
    let pretty = serde_json::to_string_pretty(&script).map_err(|error| error.to_string())?;
    std::fs::write(trimmed, &pretty)
        .map_err(|error| format!("Podcast script save failed: {error}"))?;
    app.set_podcast_script_json(pretty.into());
    app.set_podcast_text(podcast_script_preview_text(&script).into());
    app.set_podcast_review_text(podcast_review_text(&script, Some(trimmed)).into());
    app.set_status_text("Podcast script saved.".into());
    app.set_guide_text(
        "Saved reviewed script. Confirm speaker voices, then Render Podcast.".into(),
    );
    Ok(())
}

fn python_invocation(repo_root: &Path) -> (String, Vec<String>) {
    let venv_python = repo_root.join(".venv").join("Scripts").join("python.exe");
    if venv_python.exists() {
        return (venv_python.to_string_lossy().to_string(), Vec::new());
    }
    ("py".to_string(), vec!["-3".to_string()])
}

fn find_repo_root() -> PathBuf {
    let mut dir = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    loop {
        if dir.join("pyproject.toml").exists() {
            return dir;
        }
        if !dir.pop() {
            return std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
        }
    }
}

fn settings_path(repo_root: &Path) -> PathBuf {
    repo_root.join(".bookcast-workbench.json")
}

fn choose_folder(title: &str) -> Option<PathBuf> {
    rfd::FileDialog::new().set_title(title).pick_folder()
}

fn choose_file(title: &str, filters: &[(&str, &[&str])]) -> Option<PathBuf> {
    let mut dialog = rfd::FileDialog::new().set_title(title);
    for (name, extensions) in filters {
        dialog = dialog.add_filter(*name, *extensions);
    }
    dialog.pick_file()
}

fn path_to_string(path: &Path) -> String {
    path.to_string_lossy().into_owned()
}

fn load_settings(app: &AppWindow, repo_root: &Path) {
    let path = settings_path(repo_root);
    let Ok(raw) = std::fs::read_to_string(&path) else {
        return;
    };
    let Ok(settings) = serde_json::from_str::<WorkbenchSettings>(&raw) else {
        app.set_status_text(format!("Settings ignored, invalid JSON: {}", path.display()).into());
        return;
    };
    if !settings.library_path.is_empty() {
        app.set_library_path(settings.library_path.into());
    }
    app.set_source_path(settings.source_path.into());
    app.set_calibre_path(settings.calibre_path.into());
    app.set_calibredb_path(settings.calibredb_path.into());
    app.set_calibre_ids(settings.calibre_ids.into());
    if !settings.calibre_limit.is_empty() {
        app.set_calibre_limit(settings.calibre_limit.into());
    }
    app.set_book_id(settings.book_id.into());
    app.set_voice_name(settings.voice_name.into());
    if !settings.output_format.is_empty() {
        app.set_output_format(settings.output_format.into());
    }
    app.set_render_limit(settings.render_limit.into());
    app.set_ffmpeg_path(settings.ffmpeg_path.into());
    app.set_ffprobe_path(settings.ffprobe_path.into());
    if !settings.tts_test_text.is_empty() {
        app.set_tts_test_text(settings.tts_test_text.into());
    }
    app.set_last_output_path(settings.last_output_path.into());
    if !settings.audio_cpp_exe.is_empty() {
        app.set_audio_cpp_exe(settings.audio_cpp_exe.into());
    }
    app.set_audio_cpp_model(settings.audio_cpp_model.into());
    if !settings.audio_cpp_backend.is_empty() {
        app.set_audio_cpp_backend(settings.audio_cpp_backend.into());
    }
    app.set_audio_cpp_family(settings.audio_cpp_family.into());
    if !settings.piper_exe.is_empty() {
        app.set_piper_exe(settings.piper_exe.into());
    }
    if !settings.piper_voice_dir.is_empty() {
        app.set_piper_voice_dir(settings.piper_voice_dir.into());
    }
    if !settings.ollama_url.is_empty() {
        app.set_ollama_url(settings.ollama_url.into());
    }
    if !settings.ollama_model.is_empty() {
        app.set_ollama_model(settings.ollama_model.into());
    }
    if !settings.speaker_voice_map.is_empty() {
        app.set_speaker_voice_map(settings.speaker_voice_map.into());
    }
    if !settings.interactive_turns.is_empty() {
        app.set_interactive_turns(settings.interactive_turns.into());
    }
    app.set_interactive_seed_prompt(settings.interactive_seed_prompt.into());
    app.set_podcast_script_path(settings.podcast_script_path.into());
    app.set_podcast_focus(settings.podcast_focus.into());
    app.set_podcast_style(settings.podcast_style.into());
    app.set_podcast_mode_index(settings.podcast_mode_index);
    let engine_index = if settings.engine_index == 1
        && (!app.get_audio_cpp_exe().to_string().is_empty()
            || !app.get_audio_cpp_model().to_string().is_empty())
    {
        2
    } else {
        settings.engine_index
    };
    app.set_engine_index(engine_index);
    app.set_current_view(settings.current_view);
    app.set_status_text(format!("Settings loaded: {}", path.display()).into());
}

fn save_settings(app: &AppWindow, repo_root: &Path) -> Result<PathBuf, String> {
    let path = settings_path(repo_root);
    let settings = WorkbenchSettings {
        library_path: app.get_library_path().to_string(),
        source_path: app.get_source_path().to_string(),
        calibre_path: app.get_calibre_path().to_string(),
        calibredb_path: app.get_calibredb_path().to_string(),
        calibre_ids: app.get_calibre_ids().to_string(),
        calibre_limit: app.get_calibre_limit().to_string(),
        book_id: app.get_book_id().to_string(),
        voice_name: app.get_voice_name().to_string(),
        output_format: app.get_output_format().to_string(),
        render_limit: app.get_render_limit().to_string(),
        ffmpeg_path: app.get_ffmpeg_path().to_string(),
        ffprobe_path: app.get_ffprobe_path().to_string(),
        tts_test_text: app.get_tts_test_text().to_string(),
        last_output_path: app.get_last_output_path().to_string(),
        audio_cpp_exe: app.get_audio_cpp_exe().to_string(),
        audio_cpp_model: app.get_audio_cpp_model().to_string(),
        audio_cpp_backend: app.get_audio_cpp_backend().to_string(),
        audio_cpp_family: app.get_audio_cpp_family().to_string(),
        piper_exe: app.get_piper_exe().to_string(),
        piper_voice_dir: app.get_piper_voice_dir().to_string(),
        ollama_url: app.get_ollama_url().to_string(),
        ollama_model: app.get_ollama_model().to_string(),
        speaker_voice_map: app.get_speaker_voice_map().to_string(),
        interactive_turns: app.get_interactive_turns().to_string(),
        interactive_seed_prompt: app.get_interactive_seed_prompt().to_string(),
        podcast_script_path: app.get_podcast_script_path().to_string(),
        podcast_focus: app.get_podcast_focus().to_string(),
        podcast_style: app.get_podcast_style().to_string(),
        podcast_mode_index: app.get_podcast_mode_index(),
        engine_index: app.get_engine_index(),
        current_view: app.get_current_view(),
    };
    let raw = serde_json::to_string_pretty(&settings).map_err(|error| error.to_string())?;
    std::fs::write(&path, raw).map_err(|error| error.to_string())?;
    Ok(path)
}

fn short_hash(value: &str) -> String {
    value.chars().take(12).collect()
}

fn split_ids(value: &str) -> Vec<String> {
    value
        .split(|ch: char| ch == ',' || ch == ';' || ch.is_whitespace())
        .filter_map(|part| {
            let trimmed = part.trim();
            (!trimmed.is_empty()).then(|| trimmed.to_string())
        })
        .collect()
}

fn split_voice_map(value: &str) -> Vec<String> {
    value
        .split(|ch: char| ch == '\n' || ch == '\r' || ch == ';' || ch == ',')
        .filter_map(|part| {
            let trimmed = part.trim();
            if trimmed.is_empty() || !trimmed.contains('=') {
                return None;
            }
            let (speaker, voice) = trimmed.split_once('=').unwrap_or(("", ""));
            (!speaker.trim().is_empty() && !voice.trim().is_empty()).then(|| trimmed.to_string())
        })
        .collect()
}

fn confirmed_speaker_voice_entries(app: &AppWindow) -> Result<Vec<String>, String> {
    confirmed_voice_entries_from(
        &app.get_speaker_voice_map().to_string(),
        app.get_speaker_voices_confirmed(),
    )
}

fn optional_audiobook_speaker_voice_entries(app: &AppWindow) -> Result<Vec<String>, String> {
    optional_voice_entries_from(
        &app.get_speaker_voice_map().to_string(),
        app.get_speaker_voices_confirmed(),
    )
}

fn confirmed_voice_entries_from(value: &str, confirmed: bool) -> Result<Vec<String>, String> {
    let entries = split_voice_map(value);
    if entries.is_empty() {
        return Err("Speaker voice mapping is required before podcast rendering.".to_string());
    }
    if !confirmed {
        return Err(
            "Review every speaker=voice assignment, then tick confirmation before rendering."
                .to_string(),
        );
    }
    Ok(entries)
}

fn optional_voice_entries_from(value: &str, confirmed: bool) -> Result<Vec<String>, String> {
    let entries = split_voice_map(value);
    if entries.is_empty() {
        return Ok(entries);
    }
    if !confirmed {
        return Err(
            "Review character speaker=voice assignments and tick confirmation before multi-voice audiobook rendering."
                .to_string(),
        );
    }
    Ok(entries)
}

fn podcast_mode(index: i32) -> &'static str {
    match index {
        1 => "controversial",
        2 => "interview",
        _ => "educational",
    }
}

fn podcast_preset(index: i32) -> (&'static str, &'static str) {
    match index {
        1 => (
            "strong claims, counterarguments, evidence quality, and tradeoffs",
            "balanced but pointed debate with a fact-checking voice",
        ),
        2 => (
            "author intent, methods, findings, and concrete takeaways",
            "curious interview with concise follow-up questions",
        ),
        _ => (
            "core concepts, practical implications, and limitations",
            "clear, patient, and structured for learners",
        ),
    }
}

fn apply_podcast_preset(app: &AppWindow, index: i32) {
    let (focus, style) = podcast_preset(index);
    app.set_podcast_mode_index(index);
    app.set_podcast_focus(focus.into());
    app.set_podcast_style(style.into());
    app.set_podcast_text(format!("Preset loaded: {}.", podcast_mode(index)).into());
    app.set_podcast_review_text(
        "Review checklist: generate script, review speakers/turns, assign voices, tick confirmation, then render."
            .into(),
    );
}

fn ollama_args(app: &AppWindow) -> Vec<String> {
    vec![
        "--ollama-url".into(),
        app.get_ollama_url().to_string(),
        "--model".into(),
        app.get_ollama_model().to_string(),
    ]
}

fn render_preflight_problem(app: &AppWindow, book_id: &str) -> Option<String> {
    render_preflight_problem_from(
        book_id,
        &app.get_output_format().to_string(),
        &app.get_ffmpeg_path().to_string(),
        &app.get_ffprobe_path().to_string(),
        app.get_engine_index(),
        &app.get_piper_exe().to_string(),
        &app.get_voice_name().to_string(),
        &app.get_audio_cpp_exe().to_string(),
        &app.get_audio_cpp_model().to_string(),
        &app.get_audio_cpp_backend().to_string(),
        &app.get_audio_cpp_family().to_string(),
    )
}

fn engine_check_problem(app: &AppWindow) -> Option<String> {
    engine_check_problem_from(
        app.get_engine_index(),
        &app.get_piper_exe().to_string(),
        &app.get_voice_name().to_string(),
        &app.get_audio_cpp_exe().to_string(),
        &app.get_audio_cpp_model().to_string(),
        &app.get_audio_cpp_backend().to_string(),
        &app.get_audio_cpp_family().to_string(),
    )
}

fn tts_test_preflight_problem(app: &AppWindow) -> Option<String> {
    tts_test_preflight_problem_from(
        &app.get_tts_test_text().to_string(),
        app.get_engine_index(),
        &app.get_piper_exe().to_string(),
        &app.get_voice_name().to_string(),
        &app.get_audio_cpp_exe().to_string(),
        &app.get_audio_cpp_model().to_string(),
        &app.get_audio_cpp_backend().to_string(),
        &app.get_audio_cpp_family().to_string(),
    )
}

fn render_limit_problem(app: &AppWindow) -> Option<String> {
    let limit = app.get_render_limit().to_string();
    optional_positive_limit_problem(&limit, "Render chunk limit")
}

fn optional_positive_limit_problem(limit: &str, label: &str) -> Option<String> {
    let trimmed = limit.trim();
    if trimmed.is_empty() {
        return None;
    }
    match trimmed.parse::<u32>() {
        Ok(value) if value > 0 => None,
        _ => Some(format!("{label} must be empty or a positive whole number.")),
    }
}

fn calibredb_path_problem(app: &AppWindow) -> Option<String> {
    let value = app.get_calibredb_path().to_string();
    if value.trim().is_empty() {
        return None;
    }
    path_like_file_problem("calibredb executable", &value)
}

fn media_tool_path_problem(app: &AppWindow) -> Option<String> {
    for (label, value) in [
        ("ffmpeg executable", app.get_ffmpeg_path().to_string()),
        ("ffprobe executable", app.get_ffprobe_path().to_string()),
    ] {
        if !value.trim().is_empty() {
            if let Some(problem) = path_like_file_problem(label, &value) {
                return Some(problem);
            }
        }
    }
    None
}

fn parse_chapter_index(value: &str) -> Result<u32, String> {
    value
        .trim()
        .parse::<u32>()
        .map_err(|_| "Chapter index must be zero or a positive whole number.".to_string())
}

fn engine_check_problem_from(
    engine_index: i32,
    piper_exe: &str,
    piper_voice: &str,
    audio_cpp_exe: &str,
    audio_cpp_model: &str,
    audio_cpp_backend: &str,
    audio_cpp_family: &str,
) -> Option<String> {
    if engine_index == 1 {
        if piper_exe.trim().is_empty() {
            return Some("Piper selected, but Piper executable is missing. Run Diagnose or set Piper executable.".to_string());
        }
        if let Some(problem) = path_like_file_problem("Piper executable", piper_exe) {
            return Some(problem);
        }
        if let Some(problem) = path_like_file_problem("Piper voice/model", piper_voice) {
            return Some(problem);
        }
    }
    if engine_index == 2 {
        if audio_cpp_exe.trim().is_empty() {
            return Some("audio.cpp selected, but executable is missing. Build audio.cpp or set audiocpp_cli.exe.".to_string());
        }
        if let Some(problem) = path_like_file_problem("audio.cpp executable", audio_cpp_exe) {
            return Some(problem);
        }
        if audio_cpp_model.trim().is_empty() {
            return Some(
                "audio.cpp selected, but model is missing. Set audio.cpp model before rendering."
                    .to_string(),
            );
        }
        if let Some(problem) = path_like_file_problem("audio.cpp model", audio_cpp_model) {
            return Some(problem);
        }
        if audio_cpp_backend.trim().is_empty() {
            return Some("audio.cpp selected, but backend is empty. Use cpu unless you know another backend is available.".to_string());
        }
        if audio_cpp_family.trim().is_empty() {
            return Some(
                "audio.cpp selected, but family is missing. Set audio.cpp family, e.g. pocket_tts or qwen3_tts."
                    .to_string(),
            );
        }
    }
    None
}

fn path_like_file_problem(label: &str, value: &str) -> Option<String> {
    let value = value.trim();
    if value.is_empty() || !looks_like_path(value) || Path::new(value).exists() {
        return None;
    }
    Some(format!("{label} path not found: {value}"))
}

fn looks_like_path(value: &str) -> bool {
    let lower = value.to_ascii_lowercase();
    value.contains('\\')
        || value.contains('/')
        || value.contains(':')
        || lower.ends_with(".exe")
        || lower.ends_with(".onnx")
        || lower.ends_with(".gguf")
        || lower.ends_with(".bin")
}

fn tts_test_preflight_problem_from(
    text: &str,
    engine_index: i32,
    piper_exe: &str,
    piper_voice: &str,
    audio_cpp_exe: &str,
    audio_cpp_model: &str,
    audio_cpp_backend: &str,
    audio_cpp_family: &str,
) -> Option<String> {
    if text.trim().is_empty() {
        return Some("TTS test needs text.".to_string());
    }
    engine_check_problem_from(
        engine_index,
        piper_exe,
        piper_voice,
        audio_cpp_exe,
        audio_cpp_model,
        audio_cpp_backend,
        audio_cpp_family,
    )
}

fn render_preflight_problem_from(
    book_id: &str,
    output_format: &str,
    ffmpeg_path: &str,
    ffprobe_path: &str,
    engine_index: i32,
    piper_exe: &str,
    piper_voice: &str,
    audio_cpp_exe: &str,
    audio_cpp_model: &str,
    audio_cpp_backend: &str,
    audio_cpp_family: &str,
) -> Option<String> {
    if book_id.trim().is_empty() {
        return Some("Render needs a book id. Import a book or click Refresh Books.".to_string());
    }
    if !matches!(
        output_format.trim().to_lowercase().as_str(),
        "opus" | "mp3" | "wav" | "m4b"
    ) {
        return Some("Output must be opus, mp3, wav, or m4b.".to_string());
    }
    if let Some(problem) = path_like_file_problem("ffmpeg executable", ffmpeg_path) {
        return Some(problem);
    }
    if let Some(problem) = path_like_file_problem("ffprobe executable", ffprobe_path) {
        return Some(problem);
    }
    if let Some(problem) = engine_check_problem_from(
        engine_index,
        piper_exe,
        piper_voice,
        audio_cpp_exe,
        audio_cpp_model,
        audio_cpp_backend,
        audio_cpp_family,
    ) {
        return Some(problem);
    }
    None
}

fn render_plan_text(app: &AppWindow) -> String {
    let engine = match app.get_engine_index() {
        1 => "Piper",
        2 => "audio.cpp",
        _ => "Windows SAPI",
    };
    let book = app.get_book_id().to_string();
    let output = app.get_output_format().to_string();
    let limit = app.get_render_limit().to_string();
    let limit = if limit.trim().is_empty() {
        "all chunks".to_string()
    } else {
        format!("first {} chunks", limit.trim())
    };
    let voice = app.get_voice_name().to_string();
    let voice = if voice.trim().is_empty() {
        "default voice".to_string()
    } else {
        voice
    };
    let speaker_entries = split_voice_map(&app.get_speaker_voice_map().to_string());
    let casting = if speaker_entries.is_empty() {
        "single narrator".to_string()
    } else if app.get_speaker_voices_confirmed() {
        format!("{} confirmed speaker voice(s)", speaker_entries.len())
    } else {
        format!(
            "{} speaker voice(s) pending confirmation",
            speaker_entries.len()
        )
    };
    format!(
        "Render plan: book {}, engine {engine}, voice {voice}, casting {casting}, output {}, full render {limit}. Run sample first; full render uses same settings.",
        if book.trim().is_empty() { "(none)" } else { book.trim() },
        if output.trim().is_empty() { "opus" } else { output.trim() }
    )
}

fn render_args(app: &AppWindow, command: &str, book_id: String) -> Vec<String> {
    let mut args = vec![
        "bridge".into(),
        command.into(),
        book_id,
        "--library".into(),
        app.get_library_path().to_string(),
        "--format".into(),
        app.get_output_format().to_string(),
    ];
    let voice = app.get_voice_name().to_string();
    if !voice.trim().is_empty() {
        args.extend(["--voice".into(), voice]);
    }
    for entry in optional_audiobook_speaker_voice_entries(app).unwrap_or_default() {
        args.extend(["--speaker-voice".into(), entry]);
    }
    if app.get_speaker_voices_confirmed() {
        args.push("--confirm-speaker-voices".into());
    }
    let limit = app.get_render_limit().to_string();
    if command == "render" && !limit.trim().is_empty() {
        args.extend(["--limit".into(), limit.trim().to_string()]);
    }
    args.extend(media_tool_args(app, true));
    if app.get_engine_index() == 1 {
        args.extend(piper_args(app));
    } else if app.get_engine_index() == 2 {
        args.extend(["--provider".into(), "audio_cpp".into()]);
        args.extend([
            "--audio-cpp-exe".into(),
            app.get_audio_cpp_exe().to_string(),
        ]);
        args.extend([
            "--audio-cpp-model".into(),
            app.get_audio_cpp_model().to_string(),
        ]);
        args.extend([
            "--audio-cpp-backend".into(),
            app.get_audio_cpp_backend().to_string(),
        ]);
        let family = app.get_audio_cpp_family().to_string();
        if !family.trim().is_empty() {
            args.extend(["--audio-cpp-family".into(), family]);
        }
    }
    args
}

fn piper_args(app: &AppWindow) -> Vec<String> {
    let mut args = vec!["--provider".into(), "piper".into()];
    let exe = app.get_piper_exe().to_string();
    if !exe.trim().is_empty() {
        args.extend(["--piper-exe".into(), exe]);
    }
    let voice_dir = app.get_piper_voice_dir().to_string();
    if !voice_dir.trim().is_empty() {
        args.extend(["--piper-voice-dir".into(), voice_dir]);
    }
    let voice = app.get_voice_name().to_string();
    if !voice.trim().is_empty() {
        args.extend(["--piper-model".into(), voice]);
    }
    args
}

fn podcast_render_args(app: &AppWindow, book_id: String) -> Vec<String> {
    let mut args = vec![
        "bridge".into(),
        "podcast-render".into(),
        book_id,
        "--library".into(),
        app.get_library_path().to_string(),
        "--mode".into(),
        podcast_mode(app.get_podcast_mode_index()).into(),
        "--format".into(),
        app.get_output_format().to_string(),
    ];
    args.extend(ollama_args(app));
    args.extend(podcast_prompt_args(app));
    for entry in confirmed_speaker_voice_entries(app).unwrap_or_default() {
        args.extend(["--voice".into(), entry]);
    }
    if app.get_speaker_voices_confirmed() {
        args.push("--confirm-voices".into());
    }
    let script_path = app.get_podcast_script_path().to_string();
    if !script_path.trim().is_empty() {
        args.extend(["--script-path".into(), script_path]);
    }
    args.extend(media_tool_args(app, true));
    if app.get_engine_index() == 1 {
        args.extend(piper_args(app));
    } else if app.get_engine_index() == 2 {
        args.extend(["--provider".into(), "audio_cpp".into()]);
        args.extend([
            "--audio-cpp-exe".into(),
            app.get_audio_cpp_exe().to_string(),
        ]);
        args.extend([
            "--audio-cpp-model".into(),
            app.get_audio_cpp_model().to_string(),
        ]);
        args.extend([
            "--audio-cpp-backend".into(),
            app.get_audio_cpp_backend().to_string(),
        ]);
        let family = app.get_audio_cpp_family().to_string();
        if !family.trim().is_empty() {
            args.extend(["--audio-cpp-family".into(), family]);
        }
    }
    args
}

fn podcast_interactive_args(app: &AppWindow, book_id: String) -> Vec<String> {
    let mut args = vec![
        "bridge".into(),
        "podcast-interactive".into(),
        book_id,
        "--library".into(),
        app.get_library_path().to_string(),
        "--mode".into(),
        podcast_mode(app.get_podcast_mode_index()).into(),
        "--format".into(),
        app.get_output_format().to_string(),
        "--turns".into(),
        app.get_interactive_turns().to_string(),
    ];
    let seed = app.get_interactive_seed_prompt().to_string();
    if !seed.trim().is_empty() {
        args.extend(["--seed-prompt".into(), seed]);
    }
    args.extend(ollama_args(app));
    for entry in confirmed_speaker_voice_entries(app).unwrap_or_default() {
        args.extend(["--voice".into(), entry]);
    }
    if app.get_speaker_voices_confirmed() {
        args.push("--confirm-voices".into());
    }
    args.extend(media_tool_args(app, false));
    if app.get_engine_index() == 1 {
        args.extend(piper_args(app));
    } else if app.get_engine_index() == 2 {
        args.extend(["--provider".into(), "audio_cpp".into()]);
        args.extend([
            "--audio-cpp-exe".into(),
            app.get_audio_cpp_exe().to_string(),
        ]);
        args.extend([
            "--audio-cpp-model".into(),
            app.get_audio_cpp_model().to_string(),
        ]);
        args.extend([
            "--audio-cpp-backend".into(),
            app.get_audio_cpp_backend().to_string(),
        ]);
        let family = app.get_audio_cpp_family().to_string();
        if !family.trim().is_empty() {
            args.extend(["--audio-cpp-family".into(), family]);
        }
    }
    args
}

fn media_tool_args(app: &AppWindow, include_ffprobe: bool) -> Vec<String> {
    media_tool_args_from(
        &app.get_ffmpeg_path().to_string(),
        &app.get_ffprobe_path().to_string(),
        include_ffprobe,
    )
}

fn media_tool_args_from(ffmpeg: &str, ffprobe: &str, include_ffprobe: bool) -> Vec<String> {
    let mut args = Vec::new();
    if !ffmpeg.trim().is_empty() {
        args.extend(["--ffmpeg".to_string(), ffmpeg.trim().to_string()]);
    }
    if include_ffprobe && !ffprobe.trim().is_empty() {
        args.extend(["--ffprobe".to_string(), ffprobe.trim().to_string()]);
    }
    args
}

fn podcast_prompt_args(app: &AppWindow) -> Vec<String> {
    let mut args = Vec::new();
    let focus = app.get_podcast_focus().to_string();
    if !focus.trim().is_empty() {
        args.extend(["--focus".into(), focus]);
    }
    let style = app.get_podcast_style().to_string();
    if !style.trim().is_empty() {
        args.extend(["--style".into(), style]);
    }
    args
}

fn voice_args(app: &AppWindow) -> Vec<String> {
    let mut args = vec!["bridge".into(), "voices".into()];
    if app.get_engine_index() == 1 {
        args.extend(piper_args(app));
    } else if app.get_engine_index() == 2 {
        args.extend(["--provider".into(), "audio_cpp".into()]);
        args.extend([
            "--audio-cpp-exe".into(),
            app.get_audio_cpp_exe().to_string(),
        ]);
        args.extend([
            "--audio-cpp-model".into(),
            app.get_audio_cpp_model().to_string(),
        ]);
        args.extend([
            "--audio-cpp-backend".into(),
            app.get_audio_cpp_backend().to_string(),
        ]);
        let family = app.get_audio_cpp_family().to_string();
        if !family.trim().is_empty() {
            args.extend(["--audio-cpp-family".into(), family]);
        }
    }
    args
}

enum VoiceChoice {
    First,
    Previous,
    Next,
}

fn apply_voice_choice(app: &AppWindow, choice: VoiceChoice) {
    let current = app.get_voice_name().to_string();
    let list = app.get_voice_list_text().to_string();
    let Some(next) = voice_choice_from_list(&list, &current, choice) else {
        app.set_status_text(
            "No discovered voice IDs to choose from. Click Discover Voices first.".into(),
        );
        app.set_guide_text("Discover voices, then use First/Previous/Next Voice.".into());
        return;
    };
    app.set_voice_name(next.clone().into());
    app.set_status_text(format!("Voice selected: {next}").into());
    app.set_render_plan_text(render_plan_text(app).into());
    app.set_engine_setup_text(engine_setup_text(app).into());
}

fn voice_choice_from_list(list: &str, current: &str, choice: VoiceChoice) -> Option<String> {
    let ids = voice_ids_from_list(list);
    if ids.is_empty() {
        return None;
    }
    let index = ids.iter().position(|id| id == current).unwrap_or(0);
    let next_index = match choice {
        VoiceChoice::First => 0,
        VoiceChoice::Previous => {
            if index == 0 {
                ids.len() - 1
            } else {
                index - 1
            }
        }
        VoiceChoice::Next => (index + 1) % ids.len(),
    };
    ids.get(next_index).cloned()
}

fn voice_ids_from_list(list: &str) -> Vec<String> {
    list.lines()
        .filter_map(|line| line.split('|').next())
        .map(str::trim)
        .filter(|id| !id.is_empty() && !id.starts_with("No voices"))
        .map(ToString::to_string)
        .collect()
}

fn tts_test_args(app: &AppWindow) -> Vec<String> {
    let mut args = vec![
        "bridge".into(),
        "tts-test".into(),
        "--library".into(),
        app.get_library_path().to_string(),
        "--text".into(),
        app.get_tts_test_text().to_string(),
    ];
    let voice = app.get_voice_name().to_string();
    if !voice.trim().is_empty() {
        args.extend(["--voice".into(), voice]);
    }
    if app.get_engine_index() == 1 {
        args.extend(piper_args(app));
    } else if app.get_engine_index() == 2 {
        args.extend(["--provider".into(), "audio_cpp".into()]);
        args.extend([
            "--audio-cpp-exe".into(),
            app.get_audio_cpp_exe().to_string(),
        ]);
        args.extend([
            "--audio-cpp-model".into(),
            app.get_audio_cpp_model().to_string(),
        ]);
        args.extend([
            "--audio-cpp-backend".into(),
            app.get_audio_cpp_backend().to_string(),
        ]);
        let family = app.get_audio_cpp_family().to_string();
        if !family.trim().is_empty() {
            args.extend(["--audio-cpp-family".into(), family]);
        }
    }
    args
}

fn outputs_args(app: &AppWindow) -> Vec<String> {
    let mut args = vec![
        "bridge".into(),
        "outputs".into(),
        "--library".into(),
        app.get_library_path().to_string(),
    ];
    let book_id = app.get_book_id().to_string();
    if !book_id.trim().is_empty() {
        args.extend(["--book-id".into(), book_id]);
    }
    args
}

fn append_calibre_limit_args(args: &mut Vec<String>, app: &AppWindow) {
    let limit = app.get_calibre_limit().to_string();
    if !limit.trim().is_empty() {
        args.extend(["--limit".into(), limit.trim().to_string()]);
    }
}

fn append_calibredb_args(args: &mut Vec<String>, app: &AppWindow) {
    args.extend(calibredb_args_from(&app.get_calibredb_path().to_string()));
}

fn calibredb_args_from(value: &str) -> Vec<String> {
    let value = value.trim();
    if value.is_empty() {
        Vec::new()
    } else {
        vec!["--calibredb".to_string(), value.to_string()]
    }
}

fn preview_args(app: &AppWindow, book_id: String) -> Vec<String> {
    vec![
        "bridge".into(),
        "book-preview".into(),
        book_id,
        "--library".into(),
        app.get_library_path().to_string(),
    ]
}

fn startup_snapshot_args(app: &AppWindow) -> Vec<String> {
    let mut args = vec![
        "bridge".into(),
        "startup-snapshot".into(),
        "--library".into(),
        app.get_library_path().to_string(),
    ];
    let book_id = app.get_book_id().to_string();
    if !book_id.trim().is_empty() {
        args.extend(["--book-id".into(), book_id]);
    }
    args
}

fn select_book_id(
    app: &AppWindow,
    book_ids: &Arc<Mutex<Vec<String>>>,
    book_index: &Arc<Mutex<usize>>,
    delta: isize,
) -> Option<String> {
    let ids = book_ids.lock().expect("book ids lock");
    if ids.is_empty() {
        return None;
    }
    let current = app.get_book_id().to_string();
    let fallback = *book_index.lock().expect("book index lock");
    let current_index = ids.iter().position(|id| id == &current).unwrap_or(fallback);
    let max = ids.len().saturating_sub(1) as isize;
    let next_index = (current_index as isize + delta).clamp(0, max) as usize;
    *book_index.lock().expect("book index lock") = next_index;
    ids.get(next_index).cloned()
}

fn audio_cpp_health_args(app: &AppWindow) -> Vec<String> {
    let mut args = vec!["bridge".into(), "audio-cpp-health".into()];
    args.extend([
        "--audio-cpp-exe".into(),
        app.get_audio_cpp_exe().to_string(),
    ]);
    args.extend([
        "--audio-cpp-model".into(),
        app.get_audio_cpp_model().to_string(),
    ]);
    args.extend([
        "--audio-cpp-backend".into(),
        app.get_audio_cpp_backend().to_string(),
    ]);
    let family = app.get_audio_cpp_family().to_string();
    if !family.trim().is_empty() {
        args.extend(["--audio-cpp-family".into(), family]);
    }
    args
}

fn create_job(
    weak: slint::Weak<AppWindow>,
    jobs: Arc<Mutex<Vec<JobState>>>,
    label: &str,
    status: &str,
    progress: u8,
    detail: &str,
) -> u64 {
    let now = now_ms();
    let id = now;
    {
        let mut jobs = jobs.lock().expect("jobs lock");
        jobs.push(JobState {
            id,
            label: label.to_string(),
            status: status.to_string(),
            progress,
            detail: detail.to_string(),
            started_ms: now,
            updated_ms: now,
        });
    }
    render_queue(weak, jobs);
    id
}

fn update_job(
    weak: slint::Weak<AppWindow>,
    jobs: Arc<Mutex<Vec<JobState>>>,
    id: u64,
    status: &str,
    progress: u8,
    detail: &str,
) {
    {
        let now = now_ms();
        let mut jobs = jobs.lock().expect("jobs lock");
        if let Some(job) = jobs.iter_mut().find(|job| job.id == id) {
            job.status = status.to_string();
            job.progress = progress;
            job.detail = detail.to_string();
            job.updated_ms = now;
        }
    }
    render_queue(weak, jobs);
}

fn update_job_detail(
    weak: slint::Weak<AppWindow>,
    jobs: Arc<Mutex<Vec<JobState>>>,
    id: u64,
    detail: &str,
) {
    {
        let now = now_ms();
        let mut jobs = jobs.lock().expect("jobs lock");
        if let Some(job) = jobs.iter_mut().find(|job| job.id == id) {
            job.detail = detail.to_string();
            job.updated_ms = now;
        }
    }
    render_queue(weak, jobs);
}

fn job_has_status(jobs: &Arc<Mutex<Vec<JobState>>>, id: u64, status: &str) -> bool {
    let jobs = jobs.lock().expect("jobs lock");
    jobs.iter()
        .find(|job| job.id == id)
        .map(|job| job.status == status)
        .unwrap_or(false)
}

fn mark_latest_running_job_cancelled(
    weak: slint::Weak<AppWindow>,
    jobs: Arc<Mutex<Vec<JobState>>>,
    detail: &str,
) -> bool {
    let changed = {
        let now = now_ms();
        let mut jobs = jobs.lock().expect("jobs lock");
        if let Some(job) = jobs.iter_mut().rev().find(|job| job.status == "running") {
            job.status = "cancelled".to_string();
            job.progress = 100;
            job.detail = detail.to_string();
            job.updated_ms = now;
            true
        } else {
            false
        }
    };
    if changed {
        render_queue(weak, jobs);
    }
    changed
}

fn render_queue(weak: slint::Weak<AppWindow>, jobs: Arc<Mutex<Vec<JobState>>>) {
    let (summary, action, text) = {
        let jobs = jobs.lock().expect("jobs lock");
        if jobs.is_empty() {
            (
                "No active jobs. Queue idle.".to_string(),
                "Queue action: start an import, engine check, or render job.".to_string(),
                "Queue idle.".to_string(),
            )
        } else {
            (
                queue_summary(&jobs),
                queue_action(&jobs),
                jobs.iter()
                    .rev()
                    .take(8)
                    .map(job_queue_line)
                    .collect::<Vec<_>>()
                    .join("\n\n"),
            )
        }
    };
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            let readiness = workbench_readiness(
                &app.get_book_id().to_string(),
                app.get_engine_index(),
                &app.get_engine_check_text().to_string(),
                &app.get_last_output_path().to_string(),
                &summary,
            );
            let checklist = setup_checklist(
                &app.get_library_path().to_string(),
                &app.get_diagnostic_text().to_string(),
                &app.get_book_id().to_string(),
                app.get_engine_index(),
                &app.get_engine_check_text().to_string(),
                &app.get_last_output_path().to_string(),
                &summary,
            );
            app.set_queue_text(text.into());
            app.set_queue_summary(summary.into());
            app.set_queue_action_text(action.into());
            app.set_readiness_text(readiness.into());
            app.set_setup_checklist_text(checklist.into());
            app.set_engine_setup_text(engine_setup_text(&app).into());
        }
    });
}

fn queue_summary(jobs: &[JobState]) -> String {
    if let Some(job) = jobs.iter().rev().find(|job| job.status == "running") {
        return format!(
            "Running: {} at {}% after {} (ETA {}) | {}",
            job.label,
            job.progress,
            elapsed_label(job),
            eta_label(job),
            job.detail
        );
    }
    if let Some(job) = jobs.iter().rev().find(|job| job.status == "failed") {
        return format!("Attention: {} failed | {}", job.label, job.detail);
    }
    if let Some(job) = jobs.last() {
        if job.status == "cancelled" {
            return format!("Last cancelled: {} | {}", job.label, job.detail);
        }
        return format!("Last done: {} | {}", job.label, job.detail);
    }
    "No active jobs. Queue idle.".to_string()
}

fn queue_action(jobs: &[JobState]) -> String {
    if let Some(job) = jobs.iter().rev().find(|job| job.status == "running") {
        return format!(
            "Queue action: wait for {} or click Cancel. Current step: {}.",
            job.label, job.detail
        );
    }
    if let Some(job) = jobs.iter().rev().find(|job| job.status == "failed") {
        return format!(
            "Queue action: fix the issue, then Retry Last. Failed step: {}.",
            job.detail
        );
    }
    if let Some(job) = jobs.last() {
        if job.status == "cancelled" {
            return format!(
                "Queue action: {} was cancelled. Use Retry Last to resume from cached chunks when ready.",
                job.label
            );
        }
        if job.status == "done" && looks_like_output_path(&job.detail) {
            return "Queue action: output exists. Use Open File to play or Open Folder to inspect."
                .to_string();
        }
        if job.status == "done" {
            return format!(
                "Queue action: {} completed. Continue with the next guided step.",
                job.label
            );
        }
    }
    "Queue action: start an import, engine check, or render job.".to_string()
}

fn looks_like_output_path(value: &str) -> bool {
    let lower = value.trim().to_ascii_lowercase();
    lower.ends_with(".opus")
        || lower.ends_with(".mp3")
        || lower.ends_with(".wav")
        || lower.ends_with(".m4b")
}

fn progress_bar(progress: u8) -> String {
    let progress = progress.min(100);
    let filled = (progress as usize + 5) / 10;
    format!("[{}{}]", "#".repeat(filled), "-".repeat(10 - filled))
}

fn now_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_millis() as u64)
        .unwrap_or(0)
}

fn elapsed_label(job: &JobState) -> String {
    format_elapsed_ms(job.updated_ms.saturating_sub(job.started_ms))
}

fn eta_label(job: &JobState) -> String {
    if job.status != "running" || job.progress == 0 || job.progress >= 100 {
        return "--:--".to_string();
    }
    let elapsed_ms = job.updated_ms.saturating_sub(job.started_ms);
    let total_ms = elapsed_ms.saturating_mul(100) / u64::from(job.progress);
    format_elapsed_ms(total_ms.saturating_sub(elapsed_ms))
}

fn format_elapsed_ms(ms: u64) -> String {
    let seconds = ms / 1000;
    let minutes = seconds / 60;
    let seconds = seconds % 60;
    format!("{minutes:02}:{seconds:02}")
}

fn job_status_label(status: &str) -> &str {
    match status {
        "queued" => "Queued",
        "running" => "Running",
        "done" => "Done",
        "failed" => "Failed",
        "cancelled" => "Cancelled",
        _ => "Status",
    }
}

fn job_queue_line(job: &JobState) -> String {
    format!(
        "{} {:>3}%  {}  {}  elapsed {}  ETA {}\n  id #{:05}  {}",
        progress_bar(job.progress),
        job.progress.min(100),
        job_status_label(&job.status),
        job.label,
        elapsed_label(job),
        eta_label(job),
        job.id % 100000,
        job.detail
    )
}

fn workbench_readiness(
    book_id: &str,
    engine_index: i32,
    engine_check: &str,
    last_output: &str,
    queue_summary: &str,
) -> String {
    if queue_summary.starts_with("Running:") || queue_summary.starts_with("Attention:") {
        return queue_summary.to_string();
    }
    if book_id.trim().is_empty() {
        return "Next: import a source or Refresh Books to select a book.".to_string();
    }
    if engine_index == 2 && !engine_check.contains("audio.cpp ready") {
        return "Next: Check audio.cpp before rendering with audio.cpp.".to_string();
    }
    if !engine_check.contains("OK") {
        return "Next: Check Engine, then render a short sample.".to_string();
    }
    if last_output.trim().is_empty() {
        return "Ready for sample render. Full render after sample sounds acceptable.".to_string();
    }
    format!("Output ready: {last_output}. Open file or render another format.")
}

fn setup_checklist(
    library_path: &str,
    diagnostic_text: &str,
    book_id: &str,
    engine_index: i32,
    engine_check: &str,
    last_output: &str,
    queue_summary: &str,
) -> String {
    let diagnostics_done = !diagnostic_text.contains("Run diagnostics")
        && !diagnostic_text.contains("not run")
        && !diagnostic_text.trim().is_empty();
    let book_selected = !book_id.trim().is_empty();
    let engine_ready = if engine_index == 2 {
        engine_check.contains("audio.cpp ready")
    } else {
        engine_check.contains("OK") || engine_check.contains("voices")
    };
    let sample_or_output_done = !last_output.trim().is_empty();
    let queue_ok = !queue_summary.starts_with("Attention:");

    [
        checklist_line("Library path set", !library_path.trim().is_empty()),
        checklist_line("Diagnostics run", diagnostics_done),
        checklist_line("Book selected", book_selected),
        checklist_line("Engine checked", engine_ready),
        checklist_line("Sample or output rendered", sample_or_output_done),
        checklist_line("Queue healthy", queue_ok),
    ]
    .join("\n")
}

fn checklist_line(label: &str, done: bool) -> String {
    format!("{} {}", if done { "[x]" } else { "[ ]" }, label)
}

fn engine_setup_text(app: &AppWindow) -> String {
    engine_setup_text_from(
        app.get_engine_index(),
        &app.get_piper_exe().to_string(),
        &app.get_voice_name().to_string(),
        &app.get_audio_cpp_exe().to_string(),
        &app.get_audio_cpp_model().to_string(),
        &app.get_audio_cpp_backend().to_string(),
        &app.get_audio_cpp_family().to_string(),
        &app.get_engine_check_text().to_string(),
    )
}

fn engine_setup_text_from(
    engine_index: i32,
    piper_exe: &str,
    voice: &str,
    audio_cpp_exe: &str,
    audio_cpp_model: &str,
    audio_cpp_backend: &str,
    audio_cpp_family: &str,
    engine_check: &str,
) -> String {
    match engine_index {
        1 => [
            "Piper voices setup".to_string(),
            checklist_line("Piper app selected", !piper_exe.trim().is_empty()),
            checklist_line(
                "Piper app exists",
                path_like_file_problem("Piper executable", piper_exe).is_none()
                    && !piper_exe.trim().is_empty(),
            ),
            checklist_line("Voice selected", !voice.trim().is_empty()),
            checklist_line("Engine check passed", engine_check.contains("OK")),
            "Next: Check Voice Engine, render TTS Test, then Render Sample.".to_string(),
        ]
        .join("\n"),
        2 => [
            "audio.cpp advanced setup".to_string(),
            checklist_line("audio.cpp app selected", !audio_cpp_exe.trim().is_empty()),
            checklist_line(
                "audio.cpp app exists",
                path_like_file_problem("audio.cpp executable", audio_cpp_exe).is_none()
                    && !audio_cpp_exe.trim().is_empty(),
            ),
            checklist_line("Model configured", !audio_cpp_model.trim().is_empty()),
            checklist_line(
                "Model path exists or model name used",
                path_like_file_problem("audio.cpp model", audio_cpp_model).is_none()
                    && !audio_cpp_model.trim().is_empty(),
            ),
            checklist_line("Backend set", !audio_cpp_backend.trim().is_empty()),
            checklist_line("Model family set", !audio_cpp_family.trim().is_empty()),
            checklist_line(
                "Engine check passed",
                engine_check.contains("audio.cpp ready"),
            ),
            "Next: Check audio.cpp, render TTS Test, then Render Sample.".to_string(),
        ]
        .join("\n"),
        _ => [
            "Windows voices setup".to_string(),
            checklist_line("No path needed", true),
            checklist_line("Engine check passed", engine_check.contains("OK")),
            "Next: Check Voice Engine or render TTS Test, then Render Sample.".to_string(),
        ]
        .join("\n"),
    }
}

fn refresh_readiness(weak: slint::Weak<AppWindow>) {
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            let readiness = workbench_readiness(
                &app.get_book_id().to_string(),
                app.get_engine_index(),
                &app.get_engine_check_text().to_string(),
                &app.get_last_output_path().to_string(),
                &app.get_queue_summary().to_string(),
            );
            let checklist = setup_checklist(
                &app.get_library_path().to_string(),
                &app.get_diagnostic_text().to_string(),
                &app.get_book_id().to_string(),
                app.get_engine_index(),
                &app.get_engine_check_text().to_string(),
                &app.get_last_output_path().to_string(),
                &app.get_queue_summary().to_string(),
            );
            app.set_readiness_text(readiness.into());
            app.set_setup_checklist_text(checklist.into());
            app.set_engine_setup_text(engine_setup_text(&app).into());
        }
    });
}

fn summarize_output(text: &str) -> String {
    if let Some(value) = text
        .lines()
        .rev()
        .find_map(|line| serde_json::from_str::<Value>(line).ok())
    {
        if let Some(message) = value.get("message").and_then(Value::as_str) {
            return message.chars().take(180).collect();
        }
        if let Some(issue) = value
            .get("issues")
            .and_then(Value::as_array)
            .and_then(|items| items.first())
            .and_then(Value::as_str)
        {
            return issue.chars().take(180).collect();
        }
    }
    text.lines()
        .rev()
        .find(|line| !line.trim().is_empty())
        .map(|line| line.trim().chars().take(180).collect())
        .unwrap_or_else(|| "No output".to_string())
}

fn bridge_recovery_text(message: &str) -> String {
    let lower = message.to_lowercase();
    let has_missing_signal = lower.contains("not found")
        || lower.contains("no such file")
        || lower.contains("cannot find")
        || lower.contains("is not recognized")
        || lower.contains("filenotfound");

    if lower.contains("ffmpeg") && has_missing_signal {
        return "ffmpeg missing. In Settings, set ffmpeg executable or add ffmpeg to PATH, save settings, then Retry Last.".to_string();
    }
    if lower.contains("ffprobe") && has_missing_signal {
        return "ffprobe missing. In Settings, set ffprobe executable or add ffprobe to PATH, save settings, then Retry Last.".to_string();
    }
    if lower.contains("calibredb") && has_missing_signal {
        return "calibredb missing. Install Calibre or set calibredb executable in Import/Settings, then Diagnose Calibre again.".to_string();
    }
    if lower.contains("metadata.db") {
        return "Calibre library not found. Select the folder that directly contains metadata.db, then Diagnose Calibre again.".to_string();
    }
    if lower.contains("audio.cpp") || lower.contains("audiocpp") {
        return "audio.cpp setup failed. Check executable, model, backend, and family, then Check audio.cpp again.".to_string();
    }
    if lower.contains("piper") {
        return "Piper setup failed. Check Piper executable and voice file/folder, then Check Voice Engine again.".to_string();
    }
    if lower.contains("ollama")
        || lower.contains("connection refused")
        || lower.contains("actively refused")
    {
        return "Ollama unavailable. Start Ollama, verify the model name, then retry script generation.".to_string();
    }

    format!("Fix required: {}", summarize_output(message))
}

fn json_string_list(value: &Value, key: &str) -> String {
    json_string_vec(value, key).join("\n")
}

fn json_string_vec(value: &Value, key: &str) -> Vec<String> {
    value
        .get(key)
        .and_then(Value::as_array)
        .map(|items| {
            items
                .iter()
                .filter_map(Value::as_str)
                .map(str::to_string)
                .collect::<Vec<_>>()
        })
        .unwrap_or_default()
}

fn preferred_audio_cpp_family(families: &[String]) -> Option<&str> {
    const PREFERRED: [&str; 5] = ["pocket_tts", "qwen3_tts", "miotts", "voxcpm2", "chatterbox"];
    PREFERRED
        .iter()
        .find(|preferred| families.iter().any(|family| family == **preferred))
        .copied()
}

fn calibre_suggested_path(suggested: &str, candidates: &[String]) -> String {
    if !suggested.trim().is_empty() {
        return suggested.trim().to_string();
    }
    candidates.first().cloned().unwrap_or_default()
}

fn calibre_action_text(
    healthy: bool,
    candidate_suggestion: &str,
    source_suggestion: &str,
    first_issue: &str,
) -> String {
    if healthy {
        return "Calibre looks valid. Next: Scan Calibre, review IDs, then Import Calibre IDs."
            .to_string();
    }
    if !candidate_suggestion.trim().is_empty() {
        return "Calibre metadata found elsewhere. Next: Use suggested Calibre, then Diagnose Calibre again.".to_string();
    }
    if !source_suggestion.trim().is_empty() {
        return "This is not a Calibre library, but supported books were found. Next: Use as Source Folder, Probe Source, then Import Source.".to_string();
    }
    if first_issue.contains("calibredb not found") {
        return "Calibre CLI missing. Install Calibre or add calibredb.exe to PATH, then Diagnose Calibre again.".to_string();
    }
    if first_issue.contains("metadata.db not found") {
        return "Wrong folder. Choose the Calibre library root, the folder containing metadata.db."
            .to_string();
    }
    format!(
        "Calibre needs attention: {}",
        if first_issue.trim().is_empty() {
            "run Diagnose Calibre and follow the issue list."
        } else {
            first_issue
        }
    )
}

fn source_probe_summary(value: &Value) -> String {
    let source = value.get("source").and_then(Value::as_str).unwrap_or("");
    match value.get("kind").and_then(Value::as_str).unwrap_or("") {
        "folder" => {
            let count = value
                .get("supported_count")
                .and_then(Value::as_i64)
                .unwrap_or(0);
            let files = value
                .get("files")
                .and_then(Value::as_array)
                .map(|items| {
                    items
                        .iter()
                        .take(20)
                        .map(|file| {
                            let format = file.get("format").and_then(Value::as_str).unwrap_or("");
                            let name = file.get("name").and_then(Value::as_str).unwrap_or("");
                            format!("{format} | {name}")
                        })
                        .collect::<Vec<_>>()
                        .join("\n")
                })
                .filter(|text| !text.is_empty())
                .unwrap_or_else(|| "No supported files listed.".to_string());
            let truncated = value
                .get("truncated")
                .and_then(Value::as_bool)
                .unwrap_or(false);
            let tail = if truncated {
                "\n\nMore files exist; import will include all supported files."
            } else {
                ""
            };
            format!("Folder source\n{source}\n\nSupported files: {count}\n{files}{tail}")
        }
        _ => {
            let title = value.get("title").and_then(Value::as_str).unwrap_or("");
            let author = value.get("author").and_then(Value::as_str).unwrap_or("");
            let format = value.get("format").and_then(Value::as_str).unwrap_or("");
            let language = value
                .get("language")
                .and_then(Value::as_str)
                .filter(|item| !item.is_empty())
                .unwrap_or("unknown");
            let chars = value.get("chars").and_then(Value::as_i64).unwrap_or(0);
            let chapter_count = value
                .get("chapter_count")
                .and_then(Value::as_i64)
                .unwrap_or(0);
            let chapters = value
                .get("chapters")
                .and_then(Value::as_array)
                .map(|items| {
                    items
                        .iter()
                        .take(12)
                        .map(|chapter| {
                            let index = chapter.get("index").and_then(Value::as_i64).unwrap_or(0);
                            let title = chapter.get("title").and_then(Value::as_str).unwrap_or("");
                            let chars = chapter.get("chars").and_then(Value::as_i64).unwrap_or(0);
                            format!("{index}: {title} ({chars} chars)")
                        })
                        .collect::<Vec<_>>()
                        .join("\n")
                })
                .unwrap_or_default();
            let preview = value.get("preview").and_then(Value::as_str).unwrap_or("");
            format!(
                "File source\n{source}\n\n{author} - {title}\nFormat: {format}, language: {language}, chars: {chars}, chapters: {chapter_count}\n\nChapters\n{chapters}\n\nPreview\n{preview}"
            )
        }
    }
}

fn character_voice_template(candidates: Option<&Vec<Value>>) -> String {
    let Some(candidates) = candidates else {
        return String::new();
    };
    let mut names = Vec::new();
    for item in candidates {
        let name = item
            .get("name")
            .and_then(Value::as_str)
            .unwrap_or("")
            .trim();
        if !name.is_empty() && !names.iter().any(|existing| existing == name) {
            names.push(name.to_string());
        }
    }
    names
        .into_iter()
        .map(|name| format!("{name}="))
        .collect::<Vec<_>>()
        .join("; ")
}

fn character_review_text(candidates: Option<&Vec<Value>>) -> String {
    let count = candidates.map(|items| items.len()).unwrap_or(0);
    if count == 0 {
        return "No candidates. Re-run extraction with Ollama running, or manually enter speaker=voice pairs.".to_string();
    }
    format!(
        "Review checklist: {count} candidate(s). Check confidence/excerpts, delete false positives, merge duplicate names, assign a voice to each kept speaker, then tick confirmation."
    )
}

fn character_candidate_line(item: &Value) -> String {
    let name = item.get("name").and_then(Value::as_str).unwrap_or("");
    let role = item.get("role").and_then(Value::as_str).unwrap_or("");
    let evidence = item.get("evidence").and_then(Value::as_str).unwrap_or("");
    let confidence = item
        .get("confidence")
        .and_then(Value::as_f64)
        .map(|value| format!(" | confidence {:.0}%", value * 100.0))
        .unwrap_or_default();
    let excerpt = item
        .get("excerpt")
        .and_then(Value::as_str)
        .filter(|value| !value.trim().is_empty())
        .map(|value| format!(" | excerpt: {}", value.trim()))
        .unwrap_or_default();
    format!("{name} | {role}{confidence} | {evidence}{excerpt}")
}

fn podcast_review_text(script: &Value, saved_or_output_path: Option<&str>) -> String {
    let speaker_count = script
        .get("speakers")
        .and_then(Value::as_array)
        .map(|items| items.len())
        .unwrap_or(0);
    let turn_count = script
        .get("turns")
        .and_then(Value::as_array)
        .map(|items| items.len())
        .unwrap_or(0);
    let path_note = saved_or_output_path
        .filter(|path| !path.trim().is_empty())
        .map(|path| format!(" Saved/output: {path}."))
        .unwrap_or_default();
    let render_note = if saved_or_output_path
        .map(|path| path.to_ascii_lowercase().ends_with(".json"))
        .unwrap_or(false)
    {
        "Render Podcast will reuse this reviewed script path."
    } else {
        "Render Podcast can reuse a reviewed script when Reviewed script path points to a saved JSON."
    };
    format!(
        "Review checklist: {speaker_count} speaker(s), {turn_count} turn(s). Assign every speaker=voice, tick confirmation, then render. {render_note}{path_note}"
    )
}

fn podcast_speaker_template(script: &Value) -> String {
    script
        .get("speakers")
        .and_then(Value::as_array)
        .map(|items| {
            items
                .iter()
                .filter_map(Value::as_str)
                .filter(|speaker| !speaker.trim().is_empty())
                .map(|speaker| format!("{speaker}="))
                .collect::<Vec<_>>()
                .join("; ")
        })
        .unwrap_or_default()
}

fn podcast_script_preview_text(script: &Value) -> String {
    let title = script
        .get("title")
        .and_then(Value::as_str)
        .unwrap_or("Untitled");
    let summary = script.get("summary").and_then(Value::as_str).unwrap_or("");
    let speakers = script
        .get("speakers")
        .and_then(Value::as_array)
        .map(|items| {
            items
                .iter()
                .filter_map(Value::as_str)
                .collect::<Vec<_>>()
                .join(", ")
        })
        .unwrap_or_default();
    let turns = script
        .get("turns")
        .and_then(Value::as_array)
        .map(|items| {
            items
                .iter()
                .take(12)
                .map(|turn| {
                    let speaker = turn
                        .get("speaker")
                        .and_then(Value::as_str)
                        .unwrap_or("host");
                    let text = turn.get("text").and_then(Value::as_str).unwrap_or("");
                    format!("{speaker}: {text}")
                })
                .collect::<Vec<_>>()
                .join("\n")
        })
        .unwrap_or_default();
    let citations = script
        .get("citations")
        .and_then(Value::as_array)
        .map(|items| {
            items
                .iter()
                .filter_map(Value::as_str)
                .take(6)
                .map(|item| format!("- {item}"))
                .collect::<Vec<_>>()
                .join("\n")
        })
        .filter(|text| !text.is_empty())
        .map(|text| format!("\n\nCitations\n{text}"))
        .unwrap_or_default();
    format!("{title}\nSpeakers: {speakers}\n\n{summary}{citations}\n\n{turns}")
}

fn import_done_detail(value: &Value) -> Option<String> {
    if value.get("job").and_then(Value::as_str) != Some("import") {
        return None;
    }
    let imported = value.get("imported")?.as_array()?;
    let duplicates = imported
        .iter()
        .filter(|item| {
            item.get("duplicate")
                .and_then(Value::as_bool)
                .unwrap_or(false)
        })
        .count();
    let total = imported.len();
    let new_count = total.saturating_sub(duplicates);
    if duplicates == 0 {
        Some(format!("Import done: {new_count} new book(s)"))
    } else {
        Some(format!(
            "Import done: {new_count} new, {duplicates} duplicate(s) reused"
        ))
    }
}

fn job_progress_detail(value: &Value) -> String {
    if let Some(phase) = value.get("phase").and_then(Value::as_str) {
        let chunk = value.get("chunk").and_then(Value::as_u64).unwrap_or(0);
        let total = value.get("total").and_then(Value::as_u64).unwrap_or(0);
        let cached = value
            .get("cached")
            .and_then(Value::as_bool)
            .map(|is_cached| if is_cached { " cached" } else { " rendered" })
            .unwrap_or("");
        if total > 0 {
            return format!("{phase} {chunk}/{total}{cached}");
        }
        return phase.to_string();
    }
    value
        .get("chunks")
        .and_then(Value::as_i64)
        .map(|chunks| format!("{chunks} chunks"))
        .unwrap_or_else(|| "Progress update".to_string())
}

fn handle_bridge_events(
    weak: slint::Weak<AppWindow>,
    jobs: Arc<Mutex<Vec<JobState>>>,
    book_ids: Arc<Mutex<Vec<String>>>,
    book_index: Arc<Mutex<usize>>,
    job_id: u64,
    stdout: &str,
) {
    for line in stdout.lines() {
        let Ok(value) = serde_json::from_str::<Value>(line) else {
            continue;
        };
        match value.get("event").and_then(Value::as_str) {
            Some("job_started") => {
                let job = value.get("job").and_then(Value::as_str).unwrap_or("job");
                update_job(
                    weak.clone(),
                    jobs.clone(),
                    job_id,
                    "running",
                    5,
                    &format!("{job} started"),
                );
            }
            Some("job_progress") => {
                let progress = value
                    .get("progress")
                    .and_then(Value::as_u64)
                    .unwrap_or(50)
                    .min(100) as u8;
                let detail = job_progress_detail(&value);
                update_job(
                    weak.clone(),
                    jobs.clone(),
                    job_id,
                    "running",
                    progress,
                    &detail,
                );
            }
            Some("job_done") => {
                let detail = import_done_detail(&value).unwrap_or_else(|| {
                    value
                        .get("output")
                        .and_then(Value::as_str)
                        .or_else(|| value.get("book_id").and_then(Value::as_str))
                        .unwrap_or("Done")
                        .to_string()
                });
                update_job(weak.clone(), jobs.clone(), job_id, "done", 100, &detail);
                if let Some(book_id) = value.get("book_id").and_then(Value::as_str) {
                    set_book_id(weak.clone(), book_id);
                    set_current_view(weak.clone(), 0);
                    let guide = if value.get("job").and_then(Value::as_str) == Some("import") {
                        import_done_detail(&value)
                            .map(|summary| {
                                format!("{summary}. Preview loads automatically. Render a sample next.")
                            })
                            .unwrap_or_else(|| {
                                "Import finished. Preview loads automatically. Render a sample next.".to_string()
                            })
                    } else {
                        "Import finished. Preview loads automatically. Render a sample next."
                            .to_string()
                    };
                    set_guide(weak.clone(), &guide);
                }
                if let Some(output) = value.get("output").and_then(Value::as_str) {
                    set_last_output(weak.clone(), output);
                    set_guide(
                        weak.clone(),
                        &format!("Render finished: {output}. Use Open File to play, Open Folder to inspect."),
                    );
                }
            }
            Some("voices") => {
                let provider = value
                    .get("provider")
                    .and_then(Value::as_str)
                    .unwrap_or("tts");
                let voice_count = value
                    .get("voices")
                    .and_then(Value::as_array)
                    .map(|items| items.len())
                    .unwrap_or(0);
                let voices = value
                    .get("voices")
                    .and_then(Value::as_array)
                    .map(|items| {
                        items
                            .iter()
                            .map(|voice| {
                                let id = voice.get("id").and_then(Value::as_str).unwrap_or("");
                                let label =
                                    voice.get("label").and_then(Value::as_str).unwrap_or(id);
                                let locale =
                                    voice.get("locale").and_then(Value::as_str).unwrap_or("");
                                if locale.is_empty() {
                                    format!("{id} | {label}")
                                } else {
                                    format!("{id} | {label} | {locale}")
                                }
                            })
                            .collect::<Vec<_>>()
                            .join("\n")
                    })
                    .filter(|text| !text.is_empty())
                    .unwrap_or_else(|| "No voices returned.".to_string());
                if let Some(first_id) = value
                    .get("voices")
                    .and_then(Value::as_array)
                    .and_then(|items| items.first())
                    .and_then(|voice| voice.get("id"))
                    .and_then(Value::as_str)
                {
                    set_voice_name(weak.clone(), first_id);
                }
                set_voice_list(weak.clone(), &voices);
                set_engine_check(
                    weak.clone(),
                    &format!("Engine check OK: {provider} returned {voice_count} voices."),
                );
                set_guide(
                    weak.clone(),
                    "Voices loaded. Voice field was filled with the first voice. Use Previous/Next Voice to compare candidates.",
                );
            }
            Some("audio_cpp_health") => {
                let healthy = value
                    .get("healthy")
                    .and_then(Value::as_bool)
                    .unwrap_or(false);
                let executable = value
                    .get("executable")
                    .and_then(Value::as_str)
                    .unwrap_or("");
                let issues = value
                    .get("issues")
                    .and_then(Value::as_array)
                    .map(|items| {
                        items
                            .iter()
                            .filter_map(Value::as_str)
                            .collect::<Vec<_>>()
                            .join("; ")
                    })
                    .unwrap_or_default();
                let hints = json_string_list(&value, "hints");
                let families = json_string_vec(&value, "tts_families");
                let family_hint = if families.is_empty() {
                    "No audio.cpp TTS families reported. Check executable path and build."
                        .to_string()
                } else {
                    format!(
                        "Available audio.cpp families: {}. Use one in Family; known TTS defaults are pocket_tts or qwen3_tts.",
                        families.join(", ")
                    )
                };
                set_audio_family_hint(weak.clone(), &family_hint);
                let suggested_family = preferred_audio_cpp_family(&families).map(str::to_string);
                if let Some(family) = suggested_family.as_deref() {
                    set_audio_family_if_empty(weak.clone(), family);
                }
                if healthy {
                    set_engine_check(
                        weak.clone(),
                        &format!("Engine check OK: audio.cpp ready ({executable})"),
                    );
                    set_audio_status(
                        weak.clone(),
                        &format!("audio.cpp: local config OK ({executable})"),
                    );
                    if hints.is_empty() {
                        set_guide(
                            weak.clone(),
                            "audio.cpp local health OK. Render sample next.",
                        );
                    } else {
                        set_guide(
                            weak.clone(),
                            &format!(
                                "audio.cpp local health OK. Render sample next.\n\nHints:\n{hints}"
                            ),
                        );
                    }
                } else {
                    let detail = if issues.is_empty() {
                        "audio.cpp local config failed".to_string()
                    } else {
                        issues
                    };
                    set_engine_check(weak.clone(), &format!("Engine check failed: {detail}"));
                    set_audio_status(weak.clone(), &format!("audio.cpp: {detail}"));
                    if let Some(family) = suggested_family.as_deref() {
                        let hint_block = if hints.is_empty() {
                            String::new()
                        } else {
                            format!("\n\nHints:\n{hints}")
                        };
                        set_guide(
                            weak.clone(),
                            &format!(
                                "Fix audio.cpp config: {detail}\n\nSuggested family filled if empty: {family}. Click Check audio.cpp again after model/family are set.{hint_block}"
                            ),
                        );
                    } else if hints.is_empty() {
                        set_guide(weak.clone(), &format!("Fix audio.cpp config: {detail}"));
                    } else {
                        set_guide(
                            weak.clone(),
                            &format!("Fix audio.cpp config: {detail}\n\nHints:\n{hints}"),
                        );
                    }
                }
            }
            Some("cleanup_profiles") => {
                let profiles = value
                    .get("profiles")
                    .and_then(Value::as_array)
                    .map(|items| {
                        items
                            .iter()
                            .map(|profile| {
                                let name = profile
                                    .get("name")
                                    .and_then(Value::as_str)
                                    .unwrap_or("standard");
                                let config = profile
                                    .get("config_json")
                                    .and_then(Value::as_str)
                                    .unwrap_or("{}");
                                format!("{name} | {config}")
                            })
                            .collect::<Vec<_>>()
                            .join("\n")
                    })
                    .filter(|text| !text.is_empty())
                    .unwrap_or_else(|| "No cleanup profiles returned.".to_string());
                if let Some(first_name) = value
                    .get("profiles")
                    .and_then(Value::as_array)
                    .and_then(|items| items.first())
                    .and_then(|profile| profile.get("name"))
                    .and_then(Value::as_str)
                {
                    set_cleanup_profile_name(weak.clone(), first_name);
                }
                set_cleanup_profiles(weak.clone(), &profiles);
                set_guide(
                    weak.clone(),
                    "Cleanup profiles loaded. Pick one, then Apply + Rechunk.",
                );
            }
            Some("calibre_diagnostic") => {
                let healthy = value
                    .get("healthy")
                    .and_then(Value::as_bool)
                    .unwrap_or(false);
                let library = value
                    .get("calibre_library")
                    .and_then(Value::as_str)
                    .unwrap_or("");
                let calibredb = value
                    .get("calibredb")
                    .and_then(Value::as_str)
                    .unwrap_or("missing");
                let metadata = value
                    .get("metadata_db_exists")
                    .and_then(Value::as_bool)
                    .unwrap_or(false);
                let sample_count = value
                    .get("sample_count")
                    .and_then(Value::as_i64)
                    .map(|count| count.to_string())
                    .unwrap_or_else(|| "unknown".to_string());
                let suggested = value
                    .get("suggested_library")
                    .and_then(Value::as_str)
                    .unwrap_or("");
                let candidate_paths = json_string_vec(&value, "candidate_libraries");
                let source_candidate_paths = json_string_vec(&value, "source_file_candidates");
                let candidate_suggestion = calibre_suggested_path(suggested, &candidate_paths);
                let source_suggestion = if source_candidate_paths.is_empty() {
                    String::new()
                } else {
                    library.to_string()
                };
                set_calibre_suggested_path(weak.clone(), &candidate_suggestion);
                set_source_suggested_path(weak.clone(), &source_suggestion);
                let candidates = candidate_paths.join("\n");
                let source_candidates = source_candidate_paths.join("\n");
                let issues = json_string_list(&value, "issues");
                let hints = json_string_list(&value, "hints");
                let first_issue = issues.lines().next().unwrap_or("");
                let next_action = calibre_action_text(
                    healthy,
                    &candidate_suggestion,
                    &source_suggestion,
                    first_issue,
                );
                let detail = if healthy {
                    format!(
                        "Calibre OK\nLibrary: {library}\nmetadata.db: {metadata}\ncalibredb: {calibredb}\nSample scan: {sample_count} book(s)"
                    )
                } else {
                    let suggestion = if !suggested.is_empty() {
                        format!("\nSuggested library:\n{suggested}")
                    } else {
                        String::new()
                    };
                    let candidates = if !candidates.is_empty() {
                        format!("\nCandidate libraries:\n{candidates}")
                    } else {
                        String::new()
                    };
                    let source_candidates = if !source_candidates.is_empty() {
                        format!("\nSupported source files found:\n{source_candidates}")
                    } else {
                        String::new()
                    };
                    format!(
                        "Calibre problem\nLibrary: {library}\nmetadata.db: {metadata}\ncalibredb: {calibredb}{suggestion}{candidates}{source_candidates}\n\nIssues:\n{issues}\n\nHints:\n{hints}"
                    )
                };
                set_calibre_preview(weak.clone(), &detail);
                set_calibre_action(weak.clone(), &next_action);
                if healthy {
                    set_guide(
                        weak.clone(),
                        "Calibre path looks valid. Scan/import can continue.",
                    );
                } else {
                    set_guide(weak.clone(), &format!("Fix Calibre setup: {}", next_action));
                }
            }
            Some("source_probe") => {
                let kind = value
                    .get("kind")
                    .and_then(Value::as_str)
                    .unwrap_or("source");
                let summary = source_probe_summary(&value);
                set_source_probe(weak.clone(), &summary);
                set_guide(
                    weak.clone(),
                    if kind == "folder" {
                        "Source folder probed. Review supported files, then Import Source."
                    } else {
                        "Source file probed. Review metadata and chapter sizes, then Import Source."
                    },
                );
            }
            Some("outputs") => {
                let outputs_text = value
                    .get("outputs")
                    .and_then(Value::as_array)
                    .map(|items| {
                        items
                            .iter()
                            .take(12)
                            .map(|output| {
                                let format =
                                    output.get("format").and_then(Value::as_str).unwrap_or("");
                                let created = output
                                    .get("created_at")
                                    .and_then(Value::as_str)
                                    .unwrap_or("");
                                let path = output.get("path").and_then(Value::as_str).unwrap_or("");
                                format!("{format} | {created} | {path}")
                            })
                            .collect::<Vec<_>>()
                            .join("\n")
                    })
                    .filter(|text| !text.is_empty())
                    .unwrap_or_else(|| {
                        "No outputs for this book yet. Render TTS Test or Render Sample first."
                            .to_string()
                    });
                set_output_list(weak.clone(), &outputs_text);
                if let Some(path) = value
                    .get("outputs")
                    .and_then(Value::as_array)
                    .and_then(|items| items.first())
                    .and_then(|output| output.get("path"))
                    .and_then(Value::as_str)
                {
                    set_last_output(weak.clone(), path);
                    set_guide(
                        weak.clone(),
                        "Outputs loaded. Open File plays newest output; Open Folder opens its folder.",
                    );
                }
            }
            Some("tts_test") => {
                let provider = value
                    .get("provider")
                    .and_then(Value::as_str)
                    .unwrap_or("tts");
                let chars = value.get("chars").and_then(Value::as_i64).unwrap_or(0);
                if let Some(output) = value.get("output").and_then(Value::as_str) {
                    set_last_output(weak.clone(), output);
                    set_guide(
                        weak.clone(),
                        &format!(
                            "TTS test rendered with {provider} ({chars} chars). Use Open File to play it."
                        ),
                    );
                }
            }
            Some("diagnostic") => {
                let ffmpeg = value
                    .get("ffmpeg")
                    .and_then(Value::as_str)
                    .unwrap_or("missing");
                let ffprobe = value
                    .get("ffprobe")
                    .and_then(Value::as_str)
                    .unwrap_or("missing");
                let calibredb = value
                    .get("calibredb")
                    .and_then(Value::as_str)
                    .unwrap_or("missing");
                let sapi = value
                    .get("windows_sapi")
                    .and_then(Value::as_bool)
                    .unwrap_or(false);
                let piper = value.get("piper").and_then(Value::as_bool).unwrap_or(false);
                let piper_exe = value
                    .get("piper_executable")
                    .and_then(Value::as_str)
                    .unwrap_or("missing");
                set_diagnostics(
                    weak.clone(),
                    &format!("ffmpeg: {ffmpeg}\nffprobe: {ffprobe}\ncalibredb: {calibredb}\nWindows SAPI: {sapi}\nPiper: {piper}\nPiper exe: {piper_exe}"),
                );
                set_guide(
                    weak.clone(),
                    if piper {
                        prefer_piper_engine(weak.clone());
                        "Diagnostics found Piper. Choose Piper local voices, discover voices, then render a sample."
                    } else if sapi {
                        "Diagnostics OK enough for Windows SAPI render. Import a source or scan Calibre."
                    } else {
                        "Windows SAPI unavailable. Configure audio.cpp before rendering."
                    },
                );
            }
            Some("books") => {
                let loaded_ids = value
                    .get("books")
                    .and_then(Value::as_array)
                    .map(|items| {
                        items
                            .iter()
                            .filter_map(|book| book.get("id").and_then(Value::as_str))
                            .map(str::to_string)
                            .collect::<Vec<_>>()
                    })
                    .unwrap_or_default();
                let loaded_count = loaded_ids.len();
                {
                    *book_ids.lock().expect("book ids lock") = loaded_ids;
                    *book_index.lock().expect("book index lock") = 0;
                }
                let books = value
                    .get("books")
                    .and_then(Value::as_array)
                    .map(|items| {
                        items
                            .iter()
                            .map(|book| {
                                let id = book.get("id").and_then(Value::as_str).unwrap_or("");
                                let author =
                                    book.get("author").and_then(Value::as_str).unwrap_or("");
                                let title = book.get("title").and_then(Value::as_str).unwrap_or("");
                                let chunks =
                                    book.get("chunk_count").and_then(Value::as_i64).unwrap_or(0);
                                format!("{id} | {author} | {title} | {chunks} chunks")
                            })
                            .collect::<Vec<_>>()
                            .join("\n")
                    })
                    .filter(|text| !text.is_empty())
                    .unwrap_or_else(|| {
                        "No books in this BookCast library yet. Import a source file/folder or scan Calibre, then Refresh Books.".to_string()
                    });
                if let Some(first_id) = value
                    .get("books")
                    .and_then(Value::as_array)
                    .and_then(|items| items.first())
                    .and_then(|book| book.get("id"))
                    .and_then(Value::as_str)
                {
                    set_book_id_if_empty(weak.clone(), first_id);
                }
                set_books(weak.clone(), &books);
                if loaded_count == 0 {
                    set_book_selection(
                        weak.clone(),
                        "No books available yet. Import a source or scan/import Calibre first.",
                    );
                    set_guide(
                        weak.clone(),
                        "No books found in this BookCast library. Open Import Wizard next.",
                    );
                } else {
                    set_book_selection(
                        weak.clone(),
                        &format!("{loaded_count} books loaded. Use Previous/Next Book to switch without copying IDs."),
                    );
                    set_guide(
                        weak.clone(),
                        "Books loaded. First book id is selected automatically if the field was empty.",
                    );
                }
            }
            Some("chapter_detail") => {
                let index = value
                    .get("chapter_index")
                    .and_then(Value::as_i64)
                    .unwrap_or(0)
                    .to_string();
                let title = value.get("title").and_then(Value::as_str).unwrap_or("");
                let text = value.get("text").and_then(Value::as_str).unwrap_or("");
                set_chapter_edit_index(weak.clone(), &index);
                set_chapter_edit_title(weak.clone(), title);
                set_chapter_edit_text(weak.clone(), text);
                set_current_view(weak.clone(), 2);
                set_guide(weak.clone(), "Chapter loaded. Edit, then Save + Rechunk.");
            }
            Some("chapter_updated") => {
                let index = value
                    .get("chapter_index")
                    .and_then(Value::as_i64)
                    .unwrap_or(0);
                set_current_view(weak.clone(), 2);
                set_guide(
                    weak.clone(),
                    &format!("Chapter {index} saved. Preview refreshes with new chunks."),
                );
            }
            Some("book_preview") => {
                let book = value.get("book").unwrap_or(&Value::Null);
                let title = book.get("title").and_then(Value::as_str).unwrap_or("");
                let author = book.get("author").and_then(Value::as_str).unwrap_or("");
                let preview_context = value
                    .get("preview_context")
                    .and_then(Value::as_str)
                    .unwrap_or("");
                if let Some(profile) = book.get("cleanup_profile").and_then(Value::as_str) {
                    set_cleanup_profile_name(weak.clone(), profile);
                }
                let chunk_count = value
                    .get("chunk_count")
                    .and_then(Value::as_i64)
                    .unwrap_or(0);
                let chapters = value
                    .get("chapters")
                    .and_then(Value::as_array)
                    .map(|items| {
                        items
                            .iter()
                            .take(12)
                            .map(|chapter| {
                                let index =
                                    chapter.get("index").and_then(Value::as_i64).unwrap_or(0);
                                let title =
                                    chapter.get("title").and_then(Value::as_str).unwrap_or("");
                                let chars =
                                    chapter.get("chars").and_then(Value::as_i64).unwrap_or(0);
                                format!("{index}: {title} ({chars} chars)")
                            })
                            .collect::<Vec<_>>()
                            .join("\n")
                    })
                    .unwrap_or_default();
                let chunks = value
                    .get("chunks")
                    .and_then(Value::as_array)
                    .map(|items| {
                        items
                            .iter()
                            .take(12)
                            .map(|chunk| {
                                let chapter = chunk
                                    .get("chapter_index")
                                    .and_then(Value::as_i64)
                                    .unwrap_or(0);
                                let index = chunk
                                    .get("chunk_index")
                                    .and_then(Value::as_i64)
                                    .unwrap_or(0);
                                let chars = chunk.get("chars").and_then(Value::as_i64).unwrap_or(0);
                                let hash =
                                    chunk.get("text_hash").and_then(Value::as_str).unwrap_or("");
                                let status =
                                    chunk.get("status").and_then(Value::as_str).unwrap_or("");
                                let preview =
                                    chunk.get("preview").and_then(Value::as_str).unwrap_or("");
                                format!(
                                    "c{chapter}.{index} | {chars} chars | {} | {status}\n{preview}",
                                    short_hash(hash)
                                )
                            })
                            .collect::<Vec<_>>()
                            .join("\n\n")
                    })
                    .filter(|text| !text.is_empty())
                    .unwrap_or_else(|| "No chunks generated.".to_string());
                if preview_context != "update_chapter" {
                    if let Some(first_chapter) = value
                        .get("chapters")
                        .and_then(Value::as_array)
                        .and_then(|items| items.first())
                    {
                        let index = first_chapter
                            .get("index")
                            .and_then(Value::as_i64)
                            .unwrap_or(0)
                            .to_string();
                        let title = first_chapter
                            .get("title")
                            .and_then(Value::as_str)
                            .unwrap_or("");
                        set_chapter_edit_index(weak.clone(), &index);
                        set_chapter_edit_title(weak.clone(), title);
                        set_chapter_edit_text(weak.clone(), "");
                    }
                }
                let preview = value.get("preview").and_then(Value::as_str).unwrap_or("");
                set_book_preview(
                    weak.clone(),
                    &format!(
                        "{author} - {title}\n{chunk_count} chunks\n\nChapters\n{chapters}\n\nChunks\n{chunks}\n\nText Preview\n{preview}"
                    ),
                );
                if preview_context == "update_chapter" {
                    set_current_view(weak.clone(), 2);
                    set_guide(
                        weak.clone(),
                        "Chapter saved and rechunked. Review chunks, then render sample.",
                    );
                } else {
                    set_current_view(weak.clone(), 0);
                    set_guide(
                        weak.clone(),
                        "Preview loaded. Render sample before full render.",
                    );
                }
            }
            Some("calibre_books") => {
                let books = value.get("books").and_then(Value::as_array);
                let count = books.map_or(0, Vec::len);
                let skipped = value.get("skipped").and_then(Value::as_i64).unwrap_or(0);
                let selected_ids = books
                    .map(|items| {
                        items
                            .iter()
                            .take(20)
                            .filter_map(|book| book.get("id").and_then(Value::as_str))
                            .collect::<Vec<_>>()
                            .join(", ")
                    })
                    .unwrap_or_default();
                let preview = books
                    .map(|items| {
                        items
                            .iter()
                            .take(20)
                            .map(|book| {
                                let id = book.get("id").and_then(Value::as_str).unwrap_or("");
                                let authors =
                                    book.get("authors").and_then(Value::as_str).unwrap_or("");
                                let title = book.get("title").and_then(Value::as_str).unwrap_or("");
                                let formats = book
                                    .get("formats")
                                    .and_then(Value::as_array)
                                    .map(|items| {
                                        items
                                            .iter()
                                            .filter_map(Value::as_str)
                                            .collect::<Vec<_>>()
                                            .join(",")
                                    })
                                    .unwrap_or_default();
                                format!("{id} | {authors} | {title} | {formats}")
                            })
                            .collect::<Vec<_>>()
                            .join("\n")
                    })
                    .filter(|text| !text.is_empty())
                    .unwrap_or_else(|| "No importable Calibre books found.".to_string());
                let preview = if selected_ids.is_empty() {
                    preview
                } else {
                    format!("IDs selected for import: {selected_ids}\n\n{preview}")
                };
                set_calibre_preview(weak.clone(), &preview);
                if !selected_ids.is_empty() {
                    set_calibre_ids(weak.clone(), &selected_ids);
                }
                set_guide(
                    weak.clone(),
                    &format!("Calibre scan found {count} importable books, skipped {skipped}. Calibre IDs now contains visible books; remove IDs you do not want, then import."),
                );
                set_calibre_action(
                    weak.clone(),
                    "Scan complete. Next: review Calibre IDs, then click Import Calibre IDs.",
                );
            }
            Some("calibre_imported") => {
                let title = value.get("title").and_then(Value::as_str).unwrap_or("");
                let book_id = value.get("book_id").and_then(Value::as_str).unwrap_or("");
                if !book_id.is_empty() {
                    set_book_id(weak.clone(), book_id);
                    set_current_view(weak.clone(), 0);
                }
                set_guide(
                    weak.clone(),
                    &format!("Imported from Calibre: {title}. Book id filled for render."),
                );
                set_calibre_action(
                    weak.clone(),
                    "Import complete. Next: open Library to inspect chapters, or TTS Studio to render a sample.",
                );
            }
            Some("characters") => {
                let candidates = value.get("candidates").and_then(Value::as_array);
                let text = value
                    .get("candidates")
                    .and_then(Value::as_array)
                    .map(|items| {
                        items
                            .iter()
                            .map(character_candidate_line)
                            .collect::<Vec<_>>()
                            .join("\n")
                    })
                    .filter(|text| !text.is_empty())
                    .unwrap_or_else(|| "No character candidates returned.".to_string());
                let voice_template = character_voice_template(candidates);
                let review_text = character_review_text(candidates);
                set_character_text(weak.clone(), &text);
                if !voice_template.is_empty() {
                    set_speaker_voice_map(weak.clone(), &voice_template);
                    set_speaker_voices_confirmed(weak.clone(), false);
                }
                set_character_review_text(weak.clone(), &review_text);
                set_guide(
                    weak.clone(),
                    "Character candidates loaded. Review/delete false positives, assign voices, then tick confirmation.",
                );
            }
            Some("podcast_script") => {
                let script = value.get("script").unwrap_or(&Value::Null);
                let speaker_template = podcast_speaker_template(script);
                set_podcast_text(weak.clone(), &podcast_script_preview_text(script));
                if let Ok(pretty) = serde_json::to_string_pretty(script) {
                    set_podcast_script_json(weak.clone(), &pretty);
                }
                if let Some(path) = value.get("path").and_then(Value::as_str) {
                    if !speaker_template.is_empty() {
                        set_speaker_voice_map(weak.clone(), &speaker_template);
                        set_speaker_voices_confirmed(weak.clone(), false);
                    }
                    set_podcast_script_path(weak.clone(), path);
                    set_podcast_review_text(weak.clone(), &podcast_review_text(script, Some(path)));
                    set_guide(weak.clone(), &format!("Podcast script saved: {path}"));
                } else if let Some(output) = value.get("output").and_then(Value::as_str) {
                    set_last_output(weak.clone(), output);
                    set_podcast_review_text(
                        weak.clone(),
                        &podcast_review_text(script, Some(output)),
                    );
                    set_guide(
                        weak.clone(),
                        &format!("Podcast rendered: {output}. Use Open File to play, Open Folder to inspect."),
                    );
                }
            }
            Some("interactive_turn") => {
                let turn = value.get("turn").and_then(Value::as_i64).unwrap_or(0);
                let total = value.get("total").and_then(Value::as_i64).unwrap_or(0);
                let speaker = value
                    .get("speaker")
                    .and_then(Value::as_str)
                    .unwrap_or("host");
                let text = value.get("text").and_then(Value::as_str).unwrap_or("");
                let follow_up = value.get("follow_up").and_then(Value::as_str).unwrap_or("");
                let line = if follow_up.is_empty() {
                    format!("{turn}/{total} {speaker}: {text}")
                } else {
                    format!("{turn}/{total} {speaker}: {text}\nNext: {follow_up}")
                };
                append_podcast_text(weak.clone(), &line);
            }
            Some("interactive_podcast") => {
                if let Some(output) = value.get("output").and_then(Value::as_str) {
                    set_last_output(weak.clone(), output);
                    set_guide(
                        weak.clone(),
                        &format!(
                            "Interactive podcast rendered: {output}. Use Open File to play it."
                        ),
                    );
                }
            }
            Some("error") => {
                if let Some(message) = value.get("message").and_then(Value::as_str) {
                    update_job(weak.clone(), jobs.clone(), job_id, "failed", 100, message);
                    set_guide(weak.clone(), &bridge_recovery_text(message));
                }
            }
            _ => {}
        }
    }
}

fn push_log(weak: slint::Weak<AppWindow>, line: &str) {
    let line = line.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            let current = app.get_queue_text().to_string();
            let next = if current == "Queue idle." {
                format!("System\n  {line}")
            } else {
                format!("{current}\n\nSystem\n  {line}")
            };
            app.set_queue_text(next.into());
        }
    });
}

fn set_status(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_status_text(text.into());
        }
    });
}

fn set_diagnostics(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let refresh_weak = weak.clone();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_diagnostic_text(text.into());
        }
    });
    refresh_readiness(refresh_weak);
}

fn set_books(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_books_text(text.into());
        }
    });
}

fn set_book_selection(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_book_selection_text(text.into());
        }
    });
}

fn set_book_preview(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_book_preview_text(text.into());
        }
    });
}

fn set_cleanup_profiles(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_cleanup_profiles_text(text.into());
        }
    });
}

fn set_cleanup_profile_name(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_cleanup_profile_name(text.into());
        }
    });
}

fn set_chapter_edit_index(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_chapter_edit_index(text.into());
        }
    });
}

fn set_chapter_edit_title(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_chapter_edit_title(text.into());
        }
    });
}

fn set_chapter_edit_text(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_chapter_edit_text(text.into());
        }
    });
}

fn set_character_text(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_character_text(text.into());
        }
    });
}

fn set_character_review_text(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_character_review_text(text.into());
        }
    });
}

fn set_podcast_text(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_podcast_text(text.into());
        }
    });
}

fn set_podcast_review_text(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_podcast_review_text(text.into());
        }
    });
}

fn set_podcast_script_path(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_podcast_script_path(text.into());
        }
    });
}

fn set_podcast_script_json(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_podcast_script_json(text.into());
        }
    });
}

fn set_speaker_voice_map(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_speaker_voice_map(text.into());
        }
    });
}

fn set_speaker_voices_confirmed(weak: slint::Weak<AppWindow>, confirmed: bool) {
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_speaker_voices_confirmed(confirmed);
        }
    });
}

fn append_podcast_text(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            let current = app.get_podcast_text().to_string();
            let next = if current.starts_with("Generate a script first.") {
                text
            } else {
                format!("{current}\n{text}")
            };
            app.set_podcast_text(next.into());
        }
    });
}

fn set_voice_list(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_voice_list_text(text.into());
        }
    });
}

fn set_voice_name(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_voice_name(text.into());
        }
    });
}

fn set_last_output(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let refresh_weak = weak.clone();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_last_output_path(text.into());
        }
    });
    refresh_readiness(refresh_weak);
}

fn set_output_list(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_output_list_text(text.into());
        }
    });
}

fn set_guide(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_guide_text(text.into());
        }
    });
}

fn set_book_id(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let refresh_weak = weak.clone();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_book_id(text.into());
        }
    });
    refresh_readiness(refresh_weak);
}

fn set_current_view(weak: slint::Weak<AppWindow>, view: i32) {
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_current_view(view);
        }
    });
}

fn set_book_id_if_empty(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let refresh_weak = weak.clone();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            if app.get_book_id().to_string().trim().is_empty() {
                app.set_book_id(text.into());
            }
        }
    });
    refresh_readiness(refresh_weak);
}

fn prefer_piper_engine(weak: slint::Weak<AppWindow>) {
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            if app.get_engine_index() == 0 && app.get_voice_name().to_string().trim().is_empty() {
                app.set_engine_index(1);
            }
        }
    });
}

fn set_calibre_ids(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_calibre_ids(text.into());
        }
    });
}

fn set_calibre_suggested_path(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_calibre_suggested_path(text.into());
        }
    });
}

fn set_source_suggested_path(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_source_suggested_path(text.into());
        }
    });
}

fn set_calibre_action(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_calibre_action_text(text.into());
        }
    });
}

fn set_source_probe(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_source_probe_text(text.into());
        }
    });
}

fn set_calibre_preview(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_calibre_preview_text(text.into());
        }
    });
}

fn set_audio_status(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_audio_cpp_status(text.into());
        }
    });
}

fn set_audio_family_hint(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_audio_cpp_family_hint(text.into());
        }
    });
}

fn set_audio_family_if_empty(weak: slint::Weak<AppWindow>, family: &str) {
    let family = family.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            if app.get_audio_cpp_family().to_string().trim().is_empty() {
                app.set_audio_cpp_family(family.into());
            }
        }
    });
}

fn set_engine_check(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let refresh_weak = weak.clone();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_engine_check_text(text.into());
            app.set_engine_setup_text(engine_setup_text(&app).into());
        }
    });
    refresh_readiness(refresh_weak);
}

#[cfg(test)]
mod tests {
    use std::path::PathBuf;

    use serde_json::json;

    use super::audio_cpp_update_status;
    use super::bridge_recovery_text;
    use super::calibre_action_text;
    use super::calibre_suggested_path;
    use super::calibredb_args_from;
    use super::character_candidate_line;
    use super::character_review_text;
    use super::character_voice_template;
    use super::confirmed_voice_entries_from;
    use super::engine_setup_text_from;
    use super::eta_label;
    use super::format_elapsed_ms;
    use super::import_done_detail;
    use super::job_progress_detail;
    use super::job_queue_line;
    use super::media_tool_args_from;
    use super::optional_positive_limit_problem;
    use super::optional_voice_entries_from;
    use super::output_open_target;
    use super::parse_chapter_index;
    use super::podcast_preset;
    use super::podcast_review_text;
    use super::podcast_script_preview_text;
    use super::podcast_speaker_template;
    use super::preferred_audio_cpp_family;
    use super::progress_bar;
    use super::queue_action;
    use super::queue_summary;
    use super::render_preflight_problem_from;
    use super::setup_checklist;
    use super::source_probe_summary;
    use super::split_ids;
    use super::tts_test_preflight_problem_from;
    use super::validate_podcast_script_json;
    use super::voice_choice_from_list;
    use super::voice_ids_from_list;
    use super::workbench_readiness;
    use super::JobState;
    use super::VoiceChoice;

    #[test]
    fn render_preflight_requires_book_id() {
        assert_eq!(
            render_preflight_problem_from("", "opus", "", "", 0, "", "", "", "", "", "").as_deref(),
            Some("Render needs a book id. Import a book or click Refresh Books.")
        );
    }

    #[test]
    fn render_preflight_rejects_unknown_output_format() {
        assert_eq!(
            render_preflight_problem_from("book-1", "flac", "", "", 0, "", "", "", "", "", "")
                .as_deref(),
            Some("Output must be opus, mp3, wav, or m4b.")
        );
    }

    #[test]
    fn render_preflight_requires_audio_cpp_model() {
        assert_eq!(
            render_preflight_problem_from(
                "book-1",
                "opus",
                "",
                "",
                2,
                "",
                "",
                "audiocpp_cli",
                "",
                "cpu",
                ""
            )
            .as_deref(),
            Some("audio.cpp selected, but model is missing. Set audio.cpp model before rendering.")
        );
    }

    #[test]
    fn tts_test_preflight_reuses_engine_checks() {
        assert_eq!(
            tts_test_preflight_problem_from("", 0, "", "", "", "", "", "").as_deref(),
            Some("TTS test needs text.")
        );
        assert_eq!(
            tts_test_preflight_problem_from("hello", 1, "", "", "", "", "", "").as_deref(),
            Some("Piper selected, but Piper executable is missing. Run Diagnose or set Piper executable.")
        );
        assert_eq!(
            tts_test_preflight_problem_from("hello", 2, "", "", "", "model", "cpu", "").as_deref(),
            Some("audio.cpp selected, but executable is missing. Build audio.cpp or set audiocpp_cli.exe.")
        );
        assert_eq!(
            tts_test_preflight_problem_from("hello", 2, "", "", "audiocpp_cli", "", "cpu", "")
                .as_deref(),
            Some("audio.cpp selected, but model is missing. Set audio.cpp model before rendering.")
        );
        assert_eq!(
            tts_test_preflight_problem_from("hello", 2, "", "", "audiocpp_cli", "model", "cpu", ""),
            Some(
                "audio.cpp selected, but family is missing. Set audio.cpp family, e.g. pocket_tts or qwen3_tts."
                    .to_string()
            )
        );
        assert_eq!(
            tts_test_preflight_problem_from(
                "hello",
                2,
                "",
                "",
                "audiocpp_cli",
                "model",
                "cpu",
                "pocket_tts"
            ),
            None
        );
    }

    #[test]
    fn podcast_presets_fill_focus_and_style() {
        let (focus, style) = podcast_preset(0);
        assert!(focus.contains("core concepts"));
        assert!(style.contains("learners"));

        let (focus, style) = podcast_preset(1);
        assert!(focus.contains("counterarguments"));
        assert!(style.contains("fact-checking"));

        let (focus, style) = podcast_preset(2);
        assert!(focus.contains("author intent"));
        assert!(style.contains("follow-up"));
    }

    #[test]
    fn render_preflight_rejects_missing_path_like_engine_files() {
        assert_eq!(
            render_preflight_problem_from(
                "book-1",
                "opus",
                "D:\\missing\\ffmpeg.exe",
                "",
                0,
                "",
                "",
                "",
                "",
                "",
                ""
            )
            .as_deref(),
            Some("ffmpeg executable path not found: D:\\missing\\ffmpeg.exe")
        );
        assert_eq!(
            render_preflight_problem_from(
                "book-1",
                "m4b",
                "",
                "D:\\missing\\ffprobe.exe",
                0,
                "",
                "",
                "",
                "",
                "",
                ""
            )
            .as_deref(),
            Some("ffprobe executable path not found: D:\\missing\\ffprobe.exe")
        );
        assert_eq!(
            render_preflight_problem_from(
                "book-1",
                "opus",
                "",
                "",
                2,
                "",
                "",
                "D:\\missing\\audiocpp_cli.exe",
                "model",
                "cpu",
                "pocket_tts"
            )
            .as_deref(),
            Some("audio.cpp executable path not found: D:\\missing\\audiocpp_cli.exe")
        );
        assert_eq!(
            render_preflight_problem_from(
                "book-1",
                "opus",
                "",
                "",
                2,
                "",
                "",
                "audiocpp_cli",
                "D:\\missing\\model.gguf",
                "cpu",
                "pocket_tts"
            )
            .as_deref(),
            Some("audio.cpp model path not found: D:\\missing\\model.gguf")
        );
        assert_eq!(
            render_preflight_problem_from(
                "book-1",
                "opus",
                "",
                "",
                2,
                "",
                "",
                "audiocpp_cli",
                "model",
                "",
                "pocket_tts"
            )
            .as_deref(),
            Some("audio.cpp selected, but backend is empty. Use cpu unless you know another backend is available.")
        );
    }

    #[test]
    fn bridge_recovery_text_names_next_fix_for_common_tool_errors() {
        assert!(bridge_recovery_text("FileNotFoundError: ffmpeg not found")
            .contains("set ffmpeg executable"));
        assert!(bridge_recovery_text("ffprobe: no such file").contains("set ffprobe executable"));
        assert!(bridge_recovery_text("calibredb not found").contains("set calibredb executable"));
        assert!(bridge_recovery_text("metadata.db not found in D:\\Books")
            .contains("directly contains metadata.db"));
        assert!(
            bridge_recovery_text("audio.cpp family qwen3_tts failed").contains("Check audio.cpp")
        );
        assert!(bridge_recovery_text("Ollama connection refused").contains("Start Ollama"));
    }

    #[test]
    fn render_limit_accepts_empty_or_positive_integer() {
        assert_eq!(
            optional_positive_limit_problem("", "Render chunk limit"),
            None
        );
        assert_eq!(
            optional_positive_limit_problem("3", "Render chunk limit"),
            None
        );
        assert_eq!(
            optional_positive_limit_problem("0", "Render chunk limit").as_deref(),
            Some("Render chunk limit must be empty or a positive whole number.")
        );
        assert_eq!(
            optional_positive_limit_problem("abc", "Render chunk limit").as_deref(),
            Some("Render chunk limit must be empty or a positive whole number.")
        );
        assert_eq!(
            optional_positive_limit_problem("-1", "Calibre limit").as_deref(),
            Some("Calibre limit must be empty or a positive whole number.")
        );
    }

    #[test]
    fn chapter_index_accepts_zero_or_positive_integer() {
        assert_eq!(parse_chapter_index("0"), Ok(0));
        assert_eq!(parse_chapter_index(" 12 "), Ok(12));
        assert_eq!(
            parse_chapter_index(""),
            Err("Chapter index must be zero or a positive whole number.".to_string())
        );
        assert_eq!(
            parse_chapter_index("-1"),
            Err("Chapter index must be zero or a positive whole number.".to_string())
        );
    }

    #[test]
    fn split_ids_accepts_commas_semicolons_and_whitespace() {
        assert_eq!(
            split_ids("7, 8;9\n10"),
            vec![
                "7".to_string(),
                "8".to_string(),
                "9".to_string(),
                "10".to_string()
            ]
        );
    }

    #[test]
    fn confirmed_voice_entries_require_mapping_and_confirmation() {
        assert_eq!(
            confirmed_voice_entries_from("", true).unwrap_err(),
            "Speaker voice mapping is required before podcast rendering."
        );
        assert_eq!(
            confirmed_voice_entries_from("host=Narrator", false).unwrap_err(),
            "Review every speaker=voice assignment, then tick confirmation before rendering."
        );
        assert_eq!(
            confirmed_voice_entries_from("host=Narrator; explainer=Guest", true).unwrap(),
            vec!["host=Narrator".to_string(), "explainer=Guest".to_string()]
        );
        assert_eq!(
            optional_voice_entries_from("", false).unwrap(),
            Vec::<String>::new()
        );
        assert_eq!(
            optional_voice_entries_from("Ada=Ada Voice", false).unwrap_err(),
            "Review character speaker=voice assignments and tick confirmation before multi-voice audiobook rendering."
        );
        assert_eq!(
            optional_voice_entries_from("Ada=Ada Voice", true).unwrap(),
            vec!["Ada=Ada Voice".to_string()]
        );
    }

    #[test]
    fn audio_cpp_update_status_flags_remote_drift() {
        let pinned = "aaaaaaaaaaaabbbbbbbbbbbbccccccccccccdddddddd";
        let remote = "11111111111122222222222233333333333344444444";

        assert_eq!(
            audio_cpp_update_status(pinned, ""),
            "audio.cpp: remote returned no HEAD"
        );
        assert_eq!(
            audio_cpp_update_status(pinned, pinned),
            "audio.cpp: pinned aaaaaaaaaaaa is current"
        );
        assert_eq!(
            audio_cpp_update_status(pinned, remote),
            "audio.cpp: Update Available, pinned aaaaaaaaaaaa remote 111111111111"
        );
    }

    #[test]
    fn preferred_audio_cpp_family_uses_known_tts_families_only() {
        let families = vec![
            "qwen3_asr".to_string(),
            "pocket_tts".to_string(),
            "qwen3_tts".to_string(),
        ];
        assert_eq!(preferred_audio_cpp_family(&families), Some("pocket_tts"));

        let families = vec!["qwen3_asr".to_string(), "silero_vad".to_string()];
        assert_eq!(preferred_audio_cpp_family(&families), None);
    }

    #[test]
    fn calibre_suggested_path_prefers_direct_suggestion_then_first_candidate() {
        let candidates = vec!["D:\\Books\\Calibre Library".to_string()];
        assert_eq!(
            calibre_suggested_path("D:\\Books", &candidates),
            "D:\\Books"
        );
        assert_eq!(calibre_suggested_path("", &candidates), candidates[0]);
        assert_eq!(calibre_suggested_path("", &[]), "");
    }

    #[test]
    fn calibredb_args_only_pass_custom_executable_when_set() {
        assert_eq!(calibredb_args_from(""), Vec::<String>::new());
        assert_eq!(calibredb_args_from("  "), Vec::<String>::new());
        assert_eq!(
            calibredb_args_from("D:\\Tools\\Calibre2\\calibredb.exe"),
            vec![
                "--calibredb".to_string(),
                "D:\\Tools\\Calibre2\\calibredb.exe".to_string()
            ]
        );
    }

    #[test]
    fn media_tool_args_pass_custom_ffmpeg_and_ffprobe_when_set() {
        assert_eq!(media_tool_args_from("", "", true), Vec::<String>::new());
        assert_eq!(
            media_tool_args_from("D:\\Tools\\ffmpeg.exe", "D:\\Tools\\ffprobe.exe", true),
            vec![
                "--ffmpeg".to_string(),
                "D:\\Tools\\ffmpeg.exe".to_string(),
                "--ffprobe".to_string(),
                "D:\\Tools\\ffprobe.exe".to_string()
            ]
        );
        assert_eq!(
            media_tool_args_from("D:\\Tools\\ffmpeg.exe", "D:\\Tools\\ffprobe.exe", false),
            vec!["--ffmpeg".to_string(), "D:\\Tools\\ffmpeg.exe".to_string()]
        );
    }

    #[test]
    fn calibre_action_text_names_next_safe_action() {
        assert!(calibre_action_text(true, "", "", "").contains("Scan Calibre"));
        assert!(
            calibre_action_text(false, "D:\\Calibre", "", "metadata.db not found")
                .contains("Use suggested Calibre")
        );
        assert!(
            calibre_action_text(false, "", "D:\\Books", "metadata.db not found")
                .contains("Use as Source Folder")
        );
        assert!(
            calibre_action_text(false, "", "", "calibredb not found").contains("Install Calibre")
        );
        assert!(
            calibre_action_text(false, "", "", "metadata.db not found in: D:\\Books")
                .contains("folder containing metadata.db")
        );
    }

    #[test]
    fn source_probe_summary_formats_file_and_folder() {
        let file = source_probe_summary(&json!({
            "kind": "file",
            "source": "book.md",
            "format": "md",
            "title": "Book",
            "author": "Ada",
            "language": "en",
            "chars": 42,
            "chapter_count": 1,
            "chapters": [{"index": 0, "title": "Start", "chars": 42}],
            "preview": "Hello"
        }));
        assert!(file.contains("Ada - Book"));
        assert!(file.contains("0: Start (42 chars)"));

        let folder = source_probe_summary(&json!({
            "kind": "folder",
            "source": "sources",
            "supported_count": 2,
            "files": [{"format": "txt", "name": "One.txt"}],
            "truncated": true
        }));
        assert!(folder.contains("Supported files: 2"));
        assert!(folder.contains("txt | One.txt"));
        assert!(folder.contains("More files exist"));
    }

    #[test]
    fn character_candidates_seed_voice_review_template() {
        let candidates = vec![
            json!({"name": "Narrator", "role": "narrator", "evidence": "summary"}),
            json!({"name": "Ada", "role": "character", "evidence": "dialogue"}),
            json!({"name": "Ada", "role": "character", "evidence": "duplicate"}),
        ];

        assert_eq!(
            character_voice_template(Some(&candidates)),
            "Narrator=; Ada="
        );
        assert!(character_review_text(Some(&candidates)).contains("3 candidate(s)"));
        assert!(character_review_text(Some(&candidates)).contains("confidence/excerpts"));
        assert!(character_review_text(None).contains("No candidates"));
        assert_eq!(
            character_candidate_line(&json!({
                "name": "Ada",
                "role": "character",
                "evidence": "dialogue",
                "confidence": 0.82,
                "excerpt": "Ada said hello."
            })),
            "Ada | character | confidence 82% | dialogue | excerpt: Ada said hello."
        );
    }

    #[test]
    fn podcast_review_text_counts_speakers_and_explains_script_reuse() {
        let script = json!({
            "speakers": ["host", "explainer"],
            "turns": [
                {"speaker": "host", "text": "Welcome."},
                {"speaker": "explainer", "text": "Explanation."}
            ]
        });

        let review = podcast_review_text(&script, Some("D:\\out\\podcast.json"));
        assert!(review.contains("2 speaker(s), 2 turn(s)"));
        assert!(review.contains("Assign every speaker=voice"));
        assert!(review.contains("will reuse this reviewed script path"));
        assert!(review.contains("D:\\out\\podcast.json"));
    }

    #[test]
    fn podcast_script_preview_and_voice_template_use_saved_json() {
        let script = json!({
            "title": "Saved Cast",
            "summary": "Short.",
            "speakers": ["host", "expert"],
            "citations": ["Source-backed point."],
            "turns": [
                {"speaker": "host", "text": "Welcome."},
                {"speaker": "expert", "text": "Details."}
            ]
        });

        assert_eq!(podcast_speaker_template(&script), "host=; expert=");
        let preview = podcast_script_preview_text(&script);
        assert!(preview.contains("Saved Cast"));
        assert!(preview.contains("Speakers: host, expert"));
        assert!(preview.contains("Citations\n- Source-backed point."));
        assert!(preview.contains("expert: Details."));
    }

    #[test]
    fn podcast_script_editor_requires_valid_turns() {
        assert!(validate_podcast_script_json(
            r#"{"speakers":["host"],"turns":[{"speaker":"host","text":"Hi."}]}"#
        )
        .is_ok());
        assert_eq!(
            validate_podcast_script_json(r#"{"speakers":["host"],"turns":[]}"#).unwrap_err(),
            "script needs a non-empty turns array"
        );
        assert!(validate_podcast_script_json("not json")
            .unwrap_err()
            .contains("expected ident"));
    }

    #[test]
    fn output_open_target_can_open_file_or_parent_folder() {
        let path = r"C:\tmp\book.opus";
        assert_eq!(output_open_target(path, false), PathBuf::from(path));
        assert_eq!(output_open_target(path, true), PathBuf::from(r"C:\tmp"));
    }

    #[test]
    fn render_preflight_accepts_configured_piper() {
        assert_eq!(
            render_preflight_problem_from("book-1", "m4b", "", "", 1, "piper", "", "", "", "", ""),
            None
        );
    }

    #[test]
    fn job_progress_detail_uses_phase_and_counter() {
        assert_eq!(
            job_progress_detail(&json!({"phase":"tts","chunk":2,"total":5,"cached":false})),
            "tts 2/5 rendered"
        );
    }

    #[test]
    fn import_done_detail_counts_duplicate_reuse() {
        assert_eq!(
            import_done_detail(&json!({
                "job": "import",
                "imported": [
                    {"duplicate": false},
                    {"duplicate": true}
                ]
            }))
            .as_deref(),
            Some("Import done: 1 new, 1 duplicate(s) reused")
        );
        assert_eq!(
            import_done_detail(&json!({
                "job": "import",
                "imported": [
                    {"duplicate": false},
                    {"duplicate": false}
                ]
            }))
            .as_deref(),
            Some("Import done: 2 new book(s)")
        );
        assert_eq!(import_done_detail(&json!({"job": "render"})), None);
    }

    #[test]
    fn queue_summary_prefers_running_then_failed_then_last_done() {
        let jobs = vec![
            JobState {
                id: 1,
                label: "import".to_string(),
                status: "done".to_string(),
                progress: 100,
                detail: "book-1".to_string(),
                started_ms: 1_000,
                updated_ms: 2_000,
            },
            JobState {
                id: 2,
                label: "render".to_string(),
                status: "running".to_string(),
                progress: 42,
                detail: "tts 2/5 rendered".to_string(),
                started_ms: 1_000,
                updated_ms: 76_000,
            },
        ];
        assert_eq!(
            queue_summary(&jobs),
            "Running: render at 42% after 01:15 (ETA 01:43) | tts 2/5 rendered"
        );
        assert_eq!(
            queue_action(&jobs),
            "Queue action: wait for render or click Cancel. Current step: tts 2/5 rendered."
        );

        let failed = vec![JobState {
            id: 3,
            label: "calibre scan".to_string(),
            status: "failed".to_string(),
            progress: 100,
            detail: "metadata.db missing".to_string(),
            started_ms: 1_000,
            updated_ms: 2_000,
        }];
        assert_eq!(
            queue_summary(&failed),
            "Attention: calibre scan failed | metadata.db missing"
        );
        assert_eq!(
            queue_action(&failed),
            "Queue action: fix the issue, then Retry Last. Failed step: metadata.db missing."
        );

        let cancelled = vec![JobState {
            id: 4,
            label: "render".to_string(),
            status: "cancelled".to_string(),
            progress: 100,
            detail: "Cancel sent to process 123".to_string(),
            started_ms: 1_000,
            updated_ms: 2_000,
        }];
        assert_eq!(
            queue_summary(&cancelled),
            "Last cancelled: render | Cancel sent to process 123"
        );
        assert_eq!(
            queue_action(&cancelled),
            "Queue action: render was cancelled. Use Retry Last to resume from cached chunks when ready."
        );
    }

    #[test]
    fn queue_action_points_to_output_when_done() {
        let jobs = vec![JobState {
            id: 4,
            label: "render".to_string(),
            status: "done".to_string(),
            progress: 100,
            detail: "D:\\out\\book.opus".to_string(),
            started_ms: 1_000,
            updated_ms: 2_000,
        }];

        assert_eq!(
            queue_summary(&jobs),
            "Last done: render | D:\\out\\book.opus"
        );
        assert_eq!(
            queue_action(&jobs),
            "Queue action: output exists. Use Open File to play or Open Folder to inspect."
        );
    }

    #[test]
    fn job_queue_line_is_readable_progress_card() {
        let job = JobState {
            id: 123456,
            label: "render".to_string(),
            status: "running".to_string(),
            progress: 42,
            detail: "tts 2/5 rendered".to_string(),
            started_ms: 1_000,
            updated_ms: 76_000,
        };

        assert_eq!(progress_bar(42), "[####------]");
        assert_eq!(progress_bar(100), "[##########]");
        assert_eq!(format_elapsed_ms(75_000), "01:15");
        assert_eq!(eta_label(&job), "01:43");
        assert_eq!(
            job_queue_line(&job),
            "[####------]  42%  Running  render  elapsed 01:15  ETA 01:43\n  id #23456  tts 2/5 rendered"
        );
    }

    #[test]
    fn voice_picker_cycles_discovered_voice_ids() {
        let list = "voice-a | Alice | de_DE\nvoice-b | Bob | en_US\nvoice-c | Cara";

        assert_eq!(
            voice_ids_from_list(list),
            vec!["voice-a", "voice-b", "voice-c"]
        );
        assert_eq!(
            voice_choice_from_list(list, "", VoiceChoice::First).as_deref(),
            Some("voice-a")
        );
        assert_eq!(
            voice_choice_from_list(list, "voice-a", VoiceChoice::Next).as_deref(),
            Some("voice-b")
        );
        assert_eq!(
            voice_choice_from_list(list, "voice-a", VoiceChoice::Previous).as_deref(),
            Some("voice-c")
        );
        assert_eq!(
            voice_choice_from_list("No voices returned.", "", VoiceChoice::First),
            None
        );
    }

    #[test]
    fn workbench_readiness_guides_next_action() {
        assert_eq!(
            workbench_readiness("", 0, "", "", "No active jobs. Queue idle."),
            "Next: import a source or Refresh Books to select a book."
        );
        assert_eq!(
            workbench_readiness(
                "book-1",
                2,
                "Engine check: not run",
                "",
                "No active jobs. Queue idle."
            ),
            "Next: Check audio.cpp before rendering with audio.cpp."
        );
        assert_eq!(
            workbench_readiness(
                "book-1",
                1,
                "Engine check OK: piper returned 1 voices.",
                "",
                "No active jobs. Queue idle."
            ),
            "Ready for sample render. Full render after sample sounds acceptable."
        );
        assert_eq!(
            workbench_readiness(
                "book-1",
                1,
                "Engine check OK",
                "",
                "Running: render at 3% - started"
            ),
            "Running: render at 3% - started"
        );
    }

    #[test]
    fn setup_checklist_tracks_manual_test_readiness() {
        let checklist = setup_checklist(
            "D:\\GIT\\bookcast-studio\\.manual-test\\library",
            "Diagnostics OK",
            "book-1",
            1,
            "Engine check OK: piper returned 1 voices.",
            "D:\\out\\book.opus",
            "No active jobs. Queue idle.",
        );

        assert!(checklist.contains("[x] Library path set"));
        assert!(checklist.contains("[x] Diagnostics run"));
        assert!(checklist.contains("[x] Book selected"));
        assert!(checklist.contains("[x] Engine checked"));
        assert!(checklist.contains("[x] Sample or output rendered"));
        assert!(checklist.contains("[x] Queue healthy"));

        let blocked = setup_checklist(
            "library",
            "Run diagnostics before importing.",
            "",
            2,
            "Engine check: not run",
            "",
            "Attention: render failed - missing model",
        );
        assert!(blocked.contains("[ ] Diagnostics run"));
        assert!(blocked.contains("[ ] Book selected"));
        assert!(blocked.contains("[ ] Engine checked"));
        assert!(blocked.contains("[ ] Sample or output rendered"));
        assert!(blocked.contains("[ ] Queue healthy"));
    }

    #[test]
    fn engine_setup_text_explains_selected_provider_requirements() {
        let sapi = engine_setup_text_from(
            0,
            "",
            "",
            "",
            "",
            "",
            "",
            "Engine check OK: windows_sapi returned 1 voices.",
        );
        assert!(sapi.contains("Windows voices setup"));
        assert!(sapi.contains("[x] No path needed"));

        let piper =
            engine_setup_text_from(1, "piper.exe", "", "", "", "", "", "Engine check: not run");
        assert!(piper.contains("Piper voices setup"));
        assert!(piper.contains("[x] Piper app selected"));
        assert!(piper.contains("[ ] Voice selected"));

        let audio_cpp = engine_setup_text_from(
            2,
            "",
            "",
            "audiocpp_cli.exe",
            "qwen3-tts.gguf",
            "cpu",
            "qwen3_tts",
            "Engine check OK: audio.cpp ready",
        );
        assert!(audio_cpp.contains("audio.cpp advanced setup"));
        assert!(audio_cpp.contains("[x] Backend set"));
        assert!(audio_cpp.contains("[x] Model family set"));
        assert!(audio_cpp.contains("[x] Engine check passed"));
    }
}
