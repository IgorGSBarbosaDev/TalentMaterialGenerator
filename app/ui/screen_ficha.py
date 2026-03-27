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
            "matricula",
            "nome",
            "idade",
            "cargo",
            "antiguidade",
            "formacao",
            "resumo_perfil",
            "trajetoria",
            "nota_2025",
            "nota_2024",
            "nota_2023",
            "performance",
        ]
        self.column_labels = {
            "matricula": "Matricula",
            "nome": "Nome*",
            "idade": "Idade",
            "cargo": "Cargo*",
            "antiguidade": "Antiguidade",
            "formacao": "Formacao",
            "resumo_perfil": "Resumo de Perfil",
            "trajetoria": "Trajetoria",
            "nota_2025": "Nota 2025",
            "nota_2024": "Nota 2024",
            "nota_2023": "Nota 2023",
            "performance": "Performance",
        }
        self.column_mapping: dict[str, str | None] = {
            field: None for field in self.column_fields
        }
        self._column_selectors: dict[str, QComboBox] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Ficha de Curriculo")
        title.setObjectName("title")
        layout.addWidget(title)

        self.source_type = QComboBox()
        self.source_type.addItems(["OneDrive", "Arquivo local"])
        if config.get("spreadsheet_source") == "local":
            self.source_type.setCurrentText("Arquivo local")

        self.entry_source = QLineEdit(config.get("default_onedrive_url", ""))
        self.entry_output = QLineEdit(str(get_default_output_dir()))
        self.entry_output.setReadOnly(True)
        self.output_mode = QComboBox()
        self.output_mode.addItems(["one_file_per_employee", "single_deck"])
        self.output_mode.setCurrentText(
            config.get("default_output_mode", "one_file_per_employee")
        )
        self.status_label = QLabel("")
        self.status_label.setObjectName("muted")

        source_panel = QFrame()
        source_panel.setObjectName("panel")
        source_form = QFormLayout(source_panel)
        source_form.addRow("Fonte", self.source_type)
        source_form.addRow("Planilha/Link", self.entry_source)
        source_form.addRow("Saida", self.entry_output)
        source_form.addRow("Modo de saida", self.output_mode)
        layout.addWidget(source_panel)

        actions = QHBoxLayout()
        btn_browse_file = QPushButton("Procurar arquivo")
        btn_browse_file.clicked.connect(self._choose_source_file)
        btn_detect = QPushButton("Auto-detectar")
        btn_detect.clicked.connect(self._auto_detect_columns)
        actions.addWidget(btn_browse_file)
        actions.addWidget(btn_detect)
        actions.addStretch(1)
        layout.addLayout(actions)
        layout.addWidget(self.status_label)

        mapping_panel = QFrame()
        mapping_panel.setObjectName("panel")
        mapping_form = QFormLayout(mapping_panel)
        for field in self.column_fields:
            combo = QComboBox()
            combo.addItem("")
            self._column_selectors[field] = combo
            mapping_form.addRow(self.column_labels[field], combo)
        layout.addWidget(mapping_panel)

        self.preview_label = QLabel(
            "Preview: ficha no template oficial com placeholder circular."
        )
        self.preview_label.setWordWrap(True)
        self.preview_label.setObjectName("dim")
        layout.addWidget(self.preview_label)

        self.btn_generate = QPushButton("GERAR FICHAS")
        self.btn_generate.setObjectName("primary")
        self.btn_generate.clicked.connect(self._start_generation)
        layout.addWidget(self.btn_generate)
        layout.addStretch(1)

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
            self.status_label.setText("Informe a fonte de dados.")
            return False

        if self.source_type.currentText() == "Arquivo local" and not Path(source).is_file():
            self.status_label.setText("A planilha local nao foi encontrada.")
            return False

        if self.source_type.currentText() == "OneDrive" and not source.startswith("https://"):
            self.status_label.setText("Informe um link valido do OneDrive.")
            return False

        missing_required = reader.validate_required_columns(self._get_column_mapping())
        if missing_required:
            self.status_label.setText(
                f"Mapeie os campos obrigatorios: {', '.join(missing_required)}."
            )
            return False

        self.status_label.setText("Configuracao valida.")
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
            self.status_label.setText("Informe a fonte antes da auto-deteccao.")
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
            self.status_label.setText("Colunas detectadas.")
        except Exception as exc:
            self.status_label.setText(str(exc))

    def _start_generation(self) -> None:
        if not self._validate_inputs():
            return
        self.generate_requested.emit(self._get_config())
