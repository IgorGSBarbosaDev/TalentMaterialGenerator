from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import get_default_output_dir
from app.core import reader


class FichaScreen(QWidget):
    generate_requested = Signal(dict)

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__()
        self.column_fields = [
            "nome",
            "idade",
            "cargo",
            "antiguidade",
            "formacao",
            "resumo_perfil",
            "trajetoria",
            "performance",
        ]
        self.column_labels = {
            "nome": "Nome*",
            "idade": "Idade",
            "cargo": "Cargo*",
            "antiguidade": "Antiguidade",
            "formacao": "Formacao",
            "resumo_perfil": "Resumo de perfil",
            "trajetoria": "Trajetoria",
            "performance": "Performance",
        }
        self._column_selectors: dict[str, QComboBox] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(16)

        title = QLabel("Ficha de Curriculo")
        title.setObjectName("title")
        subtitle = QLabel(
            "Configure a base e o mapeamento em paines amplos para gerar fichas com menos atrito."
        )
        subtitle.setObjectName("muted")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        split = QHBoxLayout()
        split.setSpacing(16)
        layout.addLayout(split, 1)

        source_panel = QFrame()
        source_panel.setObjectName("panel")
        source_layout = QVBoxLayout(source_panel)
        source_layout.setContentsMargins(18, 18, 18, 18)
        source_layout.setSpacing(14)
        source_layout.addWidget(self._panel_title("Fonte de dados"))
        source_layout.addWidget(
            self._panel_hint("Defina origem, saida e modo de geracao em um unico bloco.")
        )

        self.source_type = QComboBox()
        self.source_type.addItems(["OneDrive", "Arquivo local"])
        if config.get("spreadsheet_source") == "local":
            self.source_type.setCurrentText("Arquivo local")

        self.entry_source = QLineEdit(config.get("default_onedrive_url", ""))
        self.entry_source.setMinimumWidth(360)
        self.entry_output = QLineEdit(str(get_default_output_dir()))
        self.entry_output.setReadOnly(True)
        self.output_mode = QComboBox()
        self.output_mode.addItems(["one_file_per_employee", "single_deck"])
        self.output_mode.setCurrentText(
            config.get("default_output_mode", "one_file_per_employee")
        )

        source_form = QFormLayout()
        source_form.setHorizontalSpacing(16)
        source_form.setVerticalSpacing(12)
        source_form.addRow("Fonte", self.source_type)
        source_form.addRow("Planilha/Link", self.entry_source)
        source_form.addRow("Saida", self.entry_output)
        source_form.addRow("Modo de saida", self.output_mode)
        source_layout.addLayout(source_form)

        actions = QHBoxLayout()
        btn_browse_file = QPushButton("Procurar arquivo")
        btn_browse_file.clicked.connect(self._choose_source_file)
        btn_detect = QPushButton("Auto-detectar")
        btn_detect.clicked.connect(self._auto_detect_columns)
        actions.addWidget(btn_browse_file)
        actions.addWidget(btn_detect)
        actions.addStretch(1)
        source_layout.addLayout(actions)
        split.addWidget(source_panel, 5)

        mapping_panel = QFrame()
        mapping_panel.setObjectName("panel")
        mapping_layout = QVBoxLayout(mapping_panel)
        mapping_layout.setContentsMargins(18, 18, 18, 18)
        mapping_layout.setSpacing(14)
        mapping_layout.addWidget(self._panel_title("Mapeamento de colunas"))
        mapping_layout.addWidget(
            self._panel_hint("Mapeie os campos obrigatorios e revise os complementares.")
        )

        mapping_form = QFormLayout()
        mapping_form.setHorizontalSpacing(16)
        mapping_form.setVerticalSpacing(10)
        for field in self.column_fields:
            combo = QComboBox()
            combo.addItem("")
            combo.setMinimumWidth(340)
            self._column_selectors[field] = combo
            mapping_form.addRow(self.column_labels[field], combo)
        mapping_layout.addLayout(mapping_form)
        split.addWidget(mapping_panel, 5)

        action_panel = QFrame()
        action_panel.setObjectName("panelAction")
        action_layout = QHBoxLayout(action_panel)
        action_layout.setContentsMargins(18, 16, 18, 16)
        action_layout.setSpacing(14)

        status_col = QVBoxLayout()
        status_col.setSpacing(6)
        status_title = self._panel_title("Acao final")
        status_title.setObjectName("panelTitle")
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        status_col.addWidget(status_title)
        status_col.addWidget(self.status_label)
        action_layout.addLayout(status_col, 1)

        self.btn_generate = QPushButton("GERAR FICHAS")
        self.btn_generate.setObjectName("primary")
        self.btn_generate.clicked.connect(self._start_generation)
        self.btn_generate.setMinimumWidth(210)
        action_layout.addWidget(self.btn_generate)
        layout.addWidget(action_panel)

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
        self.output_mode.setCurrentText(
            config.get("default_output_mode", "one_file_per_employee")
        )

    def _choose_source_file(self) -> None:
        file_path, _filter = QFileDialog.getOpenFileName(
            self, "Selecionar planilha", "", "Excel (*.xlsx)"
        )
        if file_path:
            self.source_type.setCurrentText("Arquivo local")
            self.entry_source.setText(file_path)

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

    def _validate_inputs(self) -> bool:
        source = self.entry_source.text().strip()
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
        if missing_required:
            self._set_status(
                f"Mapeie os campos obrigatorios: {', '.join(missing_required)}.",
                "warning",
            )
            return False

        self._set_status("Configuracao valida. Pronto para gerar.", "success")
        return True

    def _get_column_mapping(self) -> dict[str, str | None]:
        return {
            field: combo.currentText() or None
            for field, combo in self._column_selectors.items()
        }

    def _get_config(self) -> dict[str, Any]:
        source_kind = (
            "local" if self.source_type.currentText() == "Arquivo local" else "onedrive"
        )
        return {
            "spreadsheet_source": self.entry_source.text().strip(),
            "source_kind": source_kind,
            "output_dir": str(get_default_output_dir()),
            "column_mapping": self._get_column_mapping(),
            "output_mode": self.output_mode.currentText(),
        }

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
        self.generate_requested.emit(self._get_config())
