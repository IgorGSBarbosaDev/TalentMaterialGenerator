from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
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
from app.ui.components import (
    PreviewListItem,
    SectionCard,
    StatusBadge,
    build_badge_row,
    clear_layout,
    repolish,
)


class CaromScreen(QWidget):
    generate_requested = Signal(dict)

    page_title = "Carometro"
    page_subtitle = "Agrupamento, layout do grid e preview dos cards"
    page_badge = "Grid"

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__()
        self.column_fields = ["nome", "cargo", "area", "nota", "potencial"]
        self._column_selectors: dict[str, QComboBox] = {}
        self._preview_rows: list[dict[str, str]] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        left_column = QVBoxLayout()
        left_column.setSpacing(16)
        left_container = QWidget()
        left_container.setLayout(left_column)
        left_container.setMinimumWidth(430)

        source_card = SectionCard(
            "Fonte e agrupamento",
            "Configure a base, a forma de agrupar e o titulo do material antes de gerar o grid.",
        )
        source_form = QFormLayout()
        source_form.setSpacing(10)

        self.source_type = QComboBox()
        self.source_type.addItems(["OneDrive", "Arquivo local"])
        self.source_type.currentTextChanged.connect(self._sync_source_mode)
        self.source_type.currentTextChanged.connect(self._refresh_preview)

        self.entry_source = QLineEdit(config.get("default_onedrive_url", ""))
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
        self.columns.currentTextChanged.connect(self._refresh_preview)
        self.columns.setVisible(False)

        source_form.addRow("Origem", self.source_type)
        source_form.addRow("Planilha ou link", self.entry_source)
        source_form.addRow("Pasta de saida", self.entry_output)
        source_form.addRow("Agrupar por", self.grouping)
        source_form.addRow("Titulo", self.title_field)
        source_card.add_layout(source_form)

        actions = QHBoxLayout()
        self.btn_browse_file = QPushButton("Procurar planilha")
        self.btn_browse_file.clicked.connect(self._choose_source_file)
        self.btn_detect = QPushButton("Auto-detectar colunas")
        self.btn_detect.clicked.connect(self._auto_detect_columns)
        actions.addWidget(self.btn_browse_file)
        actions.addWidget(self.btn_detect)
        source_card.add_layout(actions)
        left_column.addWidget(source_card)

        mapping_card = SectionCard(
            "Mapeamento",
            "Campos obrigatorios ficam realcados e a preview usa as primeiras linhas da base.",
        )
        mapping_form = QFormLayout()
        mapping_form.setSpacing(10)
        for field in self.column_fields:
            combo = QComboBox()
            combo.addItem("")
            combo.currentTextChanged.connect(self._refresh_preview)
            combo.currentTextChanged.connect(self._refresh_required_states)
            self._column_selectors[field] = combo
            mapping_form.addRow(field.capitalize(), combo)
        mapping_card.add_layout(mapping_form)
        left_column.addWidget(mapping_card)

        options_card = SectionCard(
            "Layout visual",
            "Selecione quantas colunas entram por slide e quais dados devem aparecer nos cards.",
        )
        chip_row = QHBoxLayout()
        chip_row.setSpacing(8)
        self.column_group = QButtonGroup(self)
        self.column_group.setExclusive(True)
        self.column_buttons: dict[str, QPushButton] = {}
        for value in ("3", "4", "5"):
            button = QPushButton(value)
            button.setObjectName("chipButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, selected=value: self.columns.setCurrentText(selected))
            self.column_group.addButton(button)
            self.column_buttons[value] = button
            chip_row.addWidget(button)
        chip_row.addStretch(1)
        options_card.add_layout(chip_row)

        self.chk_show_nota = QCheckBox("Mostrar nota")
        self.chk_show_nota.setChecked(True)
        self.chk_show_nota.toggled.connect(self._refresh_preview)
        self.chk_show_potencial = QCheckBox("Mostrar potencial")
        self.chk_show_potencial.setChecked(True)
        self.chk_show_potencial.toggled.connect(self._refresh_preview)
        self.chk_show_cargo = QCheckBox("Mostrar cargo")
        self.chk_show_cargo.setChecked(True)
        self.chk_show_cargo.toggled.connect(self._refresh_preview)
        self.chk_cores = QCheckBox("Cores automaticas")
        self.chk_cores.setChecked(True)
        self.chk_cores.toggled.connect(self._refresh_preview)

        toggles_col = QVBoxLayout()
        toggles_col.setSpacing(8)
        toggles_col.addWidget(self.chk_show_nota)
        toggles_col.addWidget(self.chk_show_potencial)
        toggles_col.addWidget(self.chk_show_cargo)
        toggles_col.addWidget(self.chk_cores)
        options_card.add_layout(toggles_col)
        left_column.addWidget(options_card)

        action_card = SectionCard(
            "Pronto para gerar",
            "O preview ajuda a validar quantidade de cards, agrupamento e niveis de destaque visual.",
        )
        status_row = QHBoxLayout()
        self.status_badge = StatusBadge("Aguardando", "neutral")
        self.status_label = QLabel("Selecione uma fonte de dados para iniciar.")
        self.status_label.setObjectName("bodyMuted")
        self.status_label.setWordWrap(True)
        status_row.addWidget(self.status_badge)
        status_row.addWidget(self.status_label, 1)
        action_card.add_layout(status_row)

        self.btn_generate = QPushButton("Gerar carometro")
        self.btn_generate.setObjectName("primary")
        self.btn_generate.clicked.connect(self._start_generation)
        action_card.add_widget(self.btn_generate)
        left_column.addWidget(action_card)
        left_column.addStretch(1)

        right_column = QVBoxLayout()
        right_column.setSpacing(16)

        preview_card = SectionCard(
            "Preview do carometro",
            "Mini-cards e grupos atualizam localmente conforme voce muda layout, titulo e atributos visiveis.",
            object_name="previewPanel",
        )
        self.source_badge = StatusBadge("Fonte pendente", "warning")
        self.layout_badge = StatusBadge("5 colunas", "info")
        self.group_badge = StatusBadge("Agrupar por area", "info")
        preview_card.add_widget(
            build_badge_row([self.source_badge, self.layout_badge, self.group_badge])
        )

        self.canvas = QFrame()
        self.canvas.setObjectName("caromCanvas")
        canvas_layout = QVBoxLayout(self.canvas)
        canvas_layout.setContentsMargins(18, 18, 18, 18)
        canvas_layout.setSpacing(12)

        self.preview_header = QLabel("Carometro")
        self.preview_header.setObjectName("previewTitle")
        self.preview_subheader = QLabel("Talent Development  |  Grupo atual")
        self.preview_subheader.setObjectName("previewMeta")
        canvas_layout.addWidget(self.preview_header)
        canvas_layout.addWidget(self.preview_subheader)

        self.preview_grid_wrap = QWidget()
        self.preview_grid = QGridLayout(self.preview_grid_wrap)
        self.preview_grid.setContentsMargins(0, 0, 0, 0)
        self.preview_grid.setHorizontalSpacing(10)
        self.preview_grid.setVerticalSpacing(10)
        canvas_layout.addWidget(self.preview_grid_wrap)
        preview_card.add_widget(self.canvas)

        sample_card = SectionCard(
            "Amostra de colaboradores",
            "Use esta lista para validar nome, cargo, nota e potencial lidos da base.",
            object_name="previewCard",
            compact=True,
        )
        self.preview_people_wrap = QWidget()
        self.preview_people_layout = QVBoxLayout(self.preview_people_wrap)
        self.preview_people_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_people_layout.setSpacing(8)
        sample_card.add_widget(self.preview_people_wrap)
        preview_card.add_widget(sample_card)

        right_column.addWidget(preview_card)
        right_column.addStretch(1)

        layout.addWidget(left_container, 0)
        layout.addLayout(right_column, 1)

        if config.get("spreadsheet_source") == "local":
            self.source_type.setCurrentText("Arquivo local")
        self.load_config(config)
        self._sync_source_mode()
        self._sync_column_buttons()
        self._refresh_preview()

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
        self._sync_column_buttons()
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

    def _sync_column_buttons(self) -> None:
        for value, button in self.column_buttons.items():
            button.setChecked(value == self.columns.currentText())

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

    def _set_status(self, message: str, tone: str) -> None:
        self.status_label.setText(message)
        self.status_badge.update_status(
            {
                "success": "Pronto",
                "warning": "Atencao",
                "error": "Erro",
                "info": "Info",
            }.get(tone, "Aguardando"),
            tone,
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
            self._set_invalid(self.entry_source, True)
            self._set_status("A planilha local nao foi encontrada.", "error")
            return False

        if self.source_type.currentText() == "OneDrive" and not source.startswith("https://"):
            self._set_invalid(self.entry_source, True)
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

        self._set_status("Configuracao valida para geracao.", "success")
        return True

    def _auto_detect_columns(self) -> None:
        source = self.entry_source.text().strip()
        if source == "":
            self._set_invalid(self.entry_source, True)
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
            self._set_invalid(self.entry_source, False)
            self._set_status("Colunas detectadas e preview atualizado.", "success")
            self._refresh_required_states()
            self._refresh_preview()
        except Exception as exc:
            self._set_status(str(exc), "error")

    def _preview_value(self, row: dict[str, str], field: str, fallback: str) -> str:
        mapping = self._get_column_mapping()
        source_field = mapping.get(field)
        if self._preview_rows and source_field:
            value = str(row.get(source_field, "")).strip()
            if value:
                return value
        return fallback

    def _render_preview_grid(self) -> None:
        clear_layout(self.preview_grid)
        rows = self._preview_rows[:6]
        fallback = [
            {"nome": "Ana Martins", "cargo": "Analista Sr.", "nota": "4.5", "potencial": "Alto"},
            {"nome": "Carlos Ferreira", "cargo": "Coordenador", "nota": "4.3", "potencial": "Alto"},
            {"nome": "Julia Lima", "cargo": "Analista Pl.", "nota": "3.9", "potencial": "Medio"},
            {"nome": "Rafael Silva", "cargo": "Especialista", "nota": "4.1", "potencial": "Alto"},
            {"nome": "Lucas Moura", "cargo": "Analista Jr.", "nota": "3.2", "potencial": "Baixo"},
        ]
        dataset = rows if rows else fallback
        columns = max(1, int(self.columns.currentText()))
        max_items = min(len(dataset), columns * 2)
        for index, row in enumerate(dataset[:max_items]):
            card = QFrame()
            card.setObjectName("subpanel")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 10, 10, 10)
            card_layout.setSpacing(4)

            name = self._preview_value(row, "nome", str(row.get("nome", "Sem nome")))
            cargo = self._preview_value(row, "cargo", str(row.get("cargo", "Cargo")))
            nota = self._preview_value(row, "nota", str(row.get("nota", "4.0")))
            potencial = self._preview_value(
                row, "potencial", str(row.get("potencial", "Alto"))
            )

            avatar = QLabel("".join(part[:1] for part in name.split()[:2]).upper() or "?")
            avatar.setObjectName("avatarBadge")
            avatar.setAlignment(Qt.AlignCenter)
            avatar.setMinimumSize(36, 36)
            avatar.setMaximumSize(36, 36)
            card_layout.addWidget(avatar, 0, Qt.AlignLeft)

            title = QLabel(name)
            title.setObjectName("previewItemTitle")
            title.setWordWrap(True)
            card_layout.addWidget(title)

            if self.chk_show_cargo.isChecked():
                cargo_label = QLabel(cargo)
                cargo_label.setObjectName("previewItemMeta")
                cargo_label.setWordWrap(True)
                card_layout.addWidget(cargo_label)

            accent_bits: list[str] = []
            if self.chk_show_nota.isChecked():
                accent_bits.append(f"Nota {nota}")
            if self.chk_show_potencial.isChecked():
                accent_bits.append(potencial)
            accent_label = QLabel("  |  ".join(accent_bits) if accent_bits else "Card compacto")
            accent_label.setObjectName("previewItemAccent")
            accent_label.setWordWrap(True)
            card_layout.addWidget(accent_label)

            self.preview_grid.addWidget(card, index // columns, index % columns)

    def _render_people_preview(self) -> None:
        clear_layout(self.preview_people_layout)
        rows = self._preview_rows[:4]
        mapping = self._get_column_mapping()
        name_key = mapping.get("nome")
        cargo_key = mapping.get("cargo")
        note_key = mapping.get("nota")
        fallback_rows = [
            {"nome": "Ana Martins", "cargo": "Analista Sr.", "nota": "4.5"},
            {"nome": "Carlos Ferreira", "cargo": "Coordenador", "nota": "4.3"},
            {"nome": "Julia Lima", "cargo": "Analista Pl.", "nota": "3.9"},
        ]
        dataset = rows if rows else fallback_rows
        for row in dataset:
            title = (
                str(row.get(name_key, "")).strip()
                if rows and name_key
                else str(row.get("nome", "")).strip()
            ) or "Sem nome"
            role = (
                str(row.get(cargo_key, "")).strip()
                if rows and cargo_key
                else str(row.get("cargo", "")).strip()
            ) or "Cargo nao identificado"
            note = (
                str(row.get(note_key, "")).strip()
                if rows and note_key
                else str(row.get("nota", "")).strip()
            )
            self.preview_people_layout.addWidget(PreviewListItem(title, role, note))
        self.preview_people_layout.addStretch(1)

    def _refresh_preview(self) -> None:
        self._sync_column_buttons()
        mapped_count = sum(
            1 for combo in self._column_selectors.values() if combo.currentText().strip()
        )
        self.source_badge.update_status(
            "Arquivo local" if self.source_type.currentText() == "Arquivo local" else "OneDrive",
            "info" if self.entry_source.text().strip() else "warning",
        )
        self.layout_badge.update_status(f"{self.columns.currentText()} colunas", "info")
        grouping = self.grouping.currentText()
        self.group_badge.update_status(
            "Sem agrupamento" if grouping == "sem agrupamento" else f"Agrupar por {grouping}",
            "success" if mapped_count >= 4 else "warning",
        )
        self.preview_header.setText(self.title_field.text().strip() or "Carometro")
        self.preview_subheader.setText(
            f"Talent Development  |  {self.group_badge.text()}"
        )
        self._render_preview_grid()
        self._render_people_preview()

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
