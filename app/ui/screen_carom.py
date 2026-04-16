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
    validate_carom_schema_for_preset,
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

        meta = f"{employee.get('cargo', '')} | Matricula {employee.get('matricula', '-') or '-'}"
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

        meta = f"{employee.get('cargo', '')} | Matricula {employee.get('matricula', '-') or '-'}"
        self.preview = PreviewListItem(employee.get("nome", "") or "Sem Nome", meta)
        layout.addWidget(self.preview, 1)

        self.remove_button = QPushButton("Remover")
        self.remove_button.clicked.connect(lambda: self.remove_requested.emit(self.employee_key))
        layout.addWidget(self.remove_button)


class CaromScreen(QWidget):
    generate_requested = Signal(dict)

    page_title = "Carometro"
    page_badge = "Grade"

    PRESET_OPTIONS: tuple[tuple[str, str], ...] = (
        ("Mini", "mini"),
        ("Big", "big"),
        ("Projeto Trainee", "projeto_trainee"),
        ("Talent Review", "talent_review"),
    )
    SEARCH_OPTIONS: tuple[tuple[str, str], ...] = (
        ("Nome", "nome"),
        ("Matricula", "matricula"),
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
        self._last_editable_title = "Carometro"
        self._current_page = 1
        self._page_size = 50
        self._applied_search_query = ""
        self._applied_search_mode = "nome"

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
        self.model_selector.currentIndexChanged.connect(self._on_preset_changed)

        self.title_field = QLineEdit("Carometro")
        self.title_field.textChanged.connect(self._on_title_changed)

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
        source_layout.addWidget(self._field_label("Titulo"), 2, 0)
        source_layout.addWidget(self.title_field, 2, 1)
        source_layout.addWidget(self._field_label("Status da planilha"), 2, 2)
        source_layout.addWidget(self.schema_status_label, 2, 3)
        source_layout.addWidget(self._field_label("Saida"), 3, 0)
        source_layout.addWidget(self.entry_output, 3, 1, 1, 3)
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
        self.search_mode.currentIndexChanged.connect(self._on_search_filter_changed)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite nome ou matricula")
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_input.returnPressed.connect(self._apply_search)

        self.btn_search = QPushButton("Pesquisar")
        self.btn_search.clicked.connect(self._apply_search)

        self.results_hint = QLabel("Valide a planilha para habilitar a busca.")
        self.results_hint.setObjectName("muted")
        self.results_hint.setWordWrap(True)

        self.pagination_count_label = QLabel("")
        self.pagination_count_label.setObjectName("muted")
        self.pagination_count_label.setWordWrap(True)

        self.btn_previous_page = QPushButton("Anterior")
        self.btn_previous_page.clicked.connect(self._go_to_previous_page)

        self.page_indicator = QLabel("Pagina 0 de 0")
        self.page_indicator.setObjectName("muted")
        self.page_indicator.setAlignment(Qt.AlignCenter)

        self.btn_next_page = QPushButton("Proximo")
        self.btn_next_page.clicked.connect(self._go_to_next_page)

        search_controls.addWidget(self._field_label("Buscar por"), 0, 0)
        search_controls.addWidget(self.search_mode, 0, 1)
        search_controls.addWidget(self._field_label("Termo"), 1, 0)
        search_controls.addWidget(self.search_input, 1, 1)
        search_controls.addWidget(self.btn_search, 1, 2)
        search_layout.addLayout(search_controls)
        search_layout.addWidget(self.results_hint)

        self.results_list = QListWidget()
        self.results_list.setObjectName("caromResultsList")
        self.results_list.setSpacing(6)
        search_layout.addWidget(self.results_list, 1)

        pagination_layout = QHBoxLayout()
        pagination_layout.setSpacing(8)
        pagination_layout.addWidget(self.pagination_count_label, 1)
        pagination_layout.addWidget(self.btn_previous_page)
        pagination_layout.addWidget(self.page_indicator)
        pagination_layout.addWidget(self.btn_next_page)
        search_layout.addLayout(pagination_layout)
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
        footer_label = QLabel("Status da geracao")
        footer_label.setObjectName("panelTitle")
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        status_col.addWidget(footer_label)
        status_col.addWidget(self.status_label)
        action_layout.addLayout(status_col, 1)

        self.btn_generate = QPushButton("GERAR CAROMETRO")
        self.btn_generate.setObjectName("primary")
        self.btn_generate.clicked.connect(self._start_generation)
        self.btn_generate.setMinimumWidth(220)
        action_layout.addWidget(self.btn_generate)
        layout.addWidget(action_panel)

        self._compact_labels = [self.results_hint]
        self._sync_source_mode()
        self._sync_title_mode(reset_title=True)
        self._refresh_preset_option_states()
        self._set_schema_status("Planilha nao validada.", "warning")
        self._set_status("Carregue uma planilha valida para comecar a selecionar pessoas.", "info")
        self._refresh_selection_summary()
        self._refresh_action_state()
        self._update_pagination_state()

    @property
    def current_preset_id(self) -> str:
        return str(self.model_selector.currentData() or "big")

    @property
    def current_capacity(self) -> int:
        return get_carom_preset(self.current_preset_id).capacity

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
        self._last_editable_title = "Carometro"
        self.model_selector.setCurrentIndex(1)
        self._clear_loaded_data()
        self._sync_source_mode()
        self._sync_title_mode(reset_title=True)
        self._refresh_preset_option_states()
        self._set_schema_status("Planilha nao validada.", "warning")
        self._set_status("Carregue uma planilha valida para comecar a selecionar pessoas.", "info")
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

    def _sync_title_mode(self, *, reset_title: bool = False) -> None:
        preset = get_carom_preset(self.current_preset_id)
        if preset.editable_title:
            self.title_field.setReadOnly(False)
            self.title_field.setEnabled(True)
            if reset_title or self.title_field.text().strip() in {"", "Carometro Projeto Trainee", "Talent Review"}:
                self.title_field.setText(self._last_editable_title or preset.default_title)
            return

        current_text = self.title_field.text().strip()
        if current_text:
            self._last_editable_title = current_text
        self.title_field.setText(preset.default_title)
        self.title_field.setReadOnly(True)
        self.title_field.setEnabled(False)

    def _derive_filename(self) -> str:
        return normalize_filename(self.title_field.text().strip())

    def _on_title_changed(self) -> None:
        if get_carom_preset(self.current_preset_id).editable_title:
            self._last_editable_title = self.title_field.text().strip() or self._last_editable_title
        self._set_invalid(self.title_field, False)
        self._refresh_action_state()

    def _on_preset_changed(self, *_args: object) -> None:
        self._sync_title_mode()
        self._refresh_selection_summary()
        self._refresh_preset_schema_status()
        self._refresh_action_state()

    def _on_source_changed(self, *_args: object) -> None:
        self._set_invalid(self.entry_source, False)
        self._schema_valid = False
        self._schema_fields = {}
        self._source_result = None
        self._clear_loaded_data()
        self._refresh_preset_option_states()
        source = self.entry_source.text().strip()
        if source:
            self._set_schema_status("Validacao da planilha pendente.", "info")
            self._set_status("Origem alterada. Valide a planilha para habilitar a busca.", "info")
        else:
            self._set_schema_status("Planilha nao validada.", "warning")
            self._set_status("Carregue uma planilha valida para comecar a selecionar pessoas.", "info")
        self._refresh_action_state()

    def _validate_source(self) -> bool:
        source = self.entry_source.text().strip()
        self._set_invalid(self.entry_source, source == "")
        if source == "":
            self._set_status("Informe a origem da planilha.", "warning")
            self._set_schema_status("Planilha nao validada.", "warning")
            return False

        if self.source_type.currentText() == "Arquivo local" and not Path(source).is_file():
            self._set_status("A planilha local nao foi encontrada.", "error")
            self._set_schema_status("Planilha invalida: arquivo local nao encontrado.", "error")
            return False

        if self.source_type.currentText() == "OneDrive" and not source.startswith("https://"):
            self._set_status("Informe um link do OneDrive valido.", "error")
            self._set_schema_status("Planilha invalida: link do OneDrive nao reconhecido.", "error")
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
        self._applied_search_query = ""
        self._applied_search_mode = str(self.search_mode.currentData() or "nome")
        self._set_filtered_employees(self._loaded_employees)
        self._refresh_preset_option_states()
        self._select_first_compatible_preset()
        employee_count = int(result.get("employee_count", 0))
        self._refresh_preset_schema_status(employee_count=employee_count)
        self._refresh_selected_list()
        self._refresh_selection_summary()
        self._refresh_action_state()

    def _handle_worker_error(self, message: str) -> None:
        self._schema_valid = False
        self._schema_fields = {}
        self._source_result = None
        self._clear_loaded_data()
        self._refresh_preset_option_states()
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
        self._current_page = 1
        self._applied_search_query = ""
        self._applied_search_mode = "nome"
        self.results_list.clear()
        self.selected_list.clear()
        self.results_hint.setText("Valide a planilha para habilitar a busca.")
        self._update_pagination_state()
        self._refresh_selection_summary()

    def _current_preset_missing_fields(self) -> list[str]:
        if not self._schema_valid:
            return []
        return validate_carom_schema_for_preset(self._schema_fields, self.current_preset_id)

    def _preset_missing_fields(self, preset_id: str) -> list[str]:
        if not self._schema_valid:
            return []
        return validate_carom_schema_for_preset(self._schema_fields, preset_id)

    def _refresh_preset_option_states(self) -> None:
        model = self.model_selector.model()
        for index in range(self.model_selector.count()):
            item = model.item(index)
            if item is None:
                continue
            preset_id = str(self.model_selector.itemData(index))
            missing = self._preset_missing_fields(preset_id)
            item.setEnabled(not missing)
            item.setToolTip(
                ""
                if not missing
                else f"Indisponivel para esta planilha. Campos ausentes: {', '.join(missing)}."
            )

    def _select_first_compatible_preset(self) -> None:
        if not self._schema_valid or not self._current_preset_missing_fields():
            return
        for index in range(self.model_selector.count()):
            preset_id = str(self.model_selector.itemData(index))
            if not self._preset_missing_fields(preset_id):
                self.model_selector.setCurrentIndex(index)
                return

    def _refresh_preset_schema_status(self, *, employee_count: int | None = None) -> None:
        if not self._schema_valid:
            return
        missing = self._current_preset_missing_fields()
        if missing:
            joined = ", ".join(missing)
            self._set_schema_status(
                f"Planilha validada, mas o template atual exige colunas ausentes: {joined}.",
                "warning",
            )
            self._set_status(
                f"O template atual nao pode ser gerado com esta planilha. Campos ausentes: {joined}.",
                "warning",
            )
            return

        loaded = employee_count if employee_count is not None else len(self._loaded_employees)
        self._set_schema_status(
            f"Planilha padronizada validada. {loaded} colaborador(es) carregado(s).",
            "success",
        )
        self._set_status(
            "Planilha carregada. Digite um termo e clique em Pesquisar para filtrar.",
            "success",
        )

    def _on_search_text_changed(self, *_args: object) -> None:
        if self._schema_valid:
            self._set_status(
                "Filtro alterado. Clique em Pesquisar para atualizar os resultados.",
                "info",
            )
        self._refresh_action_state()

    def _on_search_filter_changed(self, *_args: object) -> None:
        if self._schema_valid:
            self._set_status(
                "Tipo de busca alterado. Clique em Pesquisar para atualizar os resultados.",
                "info",
            )
        self._refresh_action_state()

    def _apply_search(self) -> None:
        if not self._schema_valid:
            self._set_status("Valide a planilha antes de pesquisar.", "warning")
            return

        self._applied_search_query = self.search_input.text().strip()
        self._applied_search_mode = str(self.search_mode.currentData() or "nome")
        filtered = filter_carom_employees(
            self._loaded_employees,
            query=self._applied_search_query,
            mode=self._applied_search_mode,
        )
        self._set_filtered_employees(filtered)
        if self._applied_search_query:
            self._set_status("Busca atualizada.", "success")
        else:
            self._set_status("Busca limpa. Exibindo todas as pessoas disponiveis.", "info")
        self._refresh_action_state()

    def _refresh_results(self) -> None:
        if not self._schema_valid:
            self.results_list.clear()
            self.results_hint.setText("Valide a planilha para habilitar a busca.")
            self._update_pagination_state()
            return

        filtered = filter_carom_employees(
            self._loaded_employees,
            query=self._applied_search_query,
            mode=self._applied_search_mode,
        )
        self._set_filtered_employees(filtered, reset_page=False)

    def _available_employees(self, employees: list[CaromEmployee]) -> list[CaromEmployee]:
        return [
            employee
            for employee in employees
            if carom_employee_key(employee) not in self._selected_keys
        ]

    def _set_filtered_employees(
        self,
        employees: list[CaromEmployee],
        *,
        reset_page: bool = True,
    ) -> None:
        self._filtered_employees = self._available_employees(list(employees))
        if reset_page:
            self._current_page = 1
        self._clamp_current_page()
        self._refresh_results_view()

    def _total_pages(self) -> int:
        if not self._filtered_employees:
            return 0
        return (len(self._filtered_employees) + self._page_size - 1) // self._page_size

    def _clamp_current_page(self) -> None:
        total_pages = self._total_pages()
        if total_pages == 0:
            self._current_page = 1
            return
        self._current_page = min(max(self._current_page, 1), total_pages)

    def _get_visible_page_records(self) -> list[CaromEmployee]:
        self._clamp_current_page()
        if not self._filtered_employees:
            return []
        start = (self._current_page - 1) * self._page_size
        end = start + self._page_size
        return self._filtered_employees[start:end]

    def _refresh_results_view(self) -> None:
        self.results_list.clear()
        if not self._schema_valid:
            self.results_hint.setText("Valide a planilha para habilitar a busca.")
            self._update_pagination_state()
            return

        if not self._filtered_employees:
            self.results_hint.setText(
                "Nenhum resultado disponivel para a busca atual."
                if self._applied_search_query
                else "Todas as pessoas carregadas ja foram selecionadas."
            )
            self._update_pagination_state()
            return

        result_count = len(self._filtered_employees)
        self.results_hint.setText(
            "1 resultado disponivel."
            if result_count == 1
            else f"{result_count} resultados disponiveis."
        )
        for employee in self._get_visible_page_records():
            key = carom_employee_key(employee)
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 52))
            card = _SelectableEmployeeCard(key, employee)
            card.add_requested.connect(self._add_employee)
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, card)
        self._update_pagination_state()

    def _update_pagination_state(self) -> None:
        total_records = len(self._filtered_employees) if self._schema_valid else 0
        total_pages = self._total_pages() if self._schema_valid else 0
        worker_running = self._worker is not None and self._worker.isRunning()
        if total_records == 0 or total_pages == 0:
            self.pagination_count_label.setText("Nenhum colaborador para exibir.")
            self.page_indicator.setText("Pagina 0 de 0")
        else:
            start = (self._current_page - 1) * self._page_size + 1
            end = min(start + self._page_size - 1, total_records)
            self.pagination_count_label.setText(
                f"Mostrando {start}-{end} de {total_records} colaborador(es)."
            )
            self.page_indicator.setText(f"Pagina {self._current_page} de {total_pages}")

        can_page = self._schema_valid and not worker_running and total_pages > 0
        self.btn_previous_page.setEnabled(can_page and self._current_page > 1)
        self.btn_next_page.setEnabled(can_page and self._current_page < total_pages)

    def _go_to_previous_page(self) -> None:
        if self._current_page <= 1:
            return
        self._current_page -= 1
        self._refresh_results_view()

    def _go_to_next_page(self) -> None:
        if self._current_page >= self._total_pages():
            return
        self._current_page += 1
        self._refresh_results_view()

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
            self._set_status("Esta pessoa ja esta selecionada.", "warning")
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
            f"{employee.get('nome', 'colaborador')} adicionado(a) a selecao do carometro.",
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
        self._set_status("Pessoa removida da selecao atual.", "info")
        self._refresh_action_state()

    def _refresh_selection_summary(self) -> None:
        capacity = self.current_capacity
        selected_count = len(self._selected_employees)
        self.total_selected_label.setText(str(selected_count))
        self.capacity_label.setText(str(capacity))
        self.slide_count_label.setText(str(compute_projected_slide_count(selected_count, capacity)))
        self.current_slide_label.setText(compute_current_slide_status(selected_count, capacity))
        self.current_slide_label.setProperty(
            "state", "success" if selected_count and selected_count % capacity == 0 else "info"
        )
        repolish(self.current_slide_label)

    def _refresh_action_state(self) -> None:
        worker_running = self._worker is not None and self._worker.isRunning()
        title = self.title_field.text().strip()
        filename = self._derive_filename()
        missing_fields = self._current_preset_missing_fields()
        preset = get_carom_preset(self.current_preset_id)
        ready_to_generate = (
            self._schema_valid
            and not missing_fields
            and bool(self._selected_employees)
            and bool(title)
            and bool(filename)
            and not worker_running
        )
        self.search_mode.setEnabled(self._schema_valid and not worker_running)
        self.search_input.setEnabled(self._schema_valid and not worker_running)
        self.btn_search.setEnabled(self._schema_valid and not worker_running)
        self.model_selector.setEnabled(not worker_running)
        self.source_type.setEnabled(not worker_running)
        self.entry_source.setEnabled(not worker_running)
        self.btn_browse_file.setEnabled(
            self.source_type.currentText() == "Arquivo local" and not worker_running
        )
        if preset.editable_title:
            self.title_field.setEnabled(not worker_running)
        self.btn_generate.setEnabled(ready_to_generate)
        self._update_pagination_state()

    def _start_generation(self) -> None:
        title = self.title_field.text().strip()
        filename = self._derive_filename()
        self._set_invalid(self.title_field, title == "")
        if title == "":
            self._set_status("Informe um titulo antes de exportar.", "warning")
            return
        if filename == "":
            self._set_status("O nome de arquivo derivado e invalido. Ajuste o titulo.", "warning")
            return
        if not self._schema_valid:
            self._set_status("Valide a planilha antes de exportar.", "warning")
            return
        missing_fields = self._current_preset_missing_fields()
        if missing_fields:
            joined = ", ".join(missing_fields)
            self._set_status(
                f"O template atual exige colunas ausentes na planilha: {joined}.",
                "warning",
            )
            return
        if not self._selected_employees:
            self._set_status("Selecione pelo menos uma pessoa antes de exportar.", "warning")
            return

        self.generate_requested.emit(
            {
                "output_dir": str(get_default_output_dir()),
                "selected_employees": list(self._selected_employees),
                "source_result": self._source_result,
                "schema_fields": dict(self._schema_fields),
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
