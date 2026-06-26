from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .library import BookLibrary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bookcast-ui")
    parser.add_argument("--library", type=Path, default=Path.cwd() / "library")
    args = parser.parse_args(argv)

    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QApplication,
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
            pdf_button = QPushButton("PDF/DOCX in M2")
            pdf_button.setEnabled(False)

            toolbar = QHBoxLayout()
            toolbar.addWidget(import_button)
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

