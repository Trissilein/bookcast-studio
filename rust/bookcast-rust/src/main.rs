use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};
use serde_json::Value;

slint::slint! {
import { Button, ComboBox, LineEdit } from "std-widgets.slint";

export component AppWindow inherits Window {
    title: "BookCast Studio";
    width: 1220px;
    height: 780px;

    in-out property <string> library-path: "library";
    in-out property <string> source-path: "";
    in-out property <string> source-probe-text: "No source probed yet.";
    in-out property <string> calibre-path: "";
    in-out property <string> calibre-ids: "";
    in-out property <string> calibre-limit: "50";
    in-out property <string> calibre-preview-text: "No Calibre scan yet.";
    in-out property <string> book-id: "";
    in-out property <string> voice-name: "";
    in-out property <string> voice-list-text: "Discover voices before choosing one.";
    in-out property <string> output-format: "opus";
    in-out property <string> render-limit: "";
    in-out property <string> tts-test-text: "BookCast engine test.";
    in-out property <string> last-output-path: "";
    in-out property <string> output-list-text: "No outputs loaded.";
    in-out property <string> audio-cpp-exe: "";
    in-out property <string> audio-cpp-model: "";
    in-out property <string> audio-cpp-backend: "cpu";
    in-out property <string> audio-cpp-family: "";
    in-out property <string> piper-exe: "";
    in-out property <string> piper-voice-dir: "";
    in-out property <int> engine-index: 0;
    in-out property <string> status-text: "Ready";
    in-out property <string> diagnostic-text: "Run diagnostics before importing.";
    in-out property <string> books-text: "No books loaded.";
    in-out property <string> book-selection-text: "Refresh Books to enable selection.";
    in-out property <string> book-preview-text: "Select or import a book, then load preview.";
    in-out property <string> cleanup-profile-name: "standard";
    in-out property <string> cleanup-profiles-text: "Load cleanup profiles before changing chunking.";
    in-out property <string> character-text: "Run character extraction after loading a book preview. Ollama must be running.";
    in-out property <string> podcast-text: "Generate a script first. Render only after speaker voices are mapped.";
    in-out property <string> ollama-url: "http://127.0.0.1:11434";
    in-out property <string> ollama-model: "qwen3:8b";
    in-out property <string> speaker-voice-map: "host=; explainer=; skeptic=";
    in-out property <string> interactive-turns: "4";
    in-out property <string> interactive-seed-prompt: "";
    in-out property <int> podcast-mode-index: 0;
    in-out property <string> queue-text: "Queue idle.";
    in-out property <string> guide-text: "Next: run diagnostics, import a source, then render from TTS Studio.";
    in-out property <string> render-plan-text: "Render plan: choose a book, choose an engine, render a sample, then full book.";
    in-out property <string> engine-check-text: "Engine check: not run. Click Check Engine before rendering.";
    in-out property <string> audio-cpp-status: "audio.cpp: not checked";
    in-out property <int> current-view: 0;

    callback save-settings();
    callback browse-library();
    callback browse-source-file();
    callback browse-source-folder();
    callback probe-source();
    callback browse-calibre();
    callback browse-piper-exe();
    callback browse-piper-voice-dir();
    callback browse-audio-cpp-exe();
    callback browse-audio-cpp-model();
    callback diagnose();
    callback list-books();
    callback import-source();
    callback diagnose-calibre();
    callback scan-calibre();
    callback import-calibre();
    callback load-preview();
    callback previous-book();
    callback next-book();
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
    callback discover-voices();
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
                        width: 660px;
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

                            Text { text: "Engine"; color: rgb(89, 99, 93); }
                            ComboBox {
                                model: ["Windows SAPI via Python bridge", "Piper local process", "audio.cpp external process"];
                                current-index <=> root.engine-index;
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
                            HorizontalLayout {
                                spacing: 10px;
                                Button { text: "Check Engine"; clicked => { root.check-engine(); } }
                                Button { text: "Discover Voices"; clicked => { root.discover-voices(); } }
                            }

                            HorizontalLayout {
                                spacing: 10px;
                                VerticalLayout {
                                    Text { text: "Output"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.output-format; }
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
                                }
                                VerticalLayout {
                                    Text { text: "Family"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.audio-cpp-family; }
                                }
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
                            Button { text: "Diagnose Calibre"; clicked => { root.diagnose-calibre(); } }
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
                            Text { text: "Manual confirmation required before per-character rendering."; color: rgb(89, 99, 93); font-size: 13px; wrap: word-wrap; }
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
                                VerticalLayout {
                                    Text { text: "Ollama URL"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.ollama-url; }
                                }
                                VerticalLayout {
                                    Text { text: "Model"; color: rgb(89, 99, 93); }
                                    LineEdit { text <=> root.ollama-model; }
                                }
                            }
                            Text { text: "Speaker voices: speaker=voice, separated by semicolon or comma"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.speaker-voice-map; }
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
                            Text { text: "Library root"; color: rgb(89, 99, 93); }
                            HorizontalLayout {
                                spacing: 10px;
                                LineEdit { text <=> root.library-path; }
                                Button { text: "Browse"; clicked => { root.browse-library(); } }
                            }
                            Text { text: "Default output format"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.output-format; }
                            Text { text: "Full render chunk limit (empty = all)"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.render-limit; }
                            Text { text: "Default voice"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.voice-name; }
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
                            Text { text: "audio.cpp family"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.audio-cpp-family; }
                            Text { text: "Ollama URL"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.ollama-url; }
                            Text { text: "Ollama model"; color: rgb(89, 99, 93); }
                            LineEdit { text <=> root.ollama-model; }
                            Button { text: "Save Settings"; clicked => { root.save-settings(); } }
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
}

#[derive(Default, Serialize, Deserialize)]
#[serde(default)]
struct WorkbenchSettings {
    library_path: String,
    source_path: String,
    calibre_path: String,
    calibre_ids: String,
    calibre_limit: String,
    book_id: String,
    voice_name: String,
    output_format: String,
    render_limit: String,
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

    wire_callbacks(&app, state);
    app.run()
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
            app.set_guide_text("Calibre folder selected. Click Diagnose Calibre next.".into());
        }
    });

    let weak = app.as_weak();
    app.on_browse_piper_exe(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(path) = choose_file("Choose piper executable", &[("Executable", &["exe"])]) {
            app.set_piper_exe(path_to_string(&path).into());
            app.set_status_text("Piper executable selected.".into());
        }
    });

    let weak = app.as_weak();
    app.on_browse_piper_voice_dir(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(path) = choose_folder("Choose Piper voices folder") {
            app.set_piper_voice_dir(path_to_string(&path).into());
            app.set_status_text("Piper voices folder selected.".into());
        }
    });

    let weak = app.as_weak();
    app.on_browse_audio_cpp_exe(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(path) = choose_file("Choose audio.cpp executable", &[("Executable", &["exe"])])
        {
            app.set_audio_cpp_exe(path_to_string(&path).into());
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
            app.set_guide_text("audio.cpp model selected. Click Check audio.cpp next.".into());
        }
    });

    let weak = app.as_weak();
    let diagnose_state = state.clone();
    app.on_diagnose(move || {
        let Some(app) = weak.upgrade() else { return };
        let library = app.get_library_path().to_string();
        run_bridge(
            app.as_weak(),
            diagnose_state.clone(),
            "diagnose",
            vec![
                "bridge".into(),
                "diagnose".into(),
                "--library".into(),
                library,
            ],
        );
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
            return;
        }
        run_bridge(
            app.as_weak(),
            calibre_diagnose_state.clone(),
            "calibre diagnose",
            vec!["bridge".into(), "calibre-diagnose".into(), calibre],
        );
    });

    let weak = app.as_weak();
    let calibre_state = state.clone();
    app.on_scan_calibre(move || {
        let Some(app) = weak.upgrade() else { return };
        let calibre = app.get_calibre_path().to_string();
        if calibre.trim().is_empty() {
            app.set_status_text("Calibre scan needs a library path.".into());
            return;
        }
        if let Some(problem) =
            optional_positive_limit_problem(&app.get_calibre_limit().to_string(), "Calibre limit")
        {
            app.set_status_text(problem.into());
            return;
        }
        let mut args = vec!["bridge".into(), "calibre-scan".into(), calibre];
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
            return;
        }
        if let Some(problem) =
            optional_positive_limit_problem(&app.get_calibre_limit().to_string(), "Calibre limit")
        {
            app.set_status_text(problem.into());
            return;
        }
        let ids = split_ids(&app.get_calibre_ids().to_string());
        if ids.is_empty() {
            app.set_status_text("Calibre import needs IDs. Run Scan Calibre, then remove IDs you do not want.".into());
            app.set_guide_text("Scan Calibre fills Calibre IDs with the visible importable books. Edit that field, then import.".into());
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
    let tts_test_state = state.clone();
    app.on_tts_test(move || {
        let Some(app) = weak.upgrade() else { return };
        if let Some(problem) = tts_test_preflight_problem(&app) {
            app.set_status_text(problem.clone().into());
            app.set_engine_check_text(problem.clone().into());
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
            return;
        }
        if let Some(problem) = render_limit_problem(&app) {
            app.set_status_text(problem.clone().into());
            app.set_guide_text(problem.into());
            app.set_render_plan_text(render_plan_text(&app).into());
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
        run_bridge(app.as_weak(), script_state.clone(), "podcast script", args);
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
        refresh_audio_cpp(weak.clone(), refresh_state.repo_root.clone());
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
        cancel_active_job(weak.clone(), cancel_state.active_pid.clone());
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
                        if output.status.success() {
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
                        handle_bridge_events(
                            weak.clone(),
                            state.jobs.clone(),
                            state.book_ids.clone(),
                            state.book_index.clone(),
                            job_id,
                            &stdout,
                        );
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
                        update_job_detail(
                            weak.clone(),
                            state.jobs.clone(),
                            job_id,
                            &summarize_output(&text),
                        );
                        if label == "diagnose" {
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

fn refresh_audio_cpp(weak: slint::Weak<AppWindow>, repo_root: PathBuf) {
    set_status(weak.clone(), "Checking audio.cpp upstream...");
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
                set_status(weak, "audio.cpp check completed.");
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
                set_status(weak, "audio.cpp check failed.");
            }
            Err(error) => {
                set_audio_status(weak.clone(), "audio.cpp: git not available");
                push_log(weak.clone(), &format!("audio.cpp check failed: {error}"));
                set_status(weak, "audio.cpp check failed.");
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

fn cancel_active_job(weak: slint::Weak<AppWindow>, active_pid: Arc<Mutex<Option<u32>>>) {
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
            push_log(weak, &format!("Cancelled process {pid}."));
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
        calibre_ids: app.get_calibre_ids().to_string(),
        calibre_limit: app.get_calibre_limit().to_string(),
        book_id: app.get_book_id().to_string(),
        voice_name: app.get_voice_name().to_string(),
        output_format: app.get_output_format().to_string(),
        render_limit: app.get_render_limit().to_string(),
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

fn podcast_mode(index: i32) -> &'static str {
    match index {
        1 => "controversial",
        2 => "interview",
        _ => "educational",
    }
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
        app.get_engine_index(),
        &app.get_piper_exe().to_string(),
        &app.get_audio_cpp_exe().to_string(),
        &app.get_audio_cpp_model().to_string(),
    )
}

fn engine_check_problem(app: &AppWindow) -> Option<String> {
    engine_check_problem_from(
        app.get_engine_index(),
        &app.get_piper_exe().to_string(),
        &app.get_audio_cpp_exe().to_string(),
        &app.get_audio_cpp_model().to_string(),
    )
}

fn tts_test_preflight_problem(app: &AppWindow) -> Option<String> {
    tts_test_preflight_problem_from(
        &app.get_tts_test_text().to_string(),
        app.get_engine_index(),
        &app.get_piper_exe().to_string(),
        &app.get_audio_cpp_exe().to_string(),
        &app.get_audio_cpp_model().to_string(),
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

fn engine_check_problem_from(
    engine_index: i32,
    piper_exe: &str,
    audio_cpp_exe: &str,
    audio_cpp_model: &str,
) -> Option<String> {
    if engine_index == 1 && piper_exe.trim().is_empty() {
        return Some("Piper selected, but Piper executable is missing. Run Diagnose or set Piper executable.".to_string());
    }
    if engine_index == 2 {
        if audio_cpp_exe.trim().is_empty() {
            return Some("audio.cpp selected, but executable is missing. Build audio.cpp or set audiocpp_cli.exe.".to_string());
        }
        if audio_cpp_model.trim().is_empty() {
            return Some(
                "audio.cpp selected, but model is missing. Set audio.cpp model before rendering."
                    .to_string(),
            );
        }
    }
    None
}

fn tts_test_preflight_problem_from(
    text: &str,
    engine_index: i32,
    piper_exe: &str,
    audio_cpp_exe: &str,
    audio_cpp_model: &str,
) -> Option<String> {
    if text.trim().is_empty() {
        return Some("TTS test needs text.".to_string());
    }
    engine_check_problem_from(engine_index, piper_exe, audio_cpp_exe, audio_cpp_model)
}

fn render_preflight_problem_from(
    book_id: &str,
    output_format: &str,
    engine_index: i32,
    piper_exe: &str,
    audio_cpp_exe: &str,
    audio_cpp_model: &str,
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
    if let Some(problem) =
        engine_check_problem_from(engine_index, piper_exe, audio_cpp_exe, audio_cpp_model)
    {
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
    format!(
        "Render plan: book {}, engine {engine}, voice {voice}, output {}, full render {limit}. Run sample first; full render uses same settings.",
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
    let limit = app.get_render_limit().to_string();
    if command == "render" && !limit.trim().is_empty() {
        args.extend(["--limit".into(), limit.trim().to_string()]);
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
    for entry in split_voice_map(&app.get_speaker_voice_map().to_string()) {
        args.extend(["--voice".into(), entry]);
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
    for entry in split_voice_map(&app.get_speaker_voice_map().to_string()) {
        args.extend(["--voice".into(), entry]);
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

fn preview_args(app: &AppWindow, book_id: String) -> Vec<String> {
    vec![
        "bridge".into(),
        "book-preview".into(),
        book_id,
        "--library".into(),
        app.get_library_path().to_string(),
    ]
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
    let id = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_millis() as u64)
        .unwrap_or(0);
    {
        let mut jobs = jobs.lock().expect("jobs lock");
        jobs.push(JobState {
            id,
            label: label.to_string(),
            status: status.to_string(),
            progress,
            detail: detail.to_string(),
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
        let mut jobs = jobs.lock().expect("jobs lock");
        if let Some(job) = jobs.iter_mut().find(|job| job.id == id) {
            job.status = status.to_string();
            job.progress = progress;
            job.detail = detail.to_string();
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
        let mut jobs = jobs.lock().expect("jobs lock");
        if let Some(job) = jobs.iter_mut().find(|job| job.id == id) {
            job.detail = detail.to_string();
        }
    }
    render_queue(weak, jobs);
}

fn render_queue(weak: slint::Weak<AppWindow>, jobs: Arc<Mutex<Vec<JobState>>>) {
    let text = {
        let jobs = jobs.lock().expect("jobs lock");
        if jobs.is_empty() {
            "Queue idle.".to_string()
        } else {
            jobs.iter()
                .rev()
                .take(8)
                .map(|job| {
                    format!(
                        "#{:05} | {:>7} | {:>3}% | {:<12} | {}",
                        job.id % 100000,
                        job.status,
                        job.progress,
                        job.label,
                        job.detail
                    )
                })
                .collect::<Vec<_>>()
                .join("\n")
        }
    };
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_queue_text(text.into());
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

fn json_string_list(value: &Value, key: &str) -> String {
    value
        .get(key)
        .and_then(Value::as_array)
        .map(|items| {
            items
                .iter()
                .filter_map(Value::as_str)
                .collect::<Vec<_>>()
                .join("\n")
        })
        .unwrap_or_default()
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
                let detail = value
                    .get("output")
                    .and_then(Value::as_str)
                    .or_else(|| value.get("book_id").and_then(Value::as_str))
                    .unwrap_or("Done");
                update_job(weak.clone(), jobs.clone(), job_id, "done", 100, detail);
                if let Some(book_id) = value.get("book_id").and_then(Value::as_str) {
                    set_book_id(weak.clone(), book_id);
                    set_current_view(weak.clone(), 0);
                    set_guide(
                        weak.clone(),
                        "Import finished. Preview loads automatically. Render a sample next.",
                    );
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
                    "Voices loaded. Voice field was filled with the first voice.",
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
                    if hints.is_empty() {
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
                let candidates = json_string_list(&value, "candidate_libraries");
                let issues = json_string_list(&value, "issues");
                let hints = json_string_list(&value, "hints");
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
                    format!(
                        "Calibre problem\nLibrary: {library}\nmetadata.db: {metadata}\ncalibredb: {calibredb}{suggestion}{candidates}\n\nIssues:\n{issues}\n\nHints:\n{hints}"
                    )
                };
                set_calibre_preview(weak.clone(), &detail);
                if healthy {
                    set_guide(
                        weak.clone(),
                        "Calibre path looks valid. Scan/import can continue.",
                    );
                } else {
                    set_guide(
                        weak.clone(),
                        &format!(
                            "Fix Calibre setup: {}",
                            issues.lines().next().unwrap_or("unknown issue")
                        ),
                    );
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
                    .unwrap_or_else(|| "No outputs for this book yet.".to_string());
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
                        "Diagnostics found Piper. Choose Piper local process, discover voices, then render a sample."
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
                    .unwrap_or_else(|| "No books loaded.".to_string());
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
                set_book_selection(
                    weak.clone(),
                    &format!("{loaded_count} books loaded. Use Previous/Next Book to switch without copying IDs."),
                );
                set_guide(
                    weak.clone(),
                    "Books loaded. First book id is selected automatically if the field was empty.",
                );
            }
            Some("book_preview") => {
                let book = value.get("book").unwrap_or(&Value::Null);
                let title = book.get("title").and_then(Value::as_str).unwrap_or("");
                let author = book.get("author").and_then(Value::as_str).unwrap_or("");
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
                let preview = value.get("preview").and_then(Value::as_str).unwrap_or("");
                set_book_preview(
                    weak.clone(),
                    &format!(
                        "{author} - {title}\n{chunk_count} chunks\n\nChapters\n{chapters}\n\nChunks\n{chunks}\n\nText Preview\n{preview}"
                    ),
                );
                set_current_view(weak.clone(), 0);
                set_guide(
                    weak.clone(),
                    "Preview loaded. Render sample before full render.",
                );
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
            }
            Some("characters") => {
                let text = value
                    .get("candidates")
                    .and_then(Value::as_array)
                    .map(|items| {
                        items
                            .iter()
                            .map(|item| {
                                let name = item.get("name").and_then(Value::as_str).unwrap_or("");
                                let role = item.get("role").and_then(Value::as_str).unwrap_or("");
                                let evidence =
                                    item.get("evidence").and_then(Value::as_str).unwrap_or("");
                                format!("{name} | {role} | {evidence}")
                            })
                            .collect::<Vec<_>>()
                            .join("\n")
                    })
                    .filter(|text| !text.is_empty())
                    .unwrap_or_else(|| "No character candidates returned.".to_string());
                set_character_text(weak.clone(), &text);
                set_guide(
                    weak.clone(),
                    "Character candidates loaded. Confirm names manually before voice assignment.",
                );
            }
            Some("podcast_script") => {
                let script = value.get("script").unwrap_or(&Value::Null);
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
                set_podcast_text(
                    weak.clone(),
                    &format!("{title}\nSpeakers: {speakers}\n\n{summary}\n\n{turns}"),
                );
                if let Some(path) = value.get("path").and_then(Value::as_str) {
                    set_guide(weak.clone(), &format!("Podcast script saved: {path}"));
                } else if let Some(output) = value.get("output").and_then(Value::as_str) {
                    set_last_output(weak.clone(), output);
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
                    set_guide(weak.clone(), &format!("Fix required: {message}"));
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
                format!("status   |         |     | system       | {line}")
            } else {
                format!("{current}\nstatus   |         |     | system       | {line}")
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
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_diagnostic_text(text.into());
        }
    });
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

fn set_character_text(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_character_text(text.into());
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
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_last_output_path(text.into());
        }
    });
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
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_book_id(text.into());
        }
    });
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
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            if app.get_book_id().to_string().trim().is_empty() {
                app.set_book_id(text.into());
            }
        }
    });
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

fn set_engine_check(weak: slint::Weak<AppWindow>, text: &str) {
    let text = text.to_string();
    let _ = slint::invoke_from_event_loop(move || {
        if let Some(app) = weak.upgrade() {
            app.set_engine_check_text(text.into());
        }
    });
}

#[cfg(test)]
mod tests {
    use std::path::PathBuf;

    use serde_json::json;

    use super::audio_cpp_update_status;
    use super::job_progress_detail;
    use super::optional_positive_limit_problem;
    use super::output_open_target;
    use super::render_preflight_problem_from;
    use super::source_probe_summary;
    use super::split_ids;
    use super::tts_test_preflight_problem_from;

    #[test]
    fn render_preflight_requires_book_id() {
        assert_eq!(
            render_preflight_problem_from("", "opus", 0, "", "", "").as_deref(),
            Some("Render needs a book id. Import a book or click Refresh Books.")
        );
    }

    #[test]
    fn render_preflight_rejects_unknown_output_format() {
        assert_eq!(
            render_preflight_problem_from("book-1", "flac", 0, "", "", "").as_deref(),
            Some("Output must be opus, mp3, wav, or m4b.")
        );
    }

    #[test]
    fn render_preflight_requires_audio_cpp_model() {
        assert_eq!(
            render_preflight_problem_from("book-1", "opus", 2, "", "audiocpp_cli.exe", "")
                .as_deref(),
            Some("audio.cpp selected, but model is missing. Set audio.cpp model before rendering.")
        );
    }

    #[test]
    fn tts_test_preflight_reuses_engine_checks() {
        assert_eq!(
            tts_test_preflight_problem_from("", 0, "", "", "").as_deref(),
            Some("TTS test needs text.")
        );
        assert_eq!(
            tts_test_preflight_problem_from("hello", 1, "", "", "").as_deref(),
            Some("Piper selected, but Piper executable is missing. Run Diagnose or set Piper executable.")
        );
        assert_eq!(
            tts_test_preflight_problem_from("hello", 2, "", "", "model.bin").as_deref(),
            Some("audio.cpp selected, but executable is missing. Build audio.cpp or set audiocpp_cli.exe.")
        );
        assert_eq!(
            tts_test_preflight_problem_from("hello", 2, "", "audiocpp_cli.exe", "").as_deref(),
            Some("audio.cpp selected, but model is missing. Set audio.cpp model before rendering.")
        );
        assert_eq!(
            tts_test_preflight_problem_from("hello", 2, "", "audiocpp_cli.exe", "model.bin"),
            None
        );
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
    fn output_open_target_can_open_file_or_parent_folder() {
        let path = r"C:\tmp\book.opus";
        assert_eq!(output_open_target(path, false), PathBuf::from(path));
        assert_eq!(output_open_target(path, true), PathBuf::from(r"C:\tmp"));
    }

    #[test]
    fn render_preflight_accepts_configured_piper() {
        assert_eq!(
            render_preflight_problem_from("book-1", "m4b", 1, "piper.exe", "", ""),
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
}
