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
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
    QVBoxLayout,
)

from app.core import reader


class CaromScreen(QWidget):
    generate_requested = Signal(dict)

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__()
        self.column_fields = ["nome", "cargo", "area", "nota", "potencial"]
        self._column_selectors: dict[str, QComboBox] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Carômetro")
        title.setObjectName("title")
        layout.addWidget(title)

        self.source_type = QComboBox()
        self.source_type.addItems(["OneDrive", "Arquivo local"])
        if config.get("spreadsheet_source") == "local":
            self.source_type.setCurrentText("Arquivo local")

        self.entry_source = QLineEdit(config.get("default_onedrive_url", ""))
        self.entry_output = QLineEdit(config.get("default_output_dir", ""))
        self.grouping = QComboBox()
        self.grouping.addItems(["area", "cargo", "potencial", "sem agrupamento"])
        self.columns = QComboBox()
        self.columns.addItems(["3", "4", "5"])
        self.columns.setCurrentText(str(config.get("default_carom_columns", 5)))
        self.title_field = QLineEdit("Carômetro")
        self.status_label = QLabel("")
        self.status_label.setObjectName("muted")

        self.chk_show_nota = QCheckBox("Mostrar nota")
        self.chk_show_nota.setChecked(True)
        self.chk_show_potencial = QCheckBox("Mostrar potencial")
        self.chk_show_potencial.setChecked(True)
        self.chk_show_cargo = QCheckBox("Mostrar cargo")
        self.chk_show_cargo.setChecked(True)
        self.chk_cores = QCheckBox("Cores automáticas")
        self.chk_cores.setChecked(True)

        source_panel = QFrame()
        source_panel.setObjectName("panel")
        source_form = QFormLayout(source_panel)
        source_form.addRow("Fonte", self.source_type)
        source_form.addRow("Planilha/Link", self.entry_source)
        source_form.addRow("Saída", self.entry_output)
        source_form.addRow("Agrupamento", self.grouping)
        source_form.addRow("Colunas", self.columns)
        source_form.addRow("Título", self.title_field)
        layout.addWidget(source_panel)

        actions = QHBoxLayout()
        btn_browse_file = QPushButton("Procurar arquivo")
        btn_browse_file.clicked.connect(self._choose_source_file)
        btn_browse_output = QPushButton("Procurar saída")
        btn_browse_output.clicked.connect(self._choose_output_dir)
        btn_detect = QPushButton("Auto-detectar")
        btn_detect.clicked.connect(self._auto_detect_columns)
        actions.addWidget(btn_browse_file)
        actions.addWidget(btn_browse_output)
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
            mapping_form.addRow(field.capitalize(), combo)
        layout.addWidget(mapping_panel)

        toggles = QHBoxLayout()
        toggles.addWidget(self.chk_show_nota)
        toggles.addWidget(self.chk_show_potencial)
        toggles.addWidget(self.chk_show_cargo)
        toggles.addWidget(self.chk_cores)
        toggles.addStretch(1)
        layout.addLayout(toggles)

        self.btn_generate = QPushButton("GERAR CARÔMETRO")
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
        self.entry_output.setText(config.get("default_output_dir", ""))
        self.columns.setCurrentText(str(config.get("default_carom_columns", 5)))

    def _choose_source_file(self) -> None:
        file_path, _filter = QFileDialog.getOpenFileName(
            self, "Selecionar planilha", "", "Excel (*.xlsx)"
        )
        if file_path:
            self.source_type.setCurrentText("Arquivo local")
            self.entry_source.setText(file_path)

    def _choose_output_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Selecionar pasta de saída")
        if directory:
            self.entry_output.setText(directory)

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

    def _get_column_mapping(self) -> dict[str, str | None]:
        return {
            field: combo.currentText() or None
            for field, combo in self._column_selectors.items()
        }

    def _validate_inputs(self) -> bool:
        source = self.entry_source.text().strip()
        output_dir = self.entry_output.text().strip()
        if source == "" or output_dir == "":
            self.status_label.setText("Informe a fonte de dados e a pasta de saída.")
            return False

        if self.source_type.currentText() == "Arquivo local" and not Path(source).is_file():
            self.status_label.setText("A planilha local não foi encontrada.")
            return False

        if self.source_type.currentText() == "OneDrive" and not source.startswith("https://"):
            self.status_label.setText("Informe um link válido do OneDrive.")
            return False

        missing_required = reader.validate_required_columns(self._get_column_mapping())
        if missing_required:
            self.status_label.setText(
                f"Mapeie os campos obrigatórios: {', '.join(missing_required)}."
            )
            return False

        self.status_label.setText("Configuração válida.")
        return True

    def _auto_detect_columns(self) -> None:
        source = self.entry_source.text().strip()
        if source == "":
            self.status_label.setText("Informe a fonte antes da auto-detecção.")
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

        grouping = self.grouping.currentText()
        self.generate_requested.emit(
            {
                "spreadsheet_source": self.entry_source.text().strip(),
                "source_kind": "local"
                if self.source_type.currentText() == "Arquivo local"
                else "onedrive",
                "output_dir": self.entry_output.text().strip(),
                "column_mapping": self._get_column_mapping(),
                "agrupamento": None if grouping == "sem agrupamento" else grouping,
                "colunas": int(self.columns.currentText()),
                "titulo": self.title_field.text().strip() or "Carômetro",
                "show_nota": self.chk_show_nota.isChecked(),
                "show_potencial": self.chk_show_potencial.isChecked(),
                "show_cargo": self.chk_show_cargo.isChecked(),
                "cores_automaticas": self.chk_cores.isChecked(),
            }
        )
