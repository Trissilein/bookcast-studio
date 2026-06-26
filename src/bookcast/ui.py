from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .calibre import CalibreClient, find_calibredb
from .library import BookLibrary


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
            QFileDialog,
            QHBoxLayout,
            QLabel,
            QMainWindow,
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
            self.table = QTableWidget(0, 6)
            self.table.setHorizontalHeaderLabels(["Author", "Title", "Language", "Chapters", "Chunks", "Status"])
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.setSortingEnabled(True)

            import_button = QPushButton("Import TXT/MD/EPUB")
            import_button.clicked.connect(self.import_file)
            calibre_button = QPushButton("Import from Calibre")
            calibre_button.clicked.connect(self.import_calibre)
            pdf_button = QPushButton("PDF/DOCX in M2")
            pdf_button.setEnabled(False)

            toolbar = QHBoxLayout()
            toolbar.addWidget(import_button)
            toolbar.addWidget(calibre_button)
            toolbar.addWidget(pdf_button)
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
                    book["chapter_count"],
                    book["chunk_count"],
                    book["status"],
                ]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    if col in {3, 4}:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(row, col, item)
            self.table.resizeColumnsToContents()
            self.table.setSortingEnabled(True)
            self.status.setText(f"{len(books)} books in {self.library.root}")

        def import_file(self) -> None:
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "Import source",
                str(Path.home()),
                "Supported Sources (*.txt *.md *.epub)",
            )
            if not file_name:
                return
            try:
                self.library.import_source(Path(file_name))
            except Exception as exc:
                self.status.setText(f"Import failed: {exc}")
                return
            self.refresh()

        def closeEvent(self, event) -> None:  # noqa: N802 - Qt API name
            self.library.close()
            super().closeEvent(event)

    app = QApplication(sys.argv[:1])
    window = MainWindow(args.library)
    window.show()
    return app.exec()
