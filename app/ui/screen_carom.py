from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import get_default_output_dir
from app.core.generator_carom import (
    compute_current_slide_status,
    compute_projected_slide_count,
    get_carom_preset,
)
from app.core.reader import (
    CaromEmployee,
    carom_employee_key,
    filter_carom_employees,
    normalize_filename,
)
from app.core.worker import CaromLookupWorker
from app.ui.components import PreviewListItem, repolish


class _SelectableEmployeeCard(QFrame):
    add_requested = Signal(str)

    def __init__(self, employee_key: str, employee: CaromEmployee) -> None:
        super().__init__()
        self.employee_key = employee_key
        self.setObjectName("previewListItem")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        meta = f"{employee.get('cargo', '')} | Matrícula {employee.get('matricula', '-') or '-'}"
        self.preview = PreviewListItem(employee.get("nome", "") or "Sem Nome", meta)
        layout.addWidget(self.preview, 1)

        self.add_button = QPushButton("Adicionar")
        self.add_button.clicked.connect(lambda: self.add_requested.emit(self.employee_key))
        layout.addWidget(self.add_button)


class _SelectedEmployeeCard(QFrame):
    remove_requested = Signal(str)

    def __init__(self, employee_key: str, employee: CaromEmployee, index: int) -> None:
        super().__init__()
        self.employee_key = employee_key
        self.setObjectName("previewListItem")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        order = QLabel(str(index))
        order.setObjectName("statusBadge")
        order.setAlignment(Qt.AlignCenter)
        order.setFixedSize(30, 30)
        layout.addWidget(order)

        meta = f"{employee.get('cargo', '')} | Matrícula {employee.get('matricula', '-') or '-'}"
        self.preview = PreviewListItem(employee.get("nome", "") or "Sem Nome", meta)
        layout.addWidget(self.preview, 1)

        self.remove_button = QPushButton("Remover")
        self.remove_button.clicked.connect(lambda: self.remove_requested.emit(self.employee_key))
        layout.addWidget(self.remove_button)


