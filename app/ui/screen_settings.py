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
    browse_base_requested = Signal()
    refresh_cache_requested = Signal()

    page_title = "Configuracoes"
    page_badge = "Sistema"

    def __init__(self, config: dict) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self._root_layout = layout
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        intro = SectionCard(
            "Configuracoes gerais",
            "Ajuste base padrao e cache.",
            object_name="settingsPanel",
        )
        self.intro_card = intro
        intro_note = QLabel("Essas opcoes nao alteram as regras de geracao.")
        intro_note.setObjectName("bodyMuted")
        intro_note.setWordWrap(True)
        intro.add_widget(intro_note)
        layout.addWidget(intro)

        data_card = SectionCard("Base padrao", "Valores usados ao abrir o app.")
        self.data_card = data_card
        data_form = QFormLayout()
        data_form.setSpacing(10)
        self.default_spreadsheet = QLineEdit(config.get("default_spreadsheet_path", ""))
        self.default_spreadsheet.setReadOnly(True)
        self.default_output = QLineEdit(str(get_default_output_dir()))
        self.default_output.setReadOnly(True)
        data_form.addRow("Planilha local padrao", self.default_spreadsheet)
        data_form.addRow("Pasta de saida", self.default_output)
        data_card.add_layout(data_form)
        layout.addWidget(data_card)

        cache_card = SectionCard("Cache", "Controle de validade e sincronizacao.")
        self.cache_card = cache_card
        self.base_name_label = QLabel("Nenhuma base configurada")
        self.base_name_label.setObjectName("sectionTitle")
        self.base_path_label = QLabel("")
        self.base_path_label.setObjectName("bodyMuted")
        self.base_path_label.setWordWrap(True)
        self.base_status_label = QLabel("")
        self.base_status_label.setObjectName("statusLabel")
        self.base_status_label.setWordWrap(True)
        cache_card.add_widget(self.base_name_label)
        cache_card.add_widget(self.base_path_label)
        cache_card.add_widget(self.base_status_label)
        cache_form = QFormLayout()
        cache_form.setSpacing(10)
        self.cache_ttl = QSpinBox()
        self.cache_ttl.setRange(1, 168)
        self.cache_ttl.setValue(int(config.get("cache_ttl_hours", 24)))
        cache_form.addRow("TTL do cache (horas)", self.cache_ttl)
        cache_card.add_layout(cache_form)
        btn_browse = QPushButton("Procurar arquivo")
        btn_browse.clicked.connect(self.browse_base_requested.emit)
        btn_refresh = QPushButton("Atualizar base agora")
        btn_refresh.clicked.connect(self.refresh_cache_requested.emit)
        cache_actions = QHBoxLayout()
        cache_actions.addWidget(btn_browse)
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
        button_row.addWidget(btn_save)
        button_row.addWidget(btn_reset)
        button_row.addStretch(1)
        layout.addLayout(button_row)
        layout.addStretch(1)

        self.load_config(config)

    def load_config(self, config: dict) -> None:
        self.default_spreadsheet.setText(config.get("default_spreadsheet_path", ""))
        self.default_output.setText(str(get_default_output_dir()))
        self.cache_ttl.setValue(int(config.get("cache_ttl_hours", 24)))
        self._update_base_summary(config)

    def _update_base_summary(self, config: dict) -> None:
        path = str(config.get("default_spreadsheet_path", "")).strip()
        name = str(config.get("default_spreadsheet_name", "")).strip()
        row_count = int(config.get("default_base_row_count", 0) or 0)
        status = str(config.get("default_base_status", "")).strip()
        cache_path = str(config.get("default_base_cache_path", "")).strip()
        if path == "":
            self.base_name_label.setText("Nenhuma base configurada")
            self.base_path_label.setText("")
            self.base_status_label.setText(
                "Sem base configurada. Use Procurar arquivo para selecionar uma planilha."
            )
            self.base_status_label.setProperty("state", "warning")
            return

        self.base_name_label.setText(name or "Base selecionada")
        self.base_path_label.setText(path)
        if status == "missing":
            message = (
                "Arquivo original nao encontrado. Selecione outra planilha."
                if row_count == 0
                else f"Arquivo original nao encontrado. Cache preservado com {row_count} linha(s)."
            )
            state = "error"
        elif status == "modified":
            message = (
                "Arquivo modificado. Atualize a base para usar os dados mais recentes."
            )
            state = "warning"
        elif status == "invalid":
            message = "Planilha invalida. O ultimo cache valido foi preservado."
            state = "error"
        elif status == "updated":
            message = f"Base atualizada. {row_count} linha(s) em cache."
            state = "success"
        elif status == "ready":
            message = f"Base pronta. {row_count} linha(s) em cache."
            state = "success"
        elif cache_path:
            message = f"Base pronta. {row_count} linha(s) em cache."
            state = "success"
        else:
            message = (
                f"Base selecionada. {row_count} linha(s) registradas no ultimo cache."
                if row_count
                else "Base selecionada. Atualize o cache antes de usar."
            )
            state = "info"
        self.base_status_label.setText(message)
        self.base_status_label.setProperty("state", state)

    def _emit_save(self) -> None:
        self.save_requested.emit(
            {
                "default_spreadsheet_path": self.default_spreadsheet.text().strip(),
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
