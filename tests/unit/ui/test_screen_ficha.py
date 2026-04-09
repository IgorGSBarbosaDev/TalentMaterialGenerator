from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from PySide6.QtWidgets import QFrame, QLabel

from app.config.settings import get_default_output_dir
from app.core.reader import FichaEmployee
from app.ui.screen_ficha import FichaScreen


def _make_local_spreadsheet_stub() -> Path:
    temp_dir = Path.cwd() / ".tmp-test-ui"
    temp_dir.mkdir(exist_ok=True)
    file_path = temp_dir / f"dados-{uuid4().hex}.xlsx"
    file_path.write_bytes(b"x")
    return file_path


def _employee(**overrides: str) -> FichaEmployee:
    base: FichaEmployee = {
        "matricula": "123",
        "nome": "Ana Martins",
        "idade": "30",
        "cargo": "Analista",
        "antiguidade": "5 anos",
        "formacao": "Engenharia",
        "resumo_perfil": "Resumo profissional",
        "trajetoria": "2024 - Coordenadora",
        "nota_2025": "5 / AP",
        "nota_2024": "4 / PROM",
        "nota_2023": "3 / MN+",
    }
    base.update(overrides)
    return base


def test_ficha_screen_validates_local_file_source(qtbot) -> None:
    file_path = _make_local_spreadsheet_stub()
    try:
        screen = FichaScreen({})
        qtbot.addWidget(screen)
        screen.source_type.setCurrentText("Arquivo local")
        screen.entry_source.setText(str(file_path))

        assert screen._validate_source() is True
    finally:
        file_path.unlink(missing_ok=True)


def test_ficha_screen_source_fields_use_shared_runtime_states(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)

    assert screen.entry_source.isReadOnly() is False
    assert screen.entry_source.isEnabled() is True
    assert screen.entry_source.styleSheet() == ""
    assert screen.entry_output.isReadOnly() is True
    assert screen.entry_output.isEnabled() is True
    assert screen.entry_output.styleSheet() == ""


def test_ficha_screen_starts_with_explicit_search_mode_required(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)

    assert screen.lookup_mode.currentIndex() == 0
    assert screen.lookup_name_container.isHidden() is True
    assert screen.lookup_matricula_container.isHidden() is True
    assert screen.btn_search.isEnabled() is False


def test_ficha_screen_search_mode_shows_only_active_field(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)

    screen.lookup_mode.setCurrentIndex(1)
    assert screen.lookup_name_container.isHidden() is False
    assert screen.lookup_matricula_container.isHidden() is True

    screen.lookup_mode.setCurrentIndex(2)
    assert screen.lookup_name_container.isHidden() is True
    assert screen.lookup_matricula_container.isHidden() is False


def test_ficha_screen_get_worker_payload_respects_selected_search_mode(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)
    screen.entry_source.setText("https://example.com/file.xlsx")

    screen.lookup_mode.setCurrentIndex(1)
    screen.entry_lookup_name.setText("Luiza")
    payload = screen._get_worker_payload(validate_only=False)
    assert payload["lookup_name"] == "Luiza"
    assert payload["lookup_matricula"] == ""

    screen.lookup_mode.setCurrentIndex(2)
    screen.entry_lookup_matricula.setText("123")
    payload = screen._get_worker_payload(validate_only=False)
    assert payload["lookup_name"] == ""
    assert payload["lookup_matricula"] == "123"


def test_ficha_screen_generate_payload_uses_confirmed_employee(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)
    screen.entry_source.setText("https://example.com/file.xlsx")
    screen._confirmed_employee = _employee()

    payload = screen._get_generation_payload()

    assert payload["output_dir"] == str(get_default_output_dir())
    assert payload["selected_employee"]["nome"] == "Ana Martins"
    assert "column_mapping" not in payload


def test_ficha_screen_search_requires_schema_validation(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)
    screen.lookup_mode.setCurrentIndex(1)
    screen.entry_lookup_name.setText("Ana")
    screen._refresh_action_state()

    assert screen.btn_search.isEnabled() is False


def test_ficha_screen_worker_success_marks_schema_valid(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)
    screen._worker_mode = "validate"

    screen._handle_worker_success(
        {
            "schema": {"matricula": "Matricula", "nome": "Nome", "cargo": "Cargo"},
            "row_count": 2,
            "matches": [],
            "source_result": None,
        }
    )

    assert screen._schema_valid is True
    assert "validada" in screen.schema_status_label.text().lower()