class CaromScreen(QWidget):
    generate_requested = Signal(dict)

    page_title = "Carômetro"
    page_badge = "Grade"

    PRESET_OPTIONS: tuple[tuple[str, str], ...] = (
        ("Mini", "mini"),
        ("Regular", "regular"),
        ("Grande", "large"),
    )
    SEARCH_OPTIONS: tuple[tuple[str, str], ...] = (
        ("Nome", "nome"),
        ("Matrícula", "matricula"),
    )

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__()
        self.setObjectName("caromPage")
        self._config = dict(config)
        self._worker: CaromLookupWorker | None = None
        self._schema_valid = False
        self._loaded_employees: list[CaromEmployee] = []
        self._filtered_employees: list[CaromEmployee] = []
        self._selected_employees: list[CaromEmployee] = []
        self._selected_keys: set[str] = set()
        self._source_result = None
        self._schema_fields: dict[str, str | None] = {}

        layout = QVBoxLayout(self)
        self._root_layout = layout
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        source_panel = QFrame()
        source_panel.setObjectName("panel")
        source_layout = QGridLayout(source_panel)
        source_layout.setContentsMargins(16, 16, 16, 16)
        source_layout.setHorizontalSpacing(12)
        source_layout.setVerticalSpacing(10)
        source_layout.setColumnStretch(1, 1)
        source_layout.setColumnStretch(3, 1)

        self.source_type = QComboBox()
        self.source_type.addItems(["OneDrive", "Arquivo local"])
        self.source_type.currentTextChanged.connect(self._on_source_mode_changed)

        self.entry_source = QLineEdit(config.get("default_onedrive_url", ""))
        self.entry_source.textChanged.connect(self._on_source_changed)
        self.entry_source.editingFinished.connect(self._start_schema_validation)

        self.btn_browse_file = QPushButton("Procurar")
        self.btn_browse_file.clicked.connect(self._choose_source_file)

        self.model_selector = QComboBox()
        for label, value in self.PRESET_OPTIONS:
            self.model_selector.addItem(label, value)
        self.model_selector.setCurrentIndex(1)
        self.model_selector.currentIndexChanged.connect(self._refresh_selection_summary)

        self.title_field = QLineEdit("Carômetro")
        self.title_field.textChanged.connect(self._on_title_changed)
        self.filename_field = QLineEdit()
        self.filename_field.setReadOnly(True)

        self.entry_output = QLineEdit(str(get_default_output_dir()))
        self.entry_output.setReadOnly(True)

        self.schema_status_label = QLabel("")
        self.schema_status_label.setObjectName("statusLabel")
        self.schema_status_label.setWordWrap(True)

        source_layout.addWidget(self._field_label("Origem"), 0, 0)
        source_layout.addWidget(self.source_type, 0, 1)
        source_layout.addWidget(self._field_label("Modelo"), 0, 2)
        source_layout.addWidget(self.model_selector, 0, 3)
        source_layout.addWidget(self._field_label("Planilha / Link"), 1, 0)
        source_input_row = QWidget()
        source_input_layout = QHBoxLayout(source_input_row)
        source_input_layout.setContentsMargins(0, 0, 0, 0)
        source_input_layout.setSpacing(8)
        source_input_layout.addWidget(self.entry_source, 1)
        source_input_layout.addWidget(self.btn_browse_file)
        source_layout.addWidget(source_input_row, 1, 1, 1, 3)
        source_layout.addWidget(self._field_label("Título"), 2, 0)
        source_layout.addWidget(self.title_field, 2, 1)
        source_layout.addWidget(self._field_label("Nome do arquivo"), 2, 2)
        source_layout.addWidget(self.filename_field, 2, 3)
        source_layout.addWidget(self._field_label("Saída"), 3, 0)
        source_layout.addWidget(self.entry_output, 3, 1, 1, 3)
        source_layout.addWidget(self._field_label("Status da planilha"), 4, 0)
        source_layout.addWidget(self.schema_status_label, 4, 1, 1, 3)
        layout.addWidget(source_panel)

        split = QHBoxLayout()
        self._content_split = split
        split.setSpacing(14)

        search_panel = QFrame()
        search_panel.setObjectName("panel")
        search_layout = QVBoxLayout(search_panel)
        search_layout.setContentsMargins(16, 16, 16, 16)
        search_layout.setSpacing(10)

        search_header = QLabel("Busca e resultados")
        search_header.setObjectName("panelTitle")
        search_layout.addWidget(search_header)

        search_controls = QGridLayout()
        search_controls.setHorizontalSpacing(10)
        search_controls.setVerticalSpacing(8)
        search_controls.setColumnStretch(1, 1)

        self.search_mode = QComboBox()
        for label, value in self.SEARCH_OPTIONS:
            self.search_mode.addItem(label, value)
        self.search_mode.currentIndexChanged.connect(self._on_search_changed)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite para buscar pessoas")
        self.search_input.textChanged.connect(self._on_search_changed)

        self.results_hint = QLabel("Valide a planilha para habilitar a busca em tempo real.")
        self.results_hint.setObjectName("muted")
        self.results_hint.setWordWrap(True)

        search_controls.addWidget(self._field_label("Buscar por"), 0, 0)
        search_controls.addWidget(self.search_mode, 0, 1)
        search_controls.addWidget(self._field_label("Termo"), 1, 0)
        search_controls.addWidget(self.search_input, 1, 1)
        search_layout.addLayout(search_controls)
        search_layout.addWidget(self.results_hint)

        self.results_list = QListWidget()
        self.results_list.setObjectName("caromResultsList")
        self.results_list.setSpacing(6)
        search_layout.addWidget(self.results_list, 1)
        split.addWidget(search_panel, 5)

        selection_panel = QFrame()
        selection_panel.setObjectName("panel")
        selection_layout = QVBoxLayout(selection_panel)
        selection_layout.setContentsMargins(16, 16, 16, 16)
        selection_layout.setSpacing(10)

        selection_header = QLabel("Pessoas selecionadas")
        selection_header.setObjectName("panelTitle")
        selection_layout.addWidget(selection_header)

        summary_grid = QGridLayout()
        summary_grid.setHorizontalSpacing(10)
        summary_grid.setVerticalSpacing(6)

        self.total_selected_label = QLabel("0")
        self.capacity_label = QLabel(str(self.current_capacity))
        self.slide_count_label = QLabel("0")
        self.current_slide_label = QLabel("")
        self.current_slide_label.setObjectName("statusLabel")
        self.current_slide_label.setWordWrap(True)

        summary_grid.addWidget(self._field_label("Total selecionado"), 0, 0)
        summary_grid.addWidget(self.total_selected_label, 0, 1)
        summary_grid.addWidget(self._field_label("Capacidade por slide"), 1, 0)
        summary_grid.addWidget(self.capacity_label, 1, 1)
        summary_grid.addWidget(self._field_label("Slides previstos"), 2, 0)
        summary_grid.addWidget(self.slide_count_label, 2, 1)
        summary_grid.addWidget(self._field_label("Slide atual"), 3, 0)
        summary_grid.addWidget(self.current_slide_label, 3, 1)
        selection_layout.addLayout(summary_grid)

        self.selected_list = QListWidget()
        self.selected_list.setObjectName("caromSelectedList")
        self.selected_list.setSpacing(6)
        selection_layout.addWidget(self.selected_list, 1)
        split.addWidget(selection_panel, 4)
        layout.addLayout(split, 1)

        action_panel = QFrame()
        action_panel.setObjectName("panelAction")
        action_layout = QHBoxLayout(action_panel)
        action_layout.setContentsMargins(16, 12, 16, 12)
        action_layout.setSpacing(12)

        status_col = QVBoxLayout()
        status_col.setSpacing(6)
        footer_label = QLabel("Status da geração")
        footer_label.setObjectName("panelTitle")
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        status_col.addWidget(footer_label)
        status_col.addWidget(self.status_label)
        action_layout.addLayout(status_col, 1)

        self.btn_generate = QPushButton("GERAR CARÔMETRO")
        self.btn_generate.setObjectName("primary")
        self.btn_generate.clicked.connect(self._start_generation)
        self.btn_generate.setMinimumWidth(220)
        action_layout.addWidget(self.btn_generate)
        layout.addWidget(action_panel)

        self._compact_labels = [self.results_hint]
        self._sync_source_mode()
        self._sync_filename()
        self._set_schema_status("Planilha não validada.", "warning")
        self._set_status("Carregue uma planilha válida para começar a selecionar pessoas.", "info")
        self._refresh_selection_summary()
        self._refresh_action_state()

    @property
    def current_preset_id(self) -> str:
        return str(self.model_selector.currentData() or "regular")

    @property
    def current_capacity(self) -> int:
        return get_carom_preset(self.current_preset_id)["capacity"]

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fichaFieldLabel")
        return label

    def _set_status(self, message: str, state: str) -> None:
        self.status_label.setText(message)
        self.status_label.setProperty("state", state)
        repolish(self.status_label)

    def _set_schema_status(self, message: str, state: str) -> None:
        self.schema_status_label.setText(message)
        self.schema_status_label.setProperty("state", state)
        repolish(self.schema_status_label)

    def _set_invalid(self, widget: QWidget, is_invalid: bool) -> None:
        widget.setProperty("invalid", is_invalid)
        repolish(widget)

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
        self.title_field.setText("Carômetro")
        self.model_selector.setCurrentIndex(1)
        self._clear_loaded_data()
        self._sync_source_mode()
        self._sync_filename()
        self._set_schema_status("Planilha não validada.", "warning")
        self._set_status("Carregue uma planilha válida para começar a selecionar pessoas.", "info")
        self._refresh_selection_summary()
        self._refresh_action_state()

    def _choose_source_file(self) -> None:
        file_path, _filter = QFileDialog.getOpenFileName(
            self, "Selecionar planilha", "", "Excel (*.xlsx)"
        )
        if file_path:
            self.source_type.setCurrentText("Arquivo local")
            self.entry_source.setText(file_path)
            self._start_schema_validation()

    def _on_source_mode_changed(self, *_args: object) -> None:
        self._sync_source_mode()
        self._on_source_changed()

    def _sync_source_mode(self) -> None:
        local_mode = self.source_type.currentText() == "Arquivo local"
        self.btn_browse_file.setEnabled(local_mode)
        self.entry_source.setPlaceholderText(
            "C:\\dados\\colaboradores.xlsx"
            if local_mode
            else "https://... link compartilhado do OneDrive"
        )

    def _sync_filename(self) -> None:
        title = self.title_field.text().strip()
        self.filename_field.setText(normalize_filename(title))

    def _on_title_changed(self) -> None:
        self._set_invalid(self.title_field, False)
        self._sync_filename()
        self._refresh_action_state()

    def _on_source_changed(self, *_args: object) -> None:
        self._set_invalid(self.entry_source, False)
        self._schema_valid = False
        self._schema_fields = {}
        self._source_result = None
        self._clear_loaded_data()
        source = self.entry_source.text().strip()
        if source:
            self._set_schema_status("Validação da planilha pendente.", "info")
            self._set_status("Origem alterada. Valide a planilha para habilitar a busca.", "info")
        else:
            self._set_schema_status("Planilha não validada.", "warning")
            self._set_status("Carregue uma planilha válida para começar a selecionar pessoas.", "info")
        self._refresh_action_state()

    def _validate_source(self) -> bool:
        source = self.entry_source.text().strip()
        self._set_invalid(self.entry_source, source == "")
        if source == "":
            self._set_status("Informe a origem da planilha.", "warning")
            self._set_schema_status("Planilha não validada.", "warning")
            return False

        if self.source_type.currentText() == "Arquivo local" and not Path(source).is_file():
            self._set_status("A planilha local não foi encontrada.", "error")
            self._set_schema_status("Planilha inválida: arquivo local não encontrado.", "error")
            return False

        if self.source_type.currentText() == "OneDrive" and not source.startswith("https://"):
            self._set_status("Informe um link do OneDrive válido.", "error")
            self._set_schema_status("Planilha inválida: link do OneDrive não reconhecido.", "error")
            return False
        return True

    def _start_schema_validation(self) -> None:
        if not self._validate_source():
            self._refresh_action_state()
            return
        if self._worker is not None and self._worker.isRunning():
            return

        self._worker = CaromLookupWorker(
            {
                "spreadsheet_source": self.entry_source.text().strip(),
                "cache_enabled": self._config.get("cache_enabled", True),
                "cache_ttl_hours": self._config.get("cache_ttl_hours", 24),
                "force_refresh": False,
            }
        )
        self._worker.succeeded.connect(self._handle_worker_success)
        self._worker.error.connect(self._handle_worker_error)
        self._worker.finished.connect(self._on_worker_finished)
        self._set_schema_status("Validando planilha padronizada...", "info")
        self._set_status("Carregando pessoas da planilha...", "info")
        self._refresh_action_state()
        self._worker.start()

    def _handle_worker_success(self, result: dict[str, Any]) -> None:
        self._schema_valid = True
        self._schema_fields = dict(result.get("schema", {}))
        self._source_result = result.get("source_result")
        self._loaded_employees = list(result.get("employees", []))
        self._selected_employees = []
        self._selected_keys = set()
        self.search_input.clear()
        self._filtered_employees = list(self._loaded_employees)
        employee_count = int(result.get("employee_count", 0))
        self._set_schema_status(
            f"Planilha padronizada validada. {employee_count} colaborador(es) carregado(s).",
            "success",
        )
        self._set_status("Planilha carregada. Use a busca em tempo real para montar o carômetro.", "success")
        self._refresh_results()
        self._refresh_selected_list()
        self._refresh_selection_summary()
        self._refresh_action_state()

    def _handle_worker_error(self, message: str) -> None:
        self._schema_valid = False
        self._schema_fields = {}
        self._source_result = None
        self._clear_loaded_data()
        self._set_schema_status(message, "error")
        self._set_status(message, "error")
        self._refresh_action_state()

    def _on_worker_finished(self) -> None:
        self._worker = None
        self._refresh_action_state()

    def _clear_loaded_data(self) -> None:
        self._loaded_employees = []
        self._filtered_employees = []
        self._selected_employees = []
        self._selected_keys = set()
        self.results_list.clear()
        self.selected_list.clear()
        self.results_hint.setText("Valide a planilha para habilitar a busca em tempo real.")
        self._refresh_selection_summary()

    def _on_search_changed(self, *_args: object) -> None:
        self._refresh_results()
        self._refresh_action_state()

    def _refresh_results(self) -> None:
        self.results_list.clear()
        if not self._schema_valid:
            self.results_hint.setText("Valide a planilha para habilitar a busca em tempo real.")
            return

        query = self.search_input.text().strip()
        mode = str(self.search_mode.currentData() or "nome")
        filtered = filter_carom_employees(self._loaded_employees, query=query, mode=mode)
        self._filtered_employees = [
            employee
            for employee in filtered
            if carom_employee_key(employee) not in self._selected_keys
        ]

        if not self._filtered_employees:
            self.results_hint.setText(
                "Nenhum resultado disponível para a busca atual."
                if query
                else "Todas as pessoas carregadas já foram selecionadas."
            )
            return

        result_count = len(self._filtered_employees)
        self.results_hint.setText(
            "1 resultado disponível."
            if result_count == 1
            else f"{result_count} resultados disponíveis."
        )
        for employee in self._filtered_employees:
            key = carom_employee_key(employee)
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 52))
            card = _SelectableEmployeeCard(key, employee)
            card.add_requested.connect(self._add_employee)
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, card)

    def _refresh_selected_list(self) -> None:
        self.selected_list.clear()
        for index, employee in enumerate(self._selected_employees, start=1):
            key = carom_employee_key(employee)
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 52))
            card = _SelectedEmployeeCard(key, employee, index)
            card.remove_requested.connect(self._remove_employee)
            self.selected_list.addItem(item)
            self.selected_list.setItemWidget(item, card)

    def _add_employee(self, employee_key: str) -> None:
        if employee_key in self._selected_keys:
            self._set_status("Esta pessoa já está selecionada.", "warning")
            return
        employee = next(
            (
                row
                for row in self._filtered_employees
                if carom_employee_key(row) == employee_key
            ),
            None,
        )
        if employee is None:
            return
        self._selected_employees.append(employee)
        self._selected_keys.add(employee_key)
        self._refresh_results()
        self._refresh_selected_list()
        self._refresh_selection_summary()
        self._set_status(
            f"{employee.get('nome', 'colaborador')} adicionado(a) à seleção do carômetro.",
            "success",
        )
        self._refresh_action_state()

    def _remove_employee(self, employee_key: str) -> None:
        self._selected_employees = [
            employee
            for employee in self._selected_employees
            if carom_employee_key(employee) != employee_key
        ]
        self._selected_keys.discard(employee_key)
        self._refresh_results()
        self._refresh_selected_list()
        self._refresh_selection_summary()
        self._set_status("Pessoa removida da seleção atual.", "info")
        self._refresh_action_state()

    def _refresh_selection_summary(self) -> None:
        capacity = self.current_capacity
        selected_count = len(self._selected_employees)
        self.total_selected_label.setText(str(selected_count))
        self.capacity_label.setText(str(capacity))
        self.slide_count_label.setText(
            str(compute_projected_slide_count(selected_count, capacity))
        )
        self.current_slide_label.setText(
            compute_current_slide_status(selected_count, capacity)
        )
        self.current_slide_label.setProperty(
            "state", "success" if selected_count and selected_count % capacity == 0 else "info"
        )
        repolish(self.current_slide_label)

    def _refresh_action_state(self) -> None:
        worker_running = self._worker is not None and self._worker.isRunning()
        title = self.title_field.text().strip()
        filename = self.filename_field.text().strip()
        ready_to_generate = (
            self._schema_valid
            and bool(self._selected_employees)
            and bool(title)
            and bool(filename)
            and not worker_running
        )
        self.search_mode.setEnabled(self._schema_valid and not worker_running)
        self.search_input.setEnabled(self._schema_valid and not worker_running)
        self.model_selector.setEnabled(not worker_running)
        self.source_type.setEnabled(not worker_running)
        self.entry_source.setEnabled(not worker_running)
        self.btn_browse_file.setEnabled(
            self.source_type.currentText() == "Arquivo local" and not worker_running
        )
        self.title_field.setEnabled(not worker_running)
        self.btn_generate.setEnabled(ready_to_generate)

    def _start_generation(self) -> None:
        title = self.title_field.text().strip()
        filename = self.filename_field.text().strip()
        self._set_invalid(self.title_field, title == "")
        if title == "":
            self._set_status("Informe um título antes de exportar.", "warning")
            return
        if filename == "":
            self._set_status("O nome de arquivo derivado é inválido. Ajuste o título.", "warning")
            return
        if not self._schema_valid:
            self._set_status("Valide a planilha antes de exportar.", "warning")
            return
        if not self._selected_employees:
            self._set_status("Selecione pelo menos uma pessoa antes de exportar.", "warning")
            return

        self.generate_requested.emit(
            {
                "output_dir": str(get_default_output_dir()),
                "selected_employees": list(self._selected_employees),
                "source_result": self._source_result,
                "preset_id": self.current_preset_id,
                "titulo": title,
                "file_basename": filename,
            }
        )

    def set_sidebar_collapsed(self, collapsed: bool) -> None:
        margin = 18 if collapsed else 22
        self._root_layout.setContentsMargins(margin, margin, margin, margin)
        self._root_layout.setSpacing(10 if collapsed else 14)
        self._content_split.setSpacing(10 if collapsed else 14)
        for label in self._compact_labels:
            label.setVisible(not collapsed)
