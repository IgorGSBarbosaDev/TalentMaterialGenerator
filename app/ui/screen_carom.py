from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import get_default_output_dir
from app.core import reader
from app.ui.components import repolish


class CaromScreen(QWidget):
    generate_requested = Signal(dict)

    page_title = "Carometro"
    page_subtitle = "Agrupamento, layout do grid e preview dos cards"
    page_badge = "Grid"

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__()
        self.column_fields = [
            "matricula",
            "nome",
            "cargo",
            "area",
            "nota",
            "potencial",
            "nota_2025",
            "nota_2024",
            "nota_2023",
        ]
        self._column_selectors: dict[str, QComboBox] = {}
        self._preview_rows: list[dict[str, str]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(16)

        title = QLabel("Carometro")
        title.setObjectName("title")
        subtitle = QLabel(
            "Distribua melhor as configuracoes de grade sem reservar area para exemplos de colaboradores."
        )
        subtitle.setObjectName("muted")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        top_split = QHBoxLayout()
        top_split.setSpacing(16)
        layout.addLayout(top_split, 1)

        source_panel = QFrame()
        source_panel.setObjectName("panel")
        source_layout = QVBoxLayout(source_panel)
        source_layout.setContentsMargins(18, 18, 18, 18)
        source_layout.setSpacing(14)
        source_layout.addWidget(self._panel_title("Fonte e layout"))
        source_layout.addWidget(
            self._panel_hint("Configure origem da base, agrupamento e dimensao da grade.")
        )

        self.source_type = QComboBox()
        self.source_type.addItems(["OneDrive", "Arquivo local"])
        self.source_type.currentTextChanged.connect(self._sync_source_mode)
        self.source_type.currentTextChanged.connect(self._refresh_preview)

        self.entry_source = QLineEdit(config.get("default_onedrive_url", ""))
        self.entry_source.setMinimumWidth(350)
        self.entry_source.textChanged.connect(self._on_source_changed)
        self.entry_output = QLineEdit(str(get_default_output_dir()))
        self.entry_output.setReadOnly(True)
        self.grouping = QComboBox()
        self.grouping.addItems(["area", "cargo", "potencial", "sem agrupamento"])
        self.grouping.currentTextChanged.connect(self._refresh_preview)
        self.title_field = QLineEdit("Carometro")
        self.title_field.textChanged.connect(self._refresh_preview)
        self.columns = QComboBox()
        self.columns.addItems(["3", "4", "5"])
        self.columns.setCurrentText(str(config.get("default_carom_columns", 5)))
        self.columns.currentTextChanged.connect(self._refresh_preview)

        source_form = QFormLayout()
        source_form.setHorizontalSpacing(16)
        source_form.setVerticalSpacing(12)
        source_form.addRow("Fonte", self.source_type)
        source_form.addRow("Planilha/Link", self.entry_source)
        source_form.addRow("Saida", self.entry_output)
        source_form.addRow("Agrupamento", self.grouping)
        source_form.addRow("Colunas", self.columns)
        source_form.addRow("Titulo", self.title_field)
        source_layout.addLayout(source_form)

        source_actions = QHBoxLayout()
        self.btn_browse_file = QPushButton("Procurar arquivo")
        self.btn_browse_file.clicked.connect(self._choose_source_file)
        btn_detect = QPushButton("Auto-detectar")
        btn_detect.clicked.connect(self._auto_detect_columns)
        source_actions.addWidget(self.btn_browse_file)
        source_actions.addWidget(btn_detect)
        source_actions.addStretch(1)
        source_layout.addLayout(source_actions)
        top_split.addWidget(source_panel, 5)

        mapping_panel = QFrame()
        mapping_panel.setObjectName("panel")
        mapping_layout = QVBoxLayout(mapping_panel)
        mapping_layout.setContentsMargins(18, 18, 18, 18)
        mapping_layout.setSpacing(14)
        mapping_layout.addWidget(self._panel_title("Mapeamento"))
        mapping_layout.addWidget(
            self._panel_hint("Mantenha nome e cargo obrigatorios para liberar a geracao.")
        )

        mapping_form = QFormLayout()
        mapping_form.setHorizontalSpacing(16)
        mapping_form.setVerticalSpacing(10)
        for field in self.column_fields:
            combo = QComboBox()
            combo.addItem("")
            combo.setMinimumWidth(300)
            self._column_selectors[field] = combo
            mapping_form.addRow(field.capitalize(), combo)
        mapping_layout.addLayout(mapping_form)
        top_split.addWidget(mapping_panel, 5)

        action_split = QHBoxLayout()
        action_split.setSpacing(16)
        layout.addLayout(action_split)

        options_panel = QFrame()
        options_panel.setObjectName("panel")
        options_layout = QVBoxLayout(options_panel)
        options_layout.setContentsMargins(18, 18, 18, 18)
        options_layout.setSpacing(14)
        options_layout.addWidget(self._panel_title("Exibicao do card"))
        options_layout.addWidget(
            self._panel_hint("Ajuste quais dados aparecem no card final do carometro.")
        )

        self.chk_show_nota = QCheckBox("Mostrar nota")
        self.chk_show_nota.setChecked(True)
        self.chk_show_potencial = QCheckBox("Mostrar potencial")
        self.chk_show_potencial.setChecked(True)
        self.chk_show_cargo = QCheckBox("Mostrar cargo")
        self.chk_show_cargo.setChecked(True)
        self.chk_cores = QCheckBox("Cores automaticas")
        self.chk_cores.setChecked(True)

        toggles_grid = QGridLayout()
        toggles_grid.setHorizontalSpacing(18)
        toggles_grid.setVerticalSpacing(8)
        toggles_grid.addWidget(self.chk_show_nota, 0, 0)
        toggles_grid.addWidget(self.chk_show_potencial, 0, 1)
        toggles_grid.addWidget(self.chk_show_cargo, 1, 0)
        toggles_grid.addWidget(self.chk_cores, 1, 1)
        options_layout.addLayout(toggles_grid)
        action_split.addWidget(options_panel, 7)

        action_panel = QFrame()
        action_panel.setObjectName("panelAction")
        action_layout = QVBoxLayout(action_panel)
        action_layout.setContentsMargins(18, 16, 18, 16)
        action_layout.setSpacing(10)
        action_layout.addWidget(self._panel_title("Acao final"))
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        action_layout.addWidget(self.status_label)
        self.btn_generate = QPushButton("GERAR CAROMETRO")
        self.btn_generate.setObjectName("primary")
        self.btn_generate.clicked.connect(self._start_generation)
        action_layout.addWidget(self.btn_generate)
        action_layout.addStretch(1)
        action_split.addWidget(action_panel, 3)

        self._sync_source_mode()
        self._set_status("Informe a fonte de dados para iniciar.", "info")

    def _panel_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("panelTitle")
        return label

    def _panel_hint(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("panelHint")
        label.setWordWrap(True)
        return label

    def _set_status(self, message: str, state: str) -> None:
        self.status_label.setText(message)
        self.status_label.setProperty("state", state)
        style = self.status_label.style()
        if style is not None:
            style.unpolish(self.status_label)
            style.polish(self.status_label)
        self.status_label.update()

    def load_config(self, config: dict[str, Any]) -> None:
        source_kind = str(config.get("spreadsheet_source", "onedrive")).lower()
        self.source_type.setCurrentText(
            "Arquivo local" if source_kind == "local" else "OneDrive"
        )
        self.entry_source.setText(
            config.get("default_spreadsheet_path", "")
            if source_kind == "local"
            else config.get("default_onedrive_url", "")
        )
        self.entry_output.setText(str(get_default_output_dir()))
        self.grouping.setCurrentText(str(config.get("default_grouping", "area")))
        self.columns.setCurrentText(str(config.get("default_carom_columns", 5)))
        self.title_field.setText("Carometro")
        self._refresh_required_states()
        self._refresh_preview()

    def _choose_source_file(self) -> None:
        file_path, _filter = QFileDialog.getOpenFileName(
            self, "Selecionar planilha", "", "Excel (*.xlsx)"
        )
        if file_path:
            self.source_type.setCurrentText("Arquivo local")
            self.entry_source.setText(file_path)

    def _sync_source_mode(self) -> None:
        local_mode = self.source_type.currentText() == "Arquivo local"
        self.btn_browse_file.setEnabled(local_mode)
        self.entry_source.setPlaceholderText(
            "C:\\dados\\colaboradores.xlsx"
            if local_mode
            else "https://... link compartilhado do OneDrive"
        )

    def _on_source_changed(self) -> None:
        self._set_invalid(self.entry_source, False)
        self._refresh_preview()

    def _populate_column_selectors(self, headers: list[str]) -> None:
        for combo in self._column_selectors.values():
            current = combo.currentText()
            combo.clear()
            combo.addItem("")
            combo.addItems(headers)
            if current:
                index = combo.findText(current)
                if index >= 0:
                    combo.setCurrentIndex(index)

    def _set_invalid(self, widget: QWidget, is_invalid: bool) -> None:
        widget.setProperty("invalid", is_invalid)
        repolish(widget)

    def _refresh_required_states(self) -> None:
        for field in ("nome", "cargo"):
            combo = self._column_selectors[field]
            self._set_invalid(combo, combo.currentText().strip() == "")

    def _refresh_preview(self) -> None:
        if self._preview_rows:
            self._set_status(
                f"Preview carregado: {len(self._preview_rows)} colaborador(es).", "info"
            )
            return

        source = self.entry_source.text().strip()
        if source:
            self._set_status(
                "Fonte configurada. Use Auto-detectar para validar o mapeamento.", "info"
            )

    def _get_column_mapping(self) -> dict[str, str | None]:
        return {
            field: combo.currentText() or None
            for field, combo in self._column_selectors.items()
        }

    def _validate_inputs(self) -> bool:
        source = self.entry_source.text().strip()
        self._set_invalid(self.entry_source, source == "")
        if source == "":
            self._set_status("Informe a fonte de dados.", "warning")
            return False

        if self.source_type.currentText() == "Arquivo local" and not Path(source).is_file():
            self._set_status("A planilha local nao foi encontrada.", "error")
            return False

        if self.source_type.currentText() == "OneDrive" and not source.startswith("https://"):
            self._set_status("Informe um link valido do OneDrive.", "error")
            return False

        missing_required = reader.validate_required_columns(self._get_column_mapping())
        self._refresh_required_states()
        if missing_required:
            self._set_status(
                f"Mapeie os campos obrigatorios: {', '.join(missing_required)}.",
                "warning",
            )
            return False

        self._set_status("Configuracao valida. Pronto para gerar.", "success")
        return True

    def _auto_detect_columns(self) -> None:
        source = self.entry_source.text().strip()
        if source == "":
            self._set_status("Informe a fonte antes da auto-deteccao.", "warning")
            return

        try:
            if self.source_type.currentText() == "Arquivo local":
                detected = reader.detect_columns_from_source(source)
                rows = reader.read_spreadsheet(source)
            else:
                result = reader.resolve_spreadsheet_source(source)
                detected = reader.detect_columns_from_source(result.path)
                rows = reader.read_spreadsheet(result.path)

            headers = list(rows[0].keys()) if rows else []
            self._preview_rows = rows
            self._populate_column_selectors(headers)
            for field, value in detected.items():
                combo = self._column_selectors.get(field)
                if combo is not None and value:
                    idx = combo.findText(value)
                    if idx >= 0:
                        combo.setCurrentIndex(idx)
            self._set_status("Colunas detectadas com sucesso.", "success")
        except Exception as exc:
            self._set_status(str(exc), "error")

    def _start_generation(self) -> None:
        if not self._validate_inputs():
            return

        grouping = self.grouping.currentText()
        self.generate_requested.emit(
            {
                "spreadsheet_source": self.entry_source.text().strip(),
                "source_kind": "local"
                if self.source_type.currentText() == "Arquivo local"
                else "onedrive",
                "output_dir": str(get_default_output_dir()),
                "column_mapping": self._get_column_mapping(),
                "agrupamento": None if grouping == "sem agrupamento" else grouping,
                "colunas": int(self.columns.currentText()),
                "titulo": self.title_field.text().strip() or "Carometro",
                "show_nota": self.chk_show_nota.isChecked(),
                "show_potencial": self.chk_show_potencial.isChecked(),
                "show_cargo": self.chk_show_cargo.isChecked(),
                "cores_automaticas": self.chk_cores.isChecked(),
            }
        )
