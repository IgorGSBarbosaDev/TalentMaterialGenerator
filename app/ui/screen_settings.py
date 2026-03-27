from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import get_default_output_dir


class SettingsScreen(QWidget):
    save_requested = Signal(dict)
    reset_requested = Signal()
    refresh_cache_requested = Signal()

    def __init__(self, config: dict) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Configuracoes")
        title.setObjectName("title")
        layout.addWidget(title)

        panel = QFrame()
        panel.setObjectName("panel")
        form = QFormLayout(panel)

        self.default_spreadsheet = QLineEdit(config.get("default_spreadsheet_path", ""))
        self.default_onedrive = QLineEdit(config.get("default_onedrive_url", ""))
        self.default_output = QLineEdit(str(get_default_output_dir()))
        self.default_output.setReadOnly(True)
        self.cache_ttl = QSpinBox()
        self.cache_ttl.setRange(1, 168)
        self.cache_ttl.setValue(int(config.get("cache_ttl_hours", 24)))

        form.addRow("Planilha local padrao", self.default_spreadsheet)
        form.addRow("Link padrao OneDrive", self.default_onedrive)
        form.addRow("Pasta de saida padrao", self.default_output)
        form.addRow("TTL cache (horas)", self.cache_ttl)
        layout.addWidget(panel)

        button_row = QHBoxLayout()
        btn_save = QPushButton("Salvar")
        btn_save.setObjectName("primary")
        btn_save.clicked.connect(self._emit_save)
        btn_reset = QPushButton("Restaurar padroes")
        btn_reset.clicked.connect(self.reset_requested.emit)
        btn_refresh = QPushButton("Atualizar base agora")
        btn_refresh.clicked.connect(self.refresh_cache_requested.emit)

        button_row.addWidget(btn_save)
        button_row.addWidget(btn_reset)
        button_row.addWidget(btn_refresh)
        button_row.addStretch(1)
        layout.addLayout(button_row)
        layout.addStretch(1)

    def load_config(self, config: dict) -> None:
        self.default_spreadsheet.setText(config.get("default_spreadsheet_path", ""))
        self.default_onedrive.setText(config.get("default_onedrive_url", ""))
        self.default_output.setText(str(get_default_output_dir()))
        self.cache_ttl.setValue(int(config.get("cache_ttl_hours", 24)))

    def _emit_save(self) -> None:
        self.save_requested.emit(
            {
                "default_spreadsheet_path": self.default_spreadsheet.text().strip(),
                "default_onedrive_url": self.default_onedrive.text().strip(),
                "cache_ttl_hours": self.cache_ttl.value(),
            }
        )
