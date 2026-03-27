from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
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


class FichaScreen(QWidget):
    generate_requested = Signal(dict)

    page_title = "Ficha de Curriculo"
    page_subtitle = "Base, mapeamento e preview do material individual"
    page_badge = "Template"

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
            "resumo_perfil": "Resumo de Perfil",
            "trajetoria": "Trajetoria",
            "performance": "Performance",
        }
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
            "Fonte de dados",
            "Escolha a origem da planilha e valide a base antes de gerar os slides.",
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

        self.output_mode = QComboBox()
        self.output_mode.addItems(["one_file_per_employee", "single_deck"])
        self.output_mode.currentTextChanged.connect(self._refresh_preview)

        source_actions = QHBoxLayout()
        self.btn_browse_file = QPushButton("Procurar planilha")
        self.btn_browse_file.clicked.connect(self._choose_source_file)
        self.btn_detect = QPushButton("Auto-detectar colunas")
        self.btn_detect.clicked.connect(self._auto_detect_columns)
        source_actions.addWidget(self.btn_browse_file)
        source_actions.addWidget(self.btn_detect)

        source_form.addRow("Origem", self.source_type)
        source_form.addRow("Planilha ou link", self.entry_source)
        source_form.addRow("Pasta de saida", self.entry_output)
        source_form.addRow("Modo de saida", self.output_mode)
        source_card.add_layout(source_form)
        source_card.add_layout(source_actions)
        left_column.addWidget(source_card)

        mapping_card = SectionCard(
            "Mapeamento",
            "Campos obrigatorios ficam destacados quando ainda nao foram associados.",
        )
        mapping_form = QFormLayout()
        mapping_form.setSpacing(10)
        for field in self.column_fields:
            combo = QComboBox()
            combo.addItem("")
            combo.currentTextChanged.connect(self._refresh_preview)
            combo.currentTextChanged.connect(self._refresh_required_states)
            self._column_selectors[field] = combo
            mapping_form.addRow(self.column_labels[field], combo)
        mapping_card.add_layout(mapping_form)
        left_column.addWidget(mapping_card)

        action_card = SectionCard(
            "Pronto para gerar",
            "A interface atualiza badges, preview e checklist localmente antes da execucao.",
        )
        status_row = QHBoxLayout()
        self.status_badge = StatusBadge("Aguardando", "neutral")
        self.status_label = QLabel("Selecione uma fonte de dados para iniciar.")
        self.status_label.setObjectName("bodyMuted")
        self.status_label.setWordWrap(True)
        status_row.addWidget(self.status_badge)
        status_row.addWidget(self.status_label, 1)
        action_card.add_layout(status_row)

        self.preview_hint = QLabel(
            "Preview baseado nas colunas escolhidas e, quando disponivel, nas primeiras linhas da planilha."
        )
        self.preview_hint.setObjectName("dim")
        self.preview_hint.setWordWrap(True)
        action_card.add_widget(self.preview_hint)

        self.btn_generate = QPushButton("Gerar fichas")
        self.btn_generate.setObjectName("primary")
        self.btn_generate.clicked.connect(self._start_generation)
        action_card.add_widget(self.btn_generate)
        left_column.addWidget(action_card)
        left_column.addStretch(1)

        right_column = QVBoxLayout()
        right_column.setSpacing(16)

        preview_card = SectionCard(
            "Preview da ficha",
            "Visual persistente para validar leitura da base, estrutura do slide e ordem dos colaboradores.",
            object_name="previewPanel",
        )
        self.source_badge = StatusBadge("Fonte pendente", "warning")
        self.mapping_badge = StatusBadge("Mapeamento parcial", "warning")
        self.output_badge = StatusBadge("1 por colaborador", "info")
        preview_card.add_widget(
            build_badge_row([self.source_badge, self.mapping_badge, self.output_badge])
        )

        self.slide_card = QFrame()
        self.slide_card.setObjectName("slideCard")
        slide_layout = QHBoxLayout(self.slide_card)
        slide_layout.setContentsMargins(18, 18, 18, 18)
        slide_layout.setSpacing(16)

        identity_col = QVBoxLayout()
        identity_col.setSpacing(8)
        avatar = QLabel("AM")
        avatar.setObjectName("avatarBadge")
        avatar.setMinimumSize(56, 56)
        avatar.setMaximumSize(56, 56)
        avatar.setAlignment(Qt.AlignCenter)
        self.preview_name = QLabel("Ana Martins")
        self.preview_name.setObjectName("previewTitle")
        self.preview_role = QLabel("Analista de RH Sr.")
        self.preview_role.setObjectName("previewMeta")
        self.preview_meta = QLabel("34 anos  |  6 anos de empresa")
        self.preview_meta.setObjectName("previewMeta")
        identity_col.addWidget(avatar, 0, Qt.AlignLeft)
        identity_col.addWidget(self.preview_name)
        identity_col.addWidget(self.preview_role)
        identity_col.addWidget(self.preview_meta)
        identity_col.addStretch(1)

        content_col = QVBoxLayout()
        content_col.setSpacing(10)
        performance_label = QLabel("Performance")
        performance_label.setObjectName("previewLabel")
        self.preview_performance = QLabel("2025 - 4.5 | 2024 - 4.2 | 2023 - 3.9")
        self.preview_performance.setWordWrap(True)
        self.preview_performance.setObjectName("previewMeta")
        summary_label = QLabel("Resumo")
        summary_label.setObjectName("previewLabel")
        self.preview_summary = QLabel(
            "Profissional com boa leitura de contexto, foco em desenvolvimento e visao sistêmica."
        )
        self.preview_summary.setWordWrap(True)
        self.preview_summary.setObjectName("previewItemTitle")
        career_label = QLabel("Trajetoria")
        career_label.setObjectName("previewLabel")
        self.preview_trajectory = QLabel(
            "Evolucao interna com projetos de treinamento, rituais de performance e suporte a liderancas."
        )
        self.preview_trajectory.setWordWrap(True)
        self.preview_trajectory.setObjectName("previewMeta")
        content_col.addWidget(performance_label)
        content_col.addWidget(self.preview_performance)
        content_col.addWidget(summary_label)
        content_col.addWidget(self.preview_summary)
        content_col.addWidget(career_label)
        content_col.addWidget(self.preview_trajectory)
        content_col.addStretch(1)

        slide_layout.addLayout(identity_col, 1)
        slide_layout.addLayout(content_col, 2)
        preview_card.add_widget(self.slide_card)

        people_card = SectionCard(
            "Amostra da base",
            "Os primeiros colaboradores ajudam a validar se o mapeamento esta coerente.",
            object_name="previewCard",
            compact=True,
        )
        self.preview_people_wrap = QWidget()
        self.preview_people_layout = QVBoxLayout(self.preview_people_wrap)
        self.preview_people_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_people_layout.setSpacing(8)
        people_card.add_widget(self.preview_people_wrap)
        preview_card.add_widget(people_card)

        right_column.addWidget(preview_card)
        right_column.addStretch(1)

        layout.addWidget(left_container, 0)
        layout.addLayout(right_column, 1)

        if config.get("spreadsheet_source") == "local":
            self.source_type.setCurrentText("Arquivo local")
        self.load_config(config)
        self._sync_source_mode()
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
        self.output_mode.setCurrentText(
            config.get("default_output_mode", "one_file_per_employee")
        )
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

    def _validate_inputs(self) -> bool:
        source = self.entry_source.text().strip()
        source_missing = source == ""
        self._set_invalid(self.entry_source, source_missing)
        if source_missing:
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

    def _preview_value(self, field: str, fallback: str) -> str:
        mapping = self._get_column_mapping()
        source_field = mapping.get(field)
        if self._preview_rows and source_field:
            value = str(self._preview_rows[0].get(source_field, "")).strip()
            if value:
                return value
        return fallback

    def _render_people_preview(self) -> None:
        clear_layout(self.preview_people_layout)
        rows = self._preview_rows[:4]
        mapping = self._get_column_mapping()
        name_key = mapping.get("nome")
        cargo_key = mapping.get("cargo")
        idade_key = mapping.get("idade")
        fallback_rows = [
            {"nome": "Ana Martins", "cargo": "Analista de RH Sr.", "idade": "34"},
            {"nome": "Carlos Ferreira", "cargo": "Coordenador de T&D", "idade": "41"},
            {"nome": "Julia Lima", "cargo": "Analista Pl.", "idade": "29"},
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
            age = (
                str(row.get(idade_key, "")).strip()
                if rows and idade_key
                else str(row.get("idade", "")).strip()
            )
            meta = role if not age else f"{role}  |  {age} anos"
            self.preview_people_layout.addWidget(PreviewListItem(title, meta))
        self.preview_people_layout.addStretch(1)

    def _refresh_preview(self) -> None:
        mapped_count = sum(
            1 for combo in self._column_selectors.values() if combo.currentText().strip()
        )
        mapping_tone = "success" if mapped_count >= 4 else "warning"
        output_mode = self.output_mode.currentText()
        self.source_badge.update_status(
            "Arquivo local" if self.source_type.currentText() == "Arquivo local" else "OneDrive",
            "info" if self.entry_source.text().strip() else "warning",
        )
        self.mapping_badge.update_status(
            f"{mapped_count}/{len(self.column_fields)} mapeadas", mapping_tone
        )
        self.output_badge.update_status(
            "1 por colaborador" if output_mode == "one_file_per_employee" else "Deck unico",
            "info",
        )

        name = self._preview_value("nome", "Ana Martins")
        role = self._preview_value("cargo", "Analista de RH Sr.")
        idade = self._preview_value("idade", "34")
        antiguidade = self._preview_value("antiguidade", "6")
        performance = self._preview_value(
            "performance", "2025 - 4.5 | 2024 - 4.2 | 2023 - 3.9"
        )
        resumo = self._preview_value(
            "resumo_perfil",
            "Profissional com boa leitura de contexto, foco em desenvolvimento e visao sistemica.",
        )
        trajetoria = self._preview_value(
            "trajetoria",
            "Evolucao interna com projetos de treinamento, rituais de performance e suporte a liderancas.",
        )

        self.preview_name.setText(name)
        self.preview_role.setText(role)
        self.preview_meta.setText(f"{idade} anos  |  {antiguidade} anos de empresa")
        self.preview_performance.setText(performance)
        self.preview_summary.setText(resumo)
        self.preview_trajectory.setText(trajetoria)
        self._render_people_preview()

    def _start_generation(self) -> None:
        if not self._validate_inputs():
            return
        self.generate_requested.emit(self._get_config())
