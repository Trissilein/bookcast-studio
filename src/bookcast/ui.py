from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .calibre import CalibreClient, find_calibredb
from .library import BookLibrary
from .llm import OllamaProvider
from .podcast import generate_podcast_script


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bookcast-ui")
    parser.add_argument("--library", type=Path, default=Path.cwd() / "library")
    args = parser.parse_args(argv)

    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QAbstractItemView,
            QApplication,
            QDialog,
            QDialogButtonBox,
            QCheckBox,
            QFileDialog,
            QHBoxLayout,
            QInputDialog,
            QLabel,
            QLineEdit,
            QMainWindow,
            QPlainTextEdit,
            QPushButton,
            QTableWidget,
            QTableWidgetItem,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as exc:
        raise SystemExit("PySide6 missing. Install with: python -m pip install -e .[ui]") from exc

    class MainWindow(QMainWindow):
        def __init__(self, library_root: Path) -> None:
            super().__init__()
            self.library = BookLibrary(library_root)
            self.setWindowTitle("BookCast Studio")
            self.resize(1100, 680)

            self.status = QLabel(f"Library: {library_root}")
            self.table = QTableWidget(0, 7)
            self.table.setHorizontalHeaderLabels(["Author", "Title", "Language", "Cleanup", "Chapters", "Chunks", "Status"])
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.setSortingEnabled(True)

            import_button = QPushButton("Import TXT/MD/EPUB")
            import_button.clicked.connect(self.import_file)
            calibre_button = QPushButton("Import from Calibre")
            calibre_button.clicked.connect(self.import_calibre)
            render_button = QPushButton("Render Opus")
            render_button.clicked.connect(lambda: self.render_selected("opus"))
            render_m4b_button = QPushButton("Render M4B")
            render_m4b_button.clicked.connect(lambda: self.render_selected("m4b"))
            chapters_button = QPushButton("Chapters")
            chapters_button.clicked.connect(self.edit_chapters)
            voices_button = QPushButton("Voices")
            voices_button.clicked.connect(self.edit_speakers)
            profile_button = QPushButton("Cleanup Profile")
            profile_button.clicked.connect(self.edit_cleanup_profile)
            podcast_script_button = QPushButton("Podcast Script")
            podcast_script_button.clicked.connect(self.write_podcast_script)
            podcast_render_button = QPushButton("Podcast Render")
            podcast_render_button.clicked.connect(self.render_podcast)

            toolbar = QHBoxLayout()
            toolbar.addWidget(import_button)
            toolbar.addWidget(calibre_button)
            toolbar.addWidget(render_button)
            toolbar.addWidget(render_m4b_button)
            toolbar.addWidget(chapters_button)
            toolbar.addWidget(voices_button)
            toolbar.addWidget(profile_button)
            toolbar.addWidget(podcast_script_button)
            toolbar.addWidget(podcast_render_button)
            toolbar.addStretch(1)

            layout = QVBoxLayout()
            layout.addLayout(toolbar)
            layout.addWidget(self.table)
            layout.addWidget(self.status)

            root = QWidget()
            root.setLayout(layout)
            self.setCentralWidget(root)
            self.refresh()

        def import_calibre(self) -> None:
            folder = QFileDialog.getExistingDirectory(self, "Select Calibre Library", str(Path.home()))
            if not folder:
                return
            try:
                client = CalibreClient(Path(folder), calibredb=find_calibredb() or "calibredb")
                books = [book for book in client.scan() if book.preferred_format()]
            except Exception as exc:
                self.status.setText(f"Calibre scan failed: {exc}")
                return
            if not books:
                self.status.setText("No Calibre books with EPUB/TXT/MD found.")
                return

            dialog = QDialog(self)
            dialog.setWindowTitle("Import from Calibre")
            dialog.resize(900, 520)
            table = QTableWidget(len(books), 4)
            table.setHorizontalHeaderLabels(["ID", "Author", "Title", "Formats"])
            table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            table.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
            for row, book in enumerate(books):
                for col, value in enumerate([book.id, book.authors, book.title, ", ".join(book.formats)]):
                    table.setItem(row, col, QTableWidgetItem(str(value)))
            table.resizeColumnsToContents()

            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)

            layout = QVBoxLayout()
            layout.addWidget(QLabel("Select Calibre books to import. Existing Calibre UUIDs are skipped."))
            layout.addWidget(table)
            layout.addWidget(buttons)
            dialog.setLayout(layout)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            rows = sorted({index.row() for index in table.selectedIndexes()})
            if not rows:
                self.status.setText("No Calibre books selected.")
                return
            imported = 0
            try:
                for row in rows:
                    self.library.import_calibre_book(client, books[row])
                    imported += 1
            except Exception as exc:
                self.status.setText(f"Calibre import failed after {imported} books: {exc}")
                self.refresh()
                return
            self.refresh()
            self.status.setText(f"Imported {imported} Calibre books.")

        def refresh(self) -> None:
            self.table.setSortingEnabled(False)
            books = self.library.list_books()
            self.table.setRowCount(len(books))
            for row, book in enumerate(books):
                values = [
                    book["author"],
                    book["title"],
                    book["language"] or "",
                    book["cleanup_profile"],
                    book["chapter_count"],
                    book["chunk_count"],
                    book["status"],
                ]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    if col == 0:
                        item.setData(Qt.ItemDataRole.UserRole, book["id"])
                    if col in {4, 5}:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, col, item)
            self.table.resizeColumnsToContents()
            self.table.setSortingEnabled(True)
            self.status.setText(f"{len(books)} books in {self.library.root}")

        def _selected_book_id(self) -> str | None:
            row = self.table.currentRow()
            if row < 0:
                return None
            item = self.table.item(row, 0)
            return str(item.data(Qt.ItemDataRole.UserRole)) if item else None

        def import_file(self) -> None:
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "Import source",
                str(Path.home()),
                "Supported Sources (*.txt *.md *.epub *.pdf *.docx)",
            )
            if not file_name:
                return
            try:
                self.library.import_source(Path(file_name))
            except Exception as exc:
                self.status.setText(f"Import failed: {exc}")
                return
            self.refresh()

        def render_selected(self, output_format: str = "opus") -> None:
            book_id = self._selected_book_id()
            if not book_id:
                self.status.setText("Select a book to render.")
                return
            try:
                output = self.library.render_book(str(book_id), output_format=output_format)
            except Exception as exc:
                self.status.setText(f"Render failed: {exc}")
                return
            self.refresh()
            self.status.setText(f"Rendered {output}")

        def edit_chapters(self) -> None:
            book_id = self._selected_book_id()
            if not book_id:
                self.status.setText("Select a book first.")
                return
            chapters = self.library.get_chapters(book_id)
            if not chapters:
                self.status.setText("Selected book has no chapters.")
                return

            dialog = QDialog(self)
            dialog.setWindowTitle("Edit Chapters")
            dialog.resize(980, 680)

            table = QTableWidget(len(chapters), 2)
            table.setHorizontalHeaderLabels(["Index", "Title"])
            for row, chapter in enumerate(chapters):
                table.setItem(row, 0, QTableWidgetItem(str(chapter["chapter_index"])))
                table.setItem(row, 1, QTableWidgetItem(str(chapter["title"])))
            table.resizeColumnsToContents()

            title_edit = QLineEdit()
            text_edit = QPlainTextEdit()
            text_edit.setTabChangesFocus(True)

            def load_row(row: int) -> None:
                if row < 0 or row >= len(chapters):
                    return
                title_edit.setText(str(chapters[row]["title"]))
                text_edit.setPlainText(str(chapters[row]["text"]))

            load_row(0)
            table.currentCellChanged.connect(lambda current_row, *_: load_row(current_row))
            table.selectRow(0)

            save_button = QPushButton("Save Chapter")
            close_button = QPushButton("Close")

            def save_current() -> None:
                row = table.currentRow()
                if row < 0:
                    return
                chapter_index = int(chapters[row]["chapter_index"])
                self.library.update_chapter(book_id, chapter_index, title_edit.text().strip(), text_edit.toPlainText())
                dialog.accept()

            save_button.clicked.connect(save_current)
            close_button.clicked.connect(dialog.reject)

            editor_layout = QVBoxLayout()
            editor_layout.addWidget(QLabel("Title"))
            editor_layout.addWidget(title_edit)
            editor_layout.addWidget(QLabel("Text"))
            editor_layout.addWidget(text_edit)

            button_row = QHBoxLayout()
            button_row.addWidget(save_button)
            button_row.addWidget(close_button)
            button_row.addStretch(1)

            layout = QVBoxLayout()
            layout.addWidget(QLabel("Select a chapter, edit title and text, then save."))
            layout.addWidget(table)
            layout.addLayout(editor_layout)
            layout.addLayout(button_row)
            dialog.setLayout(layout)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.refresh()
                self.status.setText("Chapter updated and chunks rebuilt.")

        def edit_speakers(self) -> None:
            book_id = self._selected_book_id()
            if not book_id:
                self.status.setText("Select a book first.")
                return
            speakers = self.library.list_speakers(book_id)
            if not speakers:
                self.status.setText("No speakers stored yet. Generate a podcast first.")
                return

            dialog = QDialog(self)
            dialog.setWindowTitle("Speakers and Voices")
            dialog.resize(760, 480)

            table = QTableWidget(len(speakers), 2)
            table.setHorizontalHeaderLabels(["Speaker", "Voice"])
            for row, speaker in enumerate(speakers):
                table.setItem(row, 0, QTableWidgetItem(str(speaker["name"])))
                table.setItem(row, 1, QTableWidgetItem(str(speaker["voice_name"] or "")))
            table.resizeColumnsToContents()

            save_button = QPushButton("Save")
            close_button = QPushButton("Close")

            def save_current() -> None:
                names: list[str] = []
                voice_map: dict[str, str] = {}
                for row in range(table.rowCount()):
                    speaker_item = table.item(row, 0)
                    voice_item = table.item(row, 1)
                    if not speaker_item:
                        continue
                    speaker = speaker_item.text().strip()
                    if not speaker:
                        continue
                    names.append(speaker)
                    voice = voice_item.text().strip() if voice_item else ""
                    if voice:
                        voice_map[speaker] = voice
                self.library.sync_speakers(book_id, names, voice_map=voice_map)
                dialog.accept()

            save_button.clicked.connect(save_current)
            close_button.clicked.connect(dialog.reject)

            button_row = QHBoxLayout()
            button_row.addWidget(save_button)
            button_row.addWidget(close_button)
            button_row.addStretch(1)

            layout = QVBoxLayout()
            layout.addWidget(QLabel("Speaker names can be mapped to installed TTS voice names."))
            layout.addWidget(table)
            layout.addLayout(button_row)
            dialog.setLayout(layout)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.refresh()
                self.status.setText("Speaker mapping saved.")

        def edit_cleanup_profile(self) -> None:
            book_id = self._selected_book_id()
            if not book_id:
                self.status.setText("Select a book first.")
                return
            book = self.library.get_book(book_id)
            if not book:
                self.status.setText("Book not found.")
                return
            profile = self.library.get_cleanup_profile(str(book.get("cleanup_profile") or "standard"))

            dialog = QDialog(self)
            dialog.setWindowTitle("Cleanup Profile")
            dialog.resize(760, 520)

            name_edit = QLineEdit(str(profile["name"]))
            json_edit = QPlainTextEdit()
            json_edit.setPlainText(json.dumps(profile.get("config", {}), ensure_ascii=False, indent=2))
            apply_to_book = QCheckBox("Apply to selected book")
            apply_to_book.setChecked(True)

            save_button = QPushButton("Save")
            close_button = QPushButton("Close")

            def save_profile() -> None:
                name = name_edit.text().strip() or "standard"
                try:
                    config = json.loads(json_edit.toPlainText() or "{}")
                except json.JSONDecodeError as exc:
                    self.status.setText(f"Invalid cleanup JSON: {exc}")
                    return
                self.library.upsert_cleanup_profile(name, config)
                if apply_to_book.isChecked():
                    self.library.set_book_cleanup_profile(book_id, name)
                dialog.accept()

            save_button.clicked.connect(save_profile)
            close_button.clicked.connect(dialog.reject)

            button_row = QHBoxLayout()
            button_row.addWidget(save_button)
            button_row.addWidget(close_button)
            button_row.addStretch(1)

            layout = QVBoxLayout()
            layout.addWidget(QLabel("Profile name"))
            layout.addWidget(name_edit)
            layout.addWidget(QLabel("Profile JSON"))
            layout.addWidget(json_edit)
            layout.addWidget(apply_to_book)
            layout.addLayout(button_row)
            dialog.setLayout(layout)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.refresh()
                self.status.setText("Cleanup profile saved.")

        def write_podcast_script(self) -> None:
            self._generate_podcast(render_audio=False)

        def render_podcast(self) -> None:
            self._generate_podcast(render_audio=True)

        def _generate_podcast(self, *, render_audio: bool) -> None:
            row = self.table.currentRow()
            if row < 0:
                self.status.setText("Select a book first.")
                return
            item = self.table.item(row, 0)
            book_id = item.data(Qt.ItemDataRole.UserRole) if item else None
            if not book_id:
                self.status.setText("Selected row has no book id.")
                return
            mode, ok = QInputDialog.getItem(
                self,
                "Podcast Mode",
                "Select podcast mode:",
                ["educational", "controversial", "interview"],
                0,
                False,
            )
            if not ok:
                return
            try:
                text = self.library.get_book_text(str(book_id))
                provider = OllamaProvider()
                if not provider.health():
                    raise RuntimeError("Ollama is not reachable")
                script = generate_podcast_script(text, provider, mode=mode)
                if render_audio:
                    output = self.library.render_podcast_script(str(book_id), script)
                    self.status.setText(f"Rendered podcast {output}")
                else:
                    output = self.library.save_podcast_script(str(book_id), script.to_dict())
                    self.status.setText(f"Wrote podcast script {output}")
            except Exception as exc:
                self.status.setText(f"Podcast failed: {exc}")
                return
            self.refresh()

        def closeEvent(self, event) -> None:  # noqa: N802 - Qt API name
            self.library.close()
            super().closeEvent(event)

    app = QApplication(sys.argv[:1])
    window = MainWindow(args.library)
    window.show()
    return app.exec()
