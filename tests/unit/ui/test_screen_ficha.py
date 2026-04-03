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


def test_ficha_screen_confirms_selected_employee_and_populates_readonly_fields(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)
    screen._schema_valid = True
    screen._handle_worker_success(
        {
            "schema": {"matricula": "Matricula", "nome": "Nome", "cargo": "Cargo"},
            "row_count": 1,
            "matches": [_employee()],
            "source_result": None,
        }
    )
    screen._confirm_selected_employee()

    assert screen._confirmed_employee is not None
    assert screen.detail_nome.text() == "Ana Martins"
    assert screen.detail_nota_2025.text() == "5 / AP"
    assert screen.detail_nota_2024.text() == "4 / PROM"
    assert screen.detail_nota_2023.text() == "3 / MN+"
    assert screen.btn_generate.isEnabled() is True


def test_ficha_screen_marks_exact_schema_order_in_status(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)
    screen._worker_mode = "validate"

    screen._handle_worker_success(
        {
            "schema": {"matricula": "Matricula", "nome": "Nome", "cargo": "Cargo"},
            "row_count": 2,
            "matches": [],
            "source_result": None,
            "schema_order_matches": True,
        }
    )

    assert "ordem esperada confirmada" in screen.schema_status_label.text().lower()


def test_ficha_screen_lookup_change_clears_confirmed_employee(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)
    screen._schema_valid = True
    screen._confirmed_employee = _employee()
    screen.detail_nome.setText("Ana Martins")
    screen._lookup_matches = [_employee()]
    screen.entry_lookup_name.setText("Carlos")

    assert screen._confirmed_employee is None
    assert screen.detail_nome.text() == ""
    assert screen.btn_generate.isEnabled() is False


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
    assert screen._root_layout.spacing() == 14

    screen.set_sidebar_collapsed(False)
    assert screen._root_layout.spacing() == 18


def test_ficha_screen_uses_dedicated_workflow_surfaces(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)

    assert screen.findChild(QFrame, "fichaSourceCard") is not None
    assert screen.findChild(QFrame, "fichaWorkflowCard") is not None
    assert screen.findChild(QFrame, "fichaLookupPane") is not None
    assert screen.findChild(QFrame, "fichaDossierPane") is not None
    assert screen.findChild(QFrame, "fichaActionBar") is not None
    assert screen.results_table.objectName() == "fichaResultsTable"
