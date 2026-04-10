from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import get_default_output_dir
from app.ui.components import SectionCard


class SettingsScreen(QWidget):
    save_requested = Signal(dict)
    reset_requested = Signal()
    refresh_cache_requested = Signal()

    page_title = "Configuracoes"
    page_badge = "Sistema"

    def __init__(self, config: dict) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self._root_layout = layout
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        title = QLabel("Configuracoes")
        title.setObjectName("title")
        layout.addWidget(title)

        intro = SectionCard(
            "Configuracoes gerais",
            "Ajuste base padrao e cache.",
            object_name="settingsPanel",
        )
        self.intro_card = intro
        intro_note = QLabel(
            "Essas opcoes nao alteram as regras de geracao."
        )
        intro_note.setObjectName("bodyMuted")
        intro_note.setWordWrap(True)
        intro.add_widget(intro_note)
        layout.addWidget(intro)

        data_card = SectionCard("Base padrao", "Valores usados ao abrir o app.")
        self.data_card = data_card
        data_form = QFormLayout()
        data_form.setSpacing(10)
        self.default_spreadsheet = QLineEdit(config.get("default_spreadsheet_path", ""))
        self.default_onedrive = QLineEdit(config.get("default_onedrive_url", ""))
        self.default_output = QLineEdit(str(get_default_output_dir()))
        self.default_output.setReadOnly(True)
        data_form.addRow("Planilha local padrao", self.default_spreadsheet)
        data_form.addRow("Link padrao OneDrive", self.default_onedrive)
        data_form.addRow("Pasta de saida", self.default_output)
        data_card.add_layout(data_form)
        layout.addWidget(data_card)

        cache_card = SectionCard("Cache", "Controle de validade e sincronizacao.")
        self.cache_card = cache_card
        cache_form = QFormLayout()
        cache_form.setSpacing(10)
        self.cache_ttl = QSpinBox()
        self.cache_ttl.setRange(1, 168)
        self.cache_ttl.setValue(int(config.get("cache_ttl_hours", 24)))
        cache_form.addRow("TTL do cache (horas)", self.cache_ttl)
        cache_card.add_layout(cache_form)
        btn_refresh = QPushButton("Atualizar base agora")
        btn_refresh.clicked.connect(self.refresh_cache_requested.emit)
        cache_actions = QHBoxLayout()
        cache_actions.addWidget(btn_refresh)
        cache_actions.addStretch(1)
        cache_card.add_layout(cache_actions)
        layout.addWidget(cache_card)

        button_row = QHBoxLayout()
        btn_save = QPushButton("Salvar configuracoes")
        btn_save.setObjectName("primary")
        btn_save.clicked.connect(self._emit_save)
        btn_reset = QPushButton("Restaurar padroes")
        btn_reset.clicked.connect(self.reset_requested.emit)
        btn_refresh_footer = QPushButton("Atualizar base agora")
        btn_refresh_footer.clicked.connect(self.refresh_cache_requested.emit)
        button_row.addWidget(btn_save)
        button_row.addWidget(btn_reset)
        button_row.addWidget(btn_refresh_footer)
        button_row.addStretch(1)
        layout.addLayout(button_row)
        layout.addStretch(1)

        self.load_config(config)

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

    def set_sidebar_collapsed(self, collapsed: bool) -> None:
        margin = 18 if collapsed else 22
        self._root_layout.setContentsMargins(margin, margin, margin, margin)
        self._root_layout.setSpacing(10 if collapsed else 14)
        self.intro_card.subtitle_label.setVisible(not collapsed)
        self.data_card.subtitle_label.setVisible(not collapsed)
        self.cache_card.subtitle_label.setVisible(not collapsed)
