from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ProgressScreen(QWidget):
    open_output_requested = Signal(str)
    reset_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._output_dir = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.title_label = QLabel("Progresso")
        self.title_label.setObjectName("title")
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("")
        self.subtitle_label.setObjectName("muted")
        layout.addWidget(self.subtitle_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.counter_label = QLabel("0 de 0")
        self.counter_label.setObjectName("muted")
        layout.addWidget(self.counter_label)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log_box, 1)

        button_row = QHBoxLayout()
        self.btn_open = QPushButton("Abrir pasta de saída")
        self.btn_open.clicked.connect(self._emit_open_output)
        self.btn_reset = QPushButton("Nova geração")
        self.btn_reset.clicked.connect(self.reset_requested.emit)
        button_row.addWidget(self.btn_open)
        button_row.addWidget(self.btn_reset)
        button_row.addStretch(1)
        layout.addLayout(button_row)

    def set_context(self, title: str, subtitle: str) -> None:
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)

    def update_progress(self, current: int, total: int, name: str = "") -> None:
        percent = 0 if total <= 0 else int((current / total) * 100)
        self.progress_bar.setValue(percent)
        label = f"{current} de {total}"
        if name:
            label = f"{label} - {name}"
        self.counter_label.setText(label)

    def append_log(self, message: str, level: str = "info") -> None:
        prefixes = {
            "success": "✓",
            "warning": "!",
            "error": "✗",
            "info": "•",
        }
        self.log_box.append(f"{prefixes.get(level, '•')} {message}")

    def on_complete(self, output_dir: str, count: int, elapsed: str) -> None:
        self._output_dir = output_dir
        self.append_log(
            f"Concluído. {count} arquivo(s) gerado(s) em {elapsed}.", "success"
        )
        self.append_log(
            "Abra os arquivos .pptx e insira as fotos nos círculos brancos.",
            "info",
        )

    def reset(self) -> None:
        self._output_dir = ""
        self.progress_bar.setValue(0)
        self.counter_label.setText("0 de 0")
        self.log_box.clear()

    def _emit_open_output(self) -> None:
        if self._output_dir:
            self.open_output_requested.emit(self._output_dir)