def test_ficha_screen_lookup_populates_results_table_with_multiple_name_matches(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)
    screen._schema_valid = True
    screen.lookup_mode.setCurrentIndex(1)
    screen.entry_lookup_name.setText("Luiza")

    screen._worker_mode = "lookup"
    screen._handle_worker_success(
        {
            "schema": {"matricula": "Matricula", "nome": "Nome", "cargo": "Cargo"},
            "row_count": 3,
            "matches": [
                _employee(matricula="101", nome="Luiza Quirino", cargo="Analista"),
                _employee(matricula="102", nome="Luiza Miranda", cargo="Coordenadora"),
                _employee(matricula="103", nome="Luiza Martins", cargo="Especialista"),
            ],
            "source_result": None,
        }
    )

    assert screen.results_table.rowCount() == 3
    assert screen.results_table.item(0, 0).text() == "101"
    assert screen.results_table.item(1, 1).text() == "Luiza Miranda"
    assert screen.results_table.item(2, 2).text() == "Especialista"
    assert "3 colaboradores encontrados" in screen.status_label.text().lower()


def test_ficha_screen_validate_button_depends_on_selected_row(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)
    screen._schema_valid = True
    screen._lookup_matches = [_employee(), _employee(matricula="456", nome="Carlos")]
    screen._populate_results_table(screen._lookup_matches)
    screen._refresh_action_state()

    assert screen.btn_confirm.isEnabled() is True

    screen.results_table.clearSelection()
    screen._refresh_action_state()

    assert screen.btn_confirm.isEnabled() is False


def test_ficha_screen_validates_selected_employee_and_clears_confirmation_on_selection_change(
    qtbot,
) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)
    screen._schema_valid = True
    screen._lookup_matches = [
        _employee(matricula="101", nome="Luiza Quirino"),
        _employee(matricula="102", nome="Luiza Miranda"),
    ]
    screen._populate_results_table(screen._lookup_matches)

    screen._confirm_selected_employee()
    assert screen._confirmed_employee is not None
    assert screen.btn_generate.isEnabled() is True

    screen.results_table.selectRow(1)

    assert screen._confirmed_employee is None
    assert screen.btn_generate.isEnabled() is False
    assert "selecao alterada" in screen.status_label.text().lower()


def test_ficha_screen_lookup_mode_change_clears_results_and_confirmed_employee(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)
    screen._schema_valid = True
    screen.lookup_mode.setCurrentIndex(1)
    screen.entry_lookup_name.setText("Ana")
    screen._lookup_matches = [_employee()]
    screen._confirmed_employee = _employee()
    screen._populate_results_table(screen._lookup_matches)

    screen.lookup_mode.setCurrentIndex(2)

    assert screen._confirmed_employee is None
    assert screen.results_table.rowCount() == 0
    assert screen.entry_lookup_name.text() == ""
    assert screen.entry_lookup_matricula.text() == ""


def test_ficha_screen_has_no_mapping_or_auto_detect_text(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)

    labels = [label.text().lower() for label in screen.findChildren(QLabel)]
    buttons = [button.text().lower() for button in screen.findChildren(type(screen.btn_search))]
    assert all("mapeamento" not in text for text in labels)
    assert all("auto-detectar" not in text for text in buttons)


def test_ficha_screen_handles_sidebar_collapsed_state(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)

    screen.set_sidebar_collapsed(True)
    assert screen._root_layout.spacing() == 12

    screen.set_sidebar_collapsed(False)
    assert screen._root_layout.spacing() == 14


def test_ficha_screen_uses_two_card_workflow_surfaces(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)

    assert screen.findChild(QFrame, "fichaSourceCard") is not None
    assert screen.findChild(QFrame, "fichaLookupPane") is not None
    assert screen.findChild(QFrame, "fichaResultsPane") is not None
    assert screen.findChild(QFrame, "fichaDossierPane") is None
    assert screen.findChild(QFrame, "fichaActionBar") is not None
    assert screen.results_table.objectName() == "fichaResultsTable"


def test_ficha_screen_results_table_uses_expected_column_order(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)

    headers = [
        screen.results_table.horizontalHeaderItem(index).text()
        for index in range(screen.results_table.columnCount())
    ]

    assert headers == ["Matricula", "Nome", "Cargo"]


def test_ficha_screen_removes_old_explanatory_texts(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)

    labels = [label.text() for label in screen.findChildren(QLabel)]

    forbidden_texts = [
        "Base padronizada e busca individual",
        "Valide a base padronizada, encontre um colaborador e revise os dados antes de gerar a ficha.",
        "Busque por nome ou matricula, confirme um colaborador e revise o dossie antes de gerar.",
        "Selecione uma linha e confirme o colaborador que sera usado na geracao individual.",
        "Colaborador confirmado",
        "Identificacao",
        "Resumo profissional",
        "Narrativa recuperada",
        "Notas anuais",
    ]

    for text in forbidden_texts:
        assert text not in labels
