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
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        source_card = QFrame()
        source_card.setObjectName("fichaSourceCard")
        source_layout = QVBoxLayout(source_card)
        source_layout.setContentsMargins(18, 18, 18, 18)
        source_layout.setSpacing(14)

        source_title = self._panel_title("Fonte de dados")
        source_title.setObjectName("panelTitleStrong")
        source_layout.addWidget(source_title)

        source_body = QHBoxLayout()
        source_body.setSpacing(14)

        source_form = QGridLayout()
        source_form.setHorizontalSpacing(12)
        source_form.setVerticalSpacing(12)
        source_form.setColumnStretch(1, 1)

        self.source_type = QComboBox()
        self.source_type.addItems(["OneDrive", "Arquivo local"])
        self.source_type.currentTextChanged.connect(self._on_source_mode_changed)

        self.entry_source = QLineEdit(config.get("default_onedrive_url", ""))
        self.entry_source.setMinimumWidth(320)
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
        self.schema_status_label = QLabel("")
        self.schema_status_label.setObjectName("statusLabel")
        self.schema_status_label.setWordWrap(True)
        schema_layout.addWidget(schema_title)
        schema_layout.addWidget(self.schema_status_label)
        schema_layout.addStretch(1)
        source_body.addWidget(schema_panel, 5)

        source_layout.addLayout(source_body)
        layout.addWidget(source_card)

        content_split = QHBoxLayout()
        self._content_split = content_split
        content_split.setSpacing(14)

        lookup_panel = QFrame()
        lookup_panel.setObjectName("fichaLookupPane")
        lookup_layout = QVBoxLayout(lookup_panel)
        lookup_layout.setContentsMargins(16, 16, 16, 16)
        lookup_layout.setSpacing(12)

        self.lookup_mode = QComboBox()
        self.lookup_mode.addItem("Selecione o tipo de busca", "")
        self.lookup_mode.addItem("Nome", "nome")
        self.lookup_mode.addItem("Matricula", "matricula")
        self.lookup_mode.currentIndexChanged.connect(self._on_lookup_mode_changed)

        self.entry_lookup_name = QLineEdit()
        self.entry_lookup_name.setPlaceholderText("Digite o nome do colaborador")
        self.entry_lookup_name.textChanged.connect(self._on_lookup_input_changed)
        self.entry_lookup_matricula = QLineEdit()
        self.entry_lookup_matricula.setPlaceholderText("Digite a matricula")
        self.entry_lookup_matricula.textChanged.connect(self._on_lookup_input_changed)

        self.lookup_name_container = self._field_stack("Nome", self.entry_lookup_name)
        self.lookup_matricula_container = self._field_stack(
            "Matricula", self.entry_lookup_matricula
        )

        lookup_layout.addWidget(self._field_stack("Tipo de busca", self.lookup_mode))
        lookup_layout.addWidget(self.lookup_name_container)
        lookup_layout.addWidget(self.lookup_matricula_container)

        lookup_actions = QHBoxLayout()
        lookup_actions.setSpacing(10)
        self.btn_search = QPushButton("Pesquisar")
        self.btn_search.clicked.connect(self._start_lookup)
        self.btn_confirm = QPushButton("Validar colaborador")
        self.btn_confirm.clicked.connect(self._confirm_selected_employee)
        lookup_actions.addWidget(self.btn_search)
        lookup_actions.addWidget(self.btn_confirm)
        lookup_layout.addLayout(lookup_actions)
        lookup_layout.addStretch(1)
        content_split.addWidget(lookup_panel, 3)

        results_panel = QFrame()
        results_panel.setObjectName("fichaResultsPane")
        results_layout = QVBoxLayout(results_panel)
        results_layout.setContentsMargins(16, 16, 16, 16)
        results_layout.setSpacing(0)

        table_wrap = QFrame()
        table_wrap.setObjectName("fichaTableWrap")
        table_layout = QVBoxLayout(table_wrap)
        table_layout.setContentsMargins(8, 8, 8, 8)
        table_layout.setSpacing(0)

        self.results_table = QTableWidget(0, 3)
        self.results_table.setObjectName("fichaResultsTable")
        self.results_table.setHorizontalHeaderLabels(["Matricula", "Nome", "Cargo"])
        self.results_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.results_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setMinimumHeight(360)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.results_table.itemSelectionChanged.connect(
            self._on_results_selection_changed
        )
        table_layout.addWidget(self.results_table)

        results_layout.addWidget(table_wrap, 1)
        content_split.addWidget(results_panel, 5)
        layout.addLayout(content_split, 1)

        action_bar = QFrame()
        action_bar.setObjectName("fichaActionBar")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(16, 12, 16, 12)
        action_layout.setSpacing(12)

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
        self.btn_generate.setMinimumWidth(200)
        action_layout.addWidget(self.btn_generate)
        layout.addWidget(action_bar)

        self._compact_labels: list[QLabel] = []
        self._sync_source_mode()
        self._sync_lookup_mode()
        self._clear_schema_state()
        self._clear_lookup_state(clear_queries=True, reset_mode=True)
        self._set_status(
            "Informe a fonte de dados. A validacao da base padronizada "
            "sera executada automaticamente.",
            "info",
        )
        self._refresh_action_state()

    def _panel_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("panelTitle")
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

    def _set_status(self, message: str, state: str) -> None:
        self.status_label.setText(message)
        self.status_label.setProperty("state", state)
        repolish(self.status_label)

    def _set_schema_status(self, message: str, state: str) -> None:
        self.schema_status_label.setText(message)
        self.schema_status_label.setProperty("state", state)
        repolish(self.schema_status_label)

    def _selected_lookup_mode(self) -> str:
        return str(self.lookup_mode.currentData() or "").strip().lower()

    def _active_lookup_value(self) -> str:
        mode = self._selected_lookup_mode()
        if mode == "nome":
            return self.entry_lookup_name.text().strip()
        if mode == "matricula":
            return self.entry_lookup_matricula.text().strip()
        return ""

    def _clear_confirmed_employee(self) -> None:
        self._confirmed_employee = None

    def _sync_lookup_mode(self) -> None:
        mode = self._selected_lookup_mode()
        self.lookup_name_container.setVisible(mode == "nome")
        self.lookup_matricula_container.setVisible(mode == "matricula")

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
        self._clear_lookup_state(clear_queries=True, reset_mode=True)
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

        if (
            self.source_type.currentText() == "Arquivo local"
            and not Path(source).is_file()
        ):
            self._set_status("A planilha local nao foi encontrada.", "error")
            self._set_schema_status(
                "Base invalida: arquivo local nao encontrado.", "error"
            )
            return False

        if self.source_type.currentText() == "OneDrive" and not source.startswith(
            "https://"
        ):
            self._set_status("Informe um link valido do OneDrive.", "error")
            self._set_schema_status(
                "Base invalida: link do OneDrive nao reconhecido.", "error"
            )
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
                "Informe a fonte de dados. A validacao da base padronizada "
                "sera executada automaticamente.",
                "info",
            )
        self._refresh_action_state()

    def _on_lookup_mode_changed(self, *_args: object) -> None:
        self.entry_lookup_name.clear()
        self.entry_lookup_matricula.clear()
        self._clear_lookup_state()
        self._sync_lookup_mode()
        if not self._schema_valid:
            self._refresh_action_state()
            return

        mode = self._selected_lookup_mode()
        if mode:
            self._set_status("Informe o valor da busca e clique em Pesquisar.", "info")
        else:
            self._set_status("Escolha o tipo de busca para continuar.", "info")
        self._refresh_action_state()

    def _on_lookup_input_changed(self, *_args: object) -> None:
        if self._lookup_matches or self._confirmed_employee is not None:
            self._lookup_matches = []
            self._lookup_source_result = None
            self._clear_confirmed_employee()
            self._populate_results_table([])
            if self._schema_valid and self._selected_lookup_mode():
                self._set_status(
                    "Filtro alterado. Pesquise novamente para atualizar os resultados.",
                    "info",
                )
        self._refresh_action_state()

    def _clear_schema_state(self) -> None:
        self._schema_valid = False
        self._schema_fields = {}
        self._set_schema_status("Base nao validada.", "warning")

    def _clear_lookup_state(
        self,
        *,
        clear_queries: bool = False,
        reset_mode: bool = False,
    ) -> None:
        self._lookup_matches = []
        self._lookup_source_result = None
        self._clear_confirmed_employee()
        self._populate_results_table([])
        if clear_queries:
            self.entry_lookup_name.clear()
            self.entry_lookup_matricula.clear()
        if reset_mode:
            self.lookup_mode.blockSignals(True)
            self.lookup_mode.setCurrentIndex(0)
            self.lookup_mode.blockSignals(False)
            self._sync_lookup_mode()
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
            self._set_status(
                "A ficha so pode buscar apos validar a base padronizada.", "warning"
            )
            return
        if self._worker is not None and self._worker.isRunning():
            return

        mode = self._selected_lookup_mode()
        if mode == "":
            self._set_status("Escolha o tipo de busca antes de pesquisar.", "warning")
            return

        query = self._active_lookup_value()
        if query == "":
            message = (
                "Informe um nome para pesquisar."
                if mode == "nome"
                else "Informe uma matricula para pesquisar."
            )
            self._set_status(message, "warning")
            return

        self._clear_lookup_state()
        self._worker_mode = "lookup"
        self._worker = FichaLookupWorker(self._get_worker_payload(validate_only=False))
        self._worker.succeeded.connect(self._handle_worker_success)
        self._worker.error.connect(self._handle_worker_error)
        self._worker.finished.connect(self._on_worker_finished)
        self._set_status("Pesquisando colaboradores na planilha...", "info")
        self._refresh_action_state()
        self._worker.start()

    def _get_worker_payload(self, *, validate_only: bool) -> dict[str, Any]:
        source_kind = (
            "local" if self.source_type.currentText() == "Arquivo local" else "onedrive"
        )
        mode = self._selected_lookup_mode()
        return {
            "spreadsheet_source": self.entry_source.text().strip(),
            "source_kind": source_kind,
            "lookup_name": (
                self.entry_lookup_name.text().strip() if mode == "nome" else ""
            ),
            "lookup_matricula": (
                self.entry_lookup_matricula.text().strip()
                if mode == "matricula"
                else ""
            ),
            "cache_enabled": self._config.get("cache_enabled", True),
            "cache_ttl_hours": self._config.get("cache_ttl_hours", 24),
            "force_refresh": False,
            "validate_only": validate_only,
        }

    def _handle_worker_success(self, result: dict[str, Any]) -> None:
        self._schema_valid = True
        self._schema_fields = dict(result.get("schema", {}))
        row_count = int(result.get("row_count", 0))
        schema_order_matches = bool(result.get("schema_order_matches", False))
        order_note = (
            " Layout de referencia da ficha confirmado."
            if schema_order_matches
            else " Layout diferente dos modelos de referencia, mas colunas reconhecidas."
        )
        self._set_schema_status(
            f"Base padronizada validada. {row_count} linha(s) reconhecida(s).{order_note}",
            "success",
        )

        if self._worker_mode == "validate":
            self._set_status(
                "Base validada. Escolha o tipo de busca e pesquise um colaborador.",
                "success",
            )
            self._refresh_action_state()
            return

        self._lookup_matches = list(result.get("matches", []))
        self._lookup_source_result = result.get("source_result")
        self._clear_confirmed_employee()
        self._populate_results_table(self._lookup_matches)

        if not self._lookup_matches:
            self._set_status(
                "Nenhum colaborador encontrado para o filtro informado.", "warning"
            )
        elif len(self._lookup_matches) == 1:
            self._set_status(
                "1 colaborador encontrado. Valide o colaborador selecionado para gerar a ficha.",
                "success",
            )
        else:
            self._set_status(
                f"{len(self._lookup_matches)} colaboradores encontrados. "
                "Selecione uma linha e valide o colaborador.",
                "info",
            )
        self._refresh_action_state()

    def _handle_worker_error(self, message: str) -> None:
        if (
            self._worker_mode == "validate"
            or "schema padrao da ficha" in message.lower()
        ):
            self._clear_schema_state()
            self._clear_lookup_state()
            self._set_schema_status(message, "error")
            self._set_status(message, "error")
        else:
            self._lookup_matches = []
            self._lookup_source_result = None
            self._clear_confirmed_employee()
            self._populate_results_table([])
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
                employee.get("matricula", "") or "-",
                employee.get("nome", ""),
                employee.get("cargo", ""),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.results_table.setItem(row, column, item)
        if employees:
            self.results_table.selectRow(0)
        else:
            self.results_table.clearSelection()

    def _selected_match(self) -> FichaEmployee | None:
        selection_model = self.results_table.selectionModel()
        if selection_model is None:
            return None
        selected_rows = selection_model.selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        if row < 0 or row >= len(self._lookup_matches):
            return None
        return self._lookup_matches[row]

    def _on_results_selection_changed(self) -> None:
        employee = self._selected_match()
        if (
            self._confirmed_employee is not None
            and employee is not None
            and employee != self._confirmed_employee
        ):
            self._clear_confirmed_employee()
            self._set_status(
                "Selecao alterada. Valide o colaborador selecionado para liberar a geracao.",
                "info",
            )
        self._refresh_action_state()

    def _confirm_selected_employee(self) -> None:
        employee = self._selected_match()
        if employee is None:
            self._set_status(
                "Selecione um colaborador na tabela para validar.", "warning"
            )
            return

        missing_required = reader.validate_ficha_employee(employee)
        if missing_required:
            self._set_status(
                "O colaborador selecionado nao possui os campos obrigatorios: "
                f"{', '.join(missing_required)}.",
                "error",
            )
            return

        self._confirmed_employee = employee
        label = employee.get("nome", "").strip() or "colaborador selecionado"
        self._set_status(
            f"Colaborador validado: {label}. Pronto para gerar a ficha.", "success"
        )
        self._refresh_action_state()

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
        has_mode = self._selected_lookup_mode() != ""
        has_query = self._active_lookup_value() != ""
        has_selection = self._selected_match() is not None
        self.btn_search.setEnabled(
            self._schema_valid and has_mode and has_query and not worker_running
        )
        self.btn_confirm.setEnabled(
            self._schema_valid and has_selection and not worker_running
        )
        self.btn_generate.setEnabled(
            self._schema_valid
            and self._confirmed_employee is not None
            and not worker_running
        )

    def _start_generation(self) -> None:
        if self._confirmed_employee is None:
            self._set_status("Valide um colaborador antes de gerar a ficha.", "warning")
            return
        self.generate_requested.emit(self._get_generation_payload())

    def set_sidebar_collapsed(self, collapsed: bool) -> None:
        margin = 18 if collapsed else 24
        self._root_layout.setContentsMargins(margin, margin, margin, margin)
        self._root_layout.setSpacing(12 if collapsed else 14)
        self._content_split.setSpacing(12 if collapsed else 14)
        for label in self._compact_labels:
            label.setVisible(not collapsed)
