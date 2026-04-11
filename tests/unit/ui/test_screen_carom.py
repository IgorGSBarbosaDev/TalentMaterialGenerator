from __future__ import annotations

from app.config.settings import get_default_output_dir
from app.ui.screen_carom import CaromScreen


def _employee(matricula: str, nome: str) -> dict[str, str]:
    return {
        "matricula": matricula,
        "nome": nome,
        "cargo": "Analista",
        "foto": "",
        "area": "Operacao",
        "localizacao": "",
        "unidade_gestao": "",
    }


def _load_employees(screen: CaromScreen) -> None:
    screen._handle_worker_success(
        {
            "schema": {"matricula": "Matricula", "nome": "Nome", "cargo": "Cargo"},
            "employees": [_employee("101", "Ana Martins"), _employee("102", "Carlos Souza")],
            "source_result": None,
            "employee_count": 2,
        }
    )


def test_carom_screen_get_generation_payload_uses_default_output_dir(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    _load_employees(screen)
    screen._add_employee("matricula:101")

    received = []
    screen.generate_requested.connect(received.append)
    screen._start_generation()

    assert received[0]["output_dir"] == str(get_default_output_dir())
    assert received[0]["preset_id"] == "regular"


def test_carom_screen_updates_completion_indicator(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    _load_employees(screen)
    screen._add_employee("matricula:101")

    assert screen.current_slide_label.text() == "Faltam 9 pessoas para completar o slide atual"


def test_carom_screen_prevents_duplicate_selection(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    _load_employees(screen)
    screen._add_employee("matricula:101")
    screen._add_employee("matricula:101")

    assert len(screen._selected_employees) == 1
    assert "já está selecionada" in screen.status_label.text()


def test_carom_screen_live_search_filters_loaded_rows(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    _load_employees(screen)

    screen.search_input.setText("carl")

    assert len(screen._filtered_employees) == 1
    assert screen._filtered_employees[0]["nome"] == "Carlos Souza"


def test_carom_screen_requires_title_and_selection_before_generation(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    _load_employees(screen)
    screen.title_field.setText("")
    screen._start_generation()

    assert "Informe um título" in screen.status_label.text()
    assert screen.btn_generate.isEnabled() is False


def test_carom_screen_handles_sidebar_collapsed_state(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)

    screen.set_sidebar_collapsed(True)
    assert screen.results_hint.isHidden() is True

    screen.set_sidebar_collapsed(False)
    assert screen.results_hint.isHidden() is False
