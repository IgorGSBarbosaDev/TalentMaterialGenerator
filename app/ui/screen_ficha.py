from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import get_default_output_dir
from app.core import reader
from app.core.reader import FichaEmployee, SpreadsheetSourceResult
from app.core.worker import FichaLookupWorker
from app.ui.components import repolish


class FichaScreen(QWidget):
    generate_requested = Signal(dict)

    page_title = "Ficha de Curriculo"
    page_subtitle = "Base padronizada e busca individual"
    page_badge = "Template"

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__()
        self.setObjectName("fichaPage")
        self._config = dict(config)
        self._lookup_matches: list[FichaEmployee] = []
        self._confirmed_employee: FichaEmployee | None = None
        self._lookup_source_result: SpreadsheetSourceResult | None = None
        self._worker: FichaLookupWorker | None = None
        self._worker_mode: str | None = None
        self._schema_valid = False
        self._schema_fields: dict[str, str | None] = {}

        layout = QVBoxLayout(self)
        self._root_layout = layout
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(18)

        title = QLabel("Ficha de Curriculo")
        title.setObjectName("title")
        subtitle = QLabel(
            "Valide a base padronizada, encontre um colaborador e revise os dados antes de gerar a ficha."
        )
        subtitle.setObjectName("muted")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        source_card = QFrame()
        source_card.setObjectName("fichaSourceCard")
        source_layout = QVBoxLayout(source_card)
        source_layout.setContentsMargins(22, 22, 22, 22)
        source_layout.setSpacing(18)

        source_title = self._panel_title("Fonte de dados")
        source_title.setObjectName("panelTitleStrong")
        self.source_hint = self._panel_hint(
            "A ficha usa a mesma base padronizada do Carometro e valida o schema automaticamente."
        )
        source_layout.addWidget(source_title)
        source_layout.addWidget(self.source_hint)

        source_body = QHBoxLayout()
        source_body.setSpacing(18)

        source_form = QGridLayout()
        source_form.setHorizontalSpacing(14)
        source_form.setVerticalSpacing(14)
        source_form.setColumnStretch(1, 1)

        self.source_type = QComboBox()
        self.source_type.addItems(["OneDrive", "Arquivo local"])
        self.source_type.currentTextChanged.connect(self._on_source_mode_changed)

        self.entry_source = QLineEdit(config.get("default_onedrive_url", ""))
        self.entry_source.setMinimumWidth(360)
        self.entry_source.textChanged.connect(self._on_source_text_changed)
        self.entry_source.editingFinished.connect(self._start_schema_validation)

        self.entry_output = QLineEdit(str(get_default_output_dir()))
        self.entry_output.setReadOnly(True)

        self.btn_browse_file = QPushButton("Procurar arquivo")
        self.btn_browse_file.clicked.connect(self._choose_source_file)

        source_input_row = QWidget()
        source_input_layout = QHBoxLayout(source_input_row)
        source_input_layout.setContentsMargins(0, 0, 0, 0)
        source_input_layout.setSpacing(10)
        source_input_layout.addWidget(self.entry_source, 1)
        source_input_layout.addWidget(self.btn_browse_file)

        source_form.addWidget(self._field_label("Fonte"), 0, 0)
        source_form.addWidget(self.source_type, 0, 1)
        source_form.addWidget(self._field_label("Planilha / Link"), 1, 0)
        source_form.addWidget(source_input_row, 1, 1)
        source_form.addWidget(self._field_label("Saida"), 2, 0)
        source_form.addWidget(self.entry_output, 2, 1)
        source_body.addLayout(source_form, 7)

        schema_panel = QFrame()
        schema_panel.setObjectName("fichaSchemaPanel")
        schema_layout = QVBoxLayout(schema_panel)
        schema_layout.setContentsMargins(16, 16, 16, 16)
        schema_layout.setSpacing(10)
        schema_title = self._panel_title("Status do schema")
        schema_note = self._meta_label(
            "A busca individual so fica disponivel quando a estrutura obrigatoria da ficha e reconhecida."
        )
        self.schema_status_label = QLabel("")
        self.schema_status_label.setObjectName("statusLabel")
        self.schema_status_label.setWordWrap(True)
        schema_layout.addWidget(schema_title)
        schema_layout.addWidget(schema_note)
        schema_layout.addWidget(self.schema_status_label)
        schema_layout.addStretch(1)
        source_body.addWidget(schema_panel, 5)

        source_layout.addLayout(source_body)
        layout.addWidget(source_card)

        workflow_card = QFrame()
        workflow_card.setObjectName("fichaWorkflowCard")
        workflow_layout = QVBoxLayout(workflow_card)
        workflow_layout.setContentsMargins(22, 22, 22, 22)
        workflow_layout.setSpacing(18)

        workflow_title = self._panel_title("Dados recuperados")
        workflow_title.setObjectName("panelTitleStrong")
        self.workflow_hint = self._panel_hint(
            "Busque por nome ou matricula, confirme um colaborador e revise o dossie antes de gerar."
        )
        workflow_layout.addWidget(workflow_title)
        workflow_layout.addWidget(self.workflow_hint)

        content_split = QHBoxLayout()
        self._content_split = content_split
        content_split.setSpacing(18)

        lookup_panel = QFrame()
        lookup_panel.setObjectName("fichaLookupPane")
        lookup_layout = QVBoxLayout(lookup_panel)
        lookup_layout.setContentsMargins(18, 18, 18, 18)
        lookup_layout.setSpacing(14)
        lookup_layout.addWidget(self._group_title("Busca e selecao"))
        lookup_layout.addWidget(
            self._meta_label(
                "Use nome ou matricula para localizar um unico colaborador dentro da base validada."
            )
        )

        lookup_inputs = QHBoxLayout()
        lookup_inputs.setSpacing(12)
        self.entry_lookup_name = QLineEdit()
        self.entry_lookup_name.setPlaceholderText("Buscar por nome")
        self.entry_lookup_name.textChanged.connect(self._on_lookup_input_changed)
        self.entry_lookup_matricula = QLineEdit()
        self.entry_lookup_matricula.setPlaceholderText("Buscar por matricula")
        self.entry_lookup_matricula.textChanged.connect(self._on_lookup_input_changed)
        lookup_inputs.addWidget(
            self._field_stack("Nome", self.entry_lookup_name),
            1,
        )
        lookup_inputs.addWidget(
            self._field_stack("Matricula", self.entry_lookup_matricula),
            1,
        )
        lookup_layout.addLayout(lookup_inputs)

        lookup_actions = QHBoxLayout()
        lookup_actions.setSpacing(10)
        self.btn_search = QPushButton("Buscar colaborador")
        self.btn_search.clicked.connect(self._start_lookup)
        self.btn_confirm = QPushButton("Confirmar colaborador")
        self.btn_confirm.clicked.connect(self._confirm_selected_employee)
        lookup_actions.addWidget(self.btn_search)
        lookup_actions.addWidget(self.btn_confirm)
        lookup_actions.addStretch(1)
        lookup_layout.addLayout(lookup_actions)

        lookup_layout.addWidget(self._group_title("Resultados da busca"))
        lookup_layout.addWidget(
            self._meta_label(
                "Selecione uma linha e confirme o colaborador que sera usado na geracao individual."
            )
        )

        results_wrap = QFrame()
        results_wrap.setObjectName("fichaTableWrap")
        results_layout = QVBoxLayout(results_wrap)
        results_layout.setContentsMargins(10, 10, 10, 10)
        results_layout.setSpacing(0)

        self.results_table = QTableWidget(0, 3)
        self.results_table.setObjectName("fichaResultsTable")
        self.results_table.setHorizontalHeaderLabels(["Nome", "Matricula", "Cargo"])
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setMinimumHeight(300)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.itemSelectionChanged.connect(self._refresh_action_state)
        self.results_table.itemDoubleClicked.connect(
            lambda _item: self._confirm_selected_employee()
        )
        results_layout.addWidget(self.results_table)
        lookup_layout.addWidget(results_wrap, 1)
        content_split.addWidget(lookup_panel, 4)

        dossier_panel = QFrame()
        dossier_panel.setObjectName("fichaDossierPane")
        dossier_layout = QVBoxLayout(dossier_panel)
        dossier_layout.setContentsMargins(18, 18, 18, 18)
        dossier_layout.setSpacing(14)
        dossier_layout.addWidget(self._group_title("Colaborador confirmado"))
        dossier_layout.addWidget(
            self._meta_label(
                "Os campos abaixo sao apenas leitura e refletem exatamente os dados recuperados da planilha."
            )
        )

        self.confirmed_status_label = QLabel("")
        self.confirmed_status_label.setObjectName("statusLabel")
        self.confirmed_status_label.setWordWrap(True)
        dossier_layout.addWidget(self.confirmed_status_label)

        self.detail_matricula = self._build_readonly_line()
        self.detail_nome = self._build_readonly_line()
        self.detail_idade = self._build_readonly_line()
        self.detail_cargo = self._build_readonly_line()
        self.detail_antiguidade = self._build_readonly_line()
        self.detail_formacao = self._build_readonly_text()
        self.detail_resumo = self._build_readonly_text()
        self.detail_trajetoria = self._build_readonly_text()
        self._detail_widgets = {
            "matricula": self.detail_matricula,
            "nome": self.detail_nome,
            "idade": self.detail_idade,
            "cargo": self.detail_cargo,
            "antiguidade": self.detail_antiguidade,
            "formacao": self.detail_formacao,
            "resumo_perfil": self.detail_resumo,
            "trajetoria": self.detail_trajetoria,
        }

        identity_group, identity_body = self._data_group(
            "Identificacao",
            "Campos principais reconhecidos para o colaborador confirmado.",
        )
        identity_grid = QGridLayout()
        identity_grid.setHorizontalSpacing(12)
        identity_grid.setVerticalSpacing(12)
        identity_grid.addWidget(self._field_stack("Matricula", self.detail_matricula), 0, 0)
        identity_grid.addWidget(self._field_stack("Nome", self.detail_nome), 0, 1)
        identity_grid.addWidget(self._field_stack("Idade", self.detail_idade), 0, 2)
        identity_grid.setColumnStretch(0, 1)
        identity_grid.setColumnStretch(1, 2)
        identity_grid.setColumnStretch(2, 1)
        identity_body.addLayout(identity_grid)
        dossier_layout.addWidget(identity_group)

        role_group, role_body = self._data_group(
            "Resumo profissional",
            "Visao rapida da posicao atual e do tempo de casa.",
        )
        role_grid = QGridLayout()
        role_grid.setHorizontalSpacing(12)
        role_grid.setVerticalSpacing(12)
        role_grid.addWidget(self._field_stack("Cargo", self.detail_cargo), 0, 0)
        role_grid.addWidget(self._field_stack("Antiguidade", self.detail_antiguidade), 0, 1)
        role_grid.setColumnStretch(0, 2)
        role_grid.setColumnStretch(1, 1)
        role_body.addLayout(role_grid)
        dossier_layout.addWidget(role_group)

        narrative_group, narrative_body = self._data_group(
            "Narrativa recuperada",
            "Conteudo recuperado automaticamente da base padronizada para a ficha.",
        )
        narrative_body.addWidget(self._field_stack("Formacao", self.detail_formacao))
        narrative_body.addWidget(self._field_stack("Resumo de perfil", self.detail_resumo))
        narrative_body.addWidget(self._field_stack("Trajetoria", self.detail_trajetoria))
        dossier_layout.addWidget(narrative_group, 1)
        content_split.addWidget(dossier_panel, 5)

        workflow_layout.addLayout(content_split, 1)
        layout.addWidget(workflow_card, 1)

        action_bar = QFrame()
        action_bar.setObjectName("fichaActionBar")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(18, 16, 18, 16)
        action_layout.setSpacing(14)

        status_col = QVBoxLayout()
        status_col.setSpacing(6)
        footer_label = QLabel("Geracao individual")
        footer_label.setObjectName("fichaFieldLabel")
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        status_col.addWidget(footer_label)
        status_col.addWidget(self.status_label)
        action_layout.addLayout(status_col, 1)

        self.btn_generate = QPushButton("Gerar ficha")
        self.btn_generate.setObjectName("primary")
        self.btn_generate.clicked.connect(self._start_generation)
        self.btn_generate.setMinimumWidth(220)
        action_layout.addWidget(self.btn_generate)
        layout.addWidget(action_bar)

        self._compact_labels = [subtitle, self.source_hint, self.workflow_hint]
        self._sync_source_mode()
        self._clear_schema_state()
        self._clear_lookup_state(clear_queries=True)
        self._set_status(
            "Informe a fonte de dados. A validacao da base padronizada sera executada automaticamente.",
            "info",
        )
        self._refresh_action_state()

    def _panel_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("panelTitle")
        return label

    def _panel_hint(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("panelHint")
        label.setWordWrap(True)
        return label

    def _group_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fichaGroupTitle")
        return label

    def _meta_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fichaMetaText")
        label.setWordWrap(True)
        return label

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fichaFieldLabel")
        return label

    def _field_stack(self, title: str, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self._field_label(title))
        layout.addWidget(widget)
        return container

    def _data_group(self, title: str, hint: str) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("fichaDataGroup")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(self._group_title(title))
        layout.addWidget(self._meta_label(hint))
        body = QVBoxLayout()
        body.setSpacing(12)
        layout.addLayout(body)
        return frame, body

    def _build_readonly_line(self) -> QLineEdit:
        field = QLineEdit()
        field.setObjectName("fichaDisplayField")
        field.setReadOnly(True)
        return field

    def _build_readonly_text(self) -> QTextEdit:
        field = QTextEdit()
        field.setObjectName("fichaDisplayField")
        field.setReadOnly(True)
        field.setMinimumHeight(92)
        return field

    def _set_status(self, message: str, state: str) -> None:
        self.status_label.setText(message)
        self.status_label.setProperty("state", state)
        repolish(self.status_label)

    def _set_schema_status(self, message: str, state: str) -> None:
        self.schema_status_label.setText(message)
        self.schema_status_label.setProperty("state", state)
        repolish(self.schema_status_label)

    def _set_confirmed_status(self, message: str, state: str) -> None:
        self.confirmed_status_label.setText(message)
        self.confirmed_status_label.setProperty("state", state)
        repolish(self.confirmed_status_label)

    def load_config(self, config: dict[str, Any]) -> None:
        self._config = dict(config)
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
        self._clear_schema_state()
        self._clear_lookup_state(clear_queries=True)
        self._refresh_action_state()
        if self.entry_source.text().strip():
            self._start_schema_validation()

    def _validate_source(self) -> bool:
        source = self.entry_source.text().strip()
        self._set_invalid(self.entry_source, source == "")
        if source == "":
            self._set_status("Informe a fonte de dados.", "warning")
            self._set_schema_status("Base nao validada.", "warning")
            return False

        if self.source_type.currentText() == "Arquivo local" and not Path(source).is_file():
            self._set_status("A planilha local nao foi encontrada.", "error")
            self._set_schema_status("Base invalida: arquivo local nao encontrado.", "error")
            return False

        if self.source_type.currentText() == "OneDrive" and not source.startswith("https://"):
            self._set_status("Informe um link valido do OneDrive.", "error")
            self._set_schema_status("Base invalida: link do OneDrive nao reconhecido.", "error")
            return False
        return True

    def _set_invalid(self, widget: QWidget, is_invalid: bool) -> None:
        widget.setProperty("invalid", is_invalid)
        repolish(widget)

    def _choose_source_file(self) -> None:
        file_path, _filter = QFileDialog.getOpenFileName(
            self, "Selecionar planilha", "", "Excel (*.xlsx)"
        )
        if file_path:
            self.source_type.setCurrentText("Arquivo local")
            self.entry_source.setText(file_path)
            self._start_schema_validation()

    def _sync_source_mode(self) -> None:
        local_mode = self.source_type.currentText() == "Arquivo local"
        self.btn_browse_file.setEnabled(local_mode)
        self.entry_source.setPlaceholderText(
            "C:\\dados\\colaboradores.xlsx"
            if local_mode
            else "https://... link compartilhado do OneDrive"
        )

    def _on_source_mode_changed(self, *_args: object) -> None:
        self._sync_source_mode()
        self._on_source_text_changed()

    def _on_source_text_changed(self, *_args: object) -> None:
        self._set_invalid(self.entry_source, False)
        self._clear_schema_state()
        self._clear_lookup_state()
        source = self.entry_source.text().strip()
        if source:
            self._set_schema_status("Validacao automatica pendente.", "info")
            self._set_status(
                "Fonte definida. Conclua a edicao do campo para validar a base padronizada.",
                "info",
            )
        else:
            self._set_schema_status("Base nao validada.", "warning")
            self._set_status(
                "Informe a fonte de dados. A validacao da base padronizada sera executada automaticamente.",
                "info",
            )
        self._refresh_action_state()

    def _on_lookup_input_changed(self, *_args: object) -> None:
        if self._lookup_matches or self._confirmed_employee is not None:
            self._lookup_matches = []
            self._lookup_source_result = None
            self._populate_results_table([])
            self._clear_display_fields()
            self._confirmed_employee = None
            self._set_confirmed_status("Nenhum colaborador confirmado.", "info")
            if self._schema_valid:
                self._set_status(
                    "Busca alterada. Execute uma nova busca para confirmar o colaborador.",
                    "info",
                )
        self._refresh_action_state()

    def _clear_schema_state(self) -> None:
        self._schema_valid = False
        self._schema_fields = {}
        self._set_schema_status("Base nao validada.", "warning")

    def _clear_lookup_state(self, *, clear_queries: bool = False) -> None:
        self._lookup_matches = []
        self._confirmed_employee = None
        self._lookup_source_result = None
        self._populate_results_table([])
        self._clear_display_fields()
        self._set_confirmed_status("Nenhum colaborador confirmado.", "info")
        if clear_queries:
            self.entry_lookup_name.clear()
            self.entry_lookup_matricula.clear()
        self._refresh_action_state()

    def _start_schema_validation(self) -> None:
        if not self._validate_source():
            self._refresh_action_state()
            return
        if self._worker is not None and self._worker.isRunning():
            return

        self._worker_mode = "validate"
        self._worker = FichaLookupWorker(self._get_worker_payload(validate_only=True))
        self._worker.succeeded.connect(self._handle_worker_success)
        self._worker.error.connect(self._handle_worker_error)
        self._worker.finished.connect(self._on_worker_finished)
        self._set_schema_status("Validando base padronizada...", "info")
        self._set_status("Validando schema da ficha...", "info")
        self._refresh_action_state()
        self._worker.start()

    def _start_lookup(self) -> None:
        if not self._schema_valid:
            self._set_status("A ficha so pode buscar apos validar a base padronizada.", "warning")
            return
        if self._worker is not None and self._worker.isRunning():
            return

        name_query = self.entry_lookup_name.text().strip()
        matricula_query = self.entry_lookup_matricula.text().strip()
        if name_query == "" and matricula_query == "":
            self._set_status("Informe nome ou matricula para buscar.", "warning")
            return

        self._clear_lookup_state()
        self._worker_mode = "lookup"
        self._worker = FichaLookupWorker(self._get_worker_payload(validate_only=False))
        self._worker.succeeded.connect(self._handle_worker_success)
        self._worker.error.connect(self._handle_worker_error)
        self._worker.finished.connect(self._on_worker_finished)
        self._set_status("Buscando colaborador na planilha...", "info")
        self._refresh_action_state()
        self._worker.start()

    def _get_worker_payload(self, *, validate_only: bool) -> dict[str, Any]:
        source_kind = (
            "local" if self.source_type.currentText() == "Arquivo local" else "onedrive"
        )
        return {
            "spreadsheet_source": self.entry_source.text().strip(),
            "source_kind": source_kind,
            "lookup_name": self.entry_lookup_name.text().strip(),
            "lookup_matricula": self.entry_lookup_matricula.text().strip(),
            "cache_enabled": self._config.get("cache_enabled", True),
            "cache_ttl_hours": self._config.get("cache_ttl_hours", 24),
            "force_refresh": False,
            "validate_only": validate_only,
        }

    def _handle_worker_success(self, result: dict[str, Any]) -> None:
        self._schema_valid = True
        self._schema_fields = dict(result.get("schema", {}))
        row_count = int(result.get("row_count", 0))
        self._set_schema_status(
            f"Base padronizada validada. {row_count} linha(s) reconhecida(s).",
            "success",
        )

        if self._worker_mode == "validate":
            self._set_status("Base validada. Busque um colaborador para recuperar os dados.", "success")
            self._refresh_action_state()
            return

        self._lookup_matches = list(result.get("matches", []))
        self._lookup_source_result = result.get("source_result")
        self._populate_results_table(self._lookup_matches)
        self._clear_display_fields()
        self._confirmed_employee = None
        self._set_confirmed_status("Nenhum colaborador confirmado.", "info")

        if not self._lookup_matches:
            self._set_status("Nenhum colaborador encontrado para os filtros informados.", "warning")
        elif len(self._lookup_matches) == 1:
            self._set_status("1 colaborador encontrado. Confirme a selecao para gerar a ficha.", "success")
        else:
            self._set_status(
                f"{len(self._lookup_matches)} colaboradores encontrados. Selecione um e confirme.",
                "info",
            )
        self._refresh_action_state()

    def _handle_worker_error(self, message: str) -> None:
        if self._worker_mode == "validate" or "schema padrao da ficha" in message.lower():
            self._clear_schema_state()
            self._clear_lookup_state()
            self._set_schema_status(message, "error")
            self._set_status(message, "error")
        else:
            self._lookup_matches = []
            self._lookup_source_result = None
            self._confirmed_employee = None
            self._populate_results_table([])
            self._clear_display_fields()
            self._set_confirmed_status("Nenhum colaborador confirmado.", "info")
            self._set_status(message, "error")
        self._refresh_action_state()

    def _on_worker_finished(self) -> None:
        self._worker = None
        self._worker_mode = None
        self._refresh_action_state()

    def _populate_results_table(self, employees: list[FichaEmployee]) -> None:
        self.results_table.setRowCount(len(employees))
        for row, employee in enumerate(employees):
            values = [
                employee.get("nome", ""),
                employee.get("matricula", "") or "-",
                employee.get("cargo", ""),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.results_table.setItem(row, column, item)
        if employees:
            self.results_table.selectRow(0)
        else:
            self.results_table.clearSelection()

    def _selected_match(self) -> FichaEmployee | None:
        row = self.results_table.currentRow()
        if row < 0 or row >= len(self._lookup_matches):
            return None
        return self._lookup_matches[row]

    def _confirm_selected_employee(self) -> None:
        employee = self._selected_match()
        if employee is None:
            self._set_status("Selecione um colaborador na lista para confirmar.", "warning")
            return

        missing_required = reader.validate_ficha_employee(employee)
        if missing_required:
            self._set_status(
                f"O colaborador selecionado nao possui os campos obrigatorios: {', '.join(missing_required)}.",
                "error",
            )
            return

        self._confirmed_employee = employee
        self._fill_display_fields(employee)
        label = employee.get("nome", "").strip() or "colaborador selecionado"
        self._set_confirmed_status(f"Colaborador confirmado: {label}.", "success")
        self._set_status(f"Colaborador confirmado: {label}. Pronto para gerar a ficha.", "success")
        self._refresh_action_state()

    def _fill_display_fields(self, employee: FichaEmployee) -> None:
        for field, widget in self._detail_widgets.items():
            value = employee.get(field, "")
            if isinstance(widget, QTextEdit):
                widget.setPlainText(value)
            else:
                widget.setText(value)

    def _clear_display_fields(self) -> None:
        for widget in self._detail_widgets.values():
            if isinstance(widget, QTextEdit):
                widget.clear()
            else:
                widget.setText("")

    def _get_generation_payload(self) -> dict[str, Any]:
        source_kind = (
            "local" if self.source_type.currentText() == "Arquivo local" else "onedrive"
        )
        return {
            "spreadsheet_source": self.entry_source.text().strip(),
            "source_kind": source_kind,
            "output_dir": str(get_default_output_dir()),
            "selected_employee": self._confirmed_employee,
            "source_result": self._lookup_source_result,
        }

    def _refresh_action_state(self) -> None:
        worker_running = self._worker is not None and self._worker.isRunning()
        has_query = (
            self.entry_lookup_name.text().strip() != ""
            or self.entry_lookup_matricula.text().strip() != ""
        )
        has_selection = self._selected_match() is not None
        self.btn_search.setEnabled(self._schema_valid and has_query and not worker_running)
        self.btn_confirm.setEnabled(self._schema_valid and has_selection and not worker_running)
        self.btn_generate.setEnabled(
            self._schema_valid and self._confirmed_employee is not None and not worker_running
        )

    def _start_generation(self) -> None:
        if self._confirmed_employee is None:
            self._set_status("Confirme um colaborador antes de gerar a ficha.", "warning")
            return
        self.generate_requested.emit(self._get_generation_payload())

    def set_sidebar_collapsed(self, collapsed: bool) -> None:
        margin = 22 if collapsed else 30
        self._root_layout.setContentsMargins(margin, margin, margin, margin)
        self._root_layout.setSpacing(14 if collapsed else 18)
        self._content_split.setSpacing(14 if collapsed else 18)
        for label in self._compact_labels:
            label.setVisible(not collapsed)
