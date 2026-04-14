from __future__ import annotations

from app.config.settings import get_default_output_dir
from app.core.reader import normalize_filename
from app.ui.screen_carom import CaromScreen


def _employee(matricula: str, nome: str) -> dict[str, str]:
    return {
        "matricula": matricula,
        "nome": nome,
        "idade": "31",
        "cargo": "Analista",
        "formacao": "Engenharia",
        "resumo_perfil": "",
        "trajetoria": "",
        "foto": "",
        "area": "Operacao",
        "localizacao": "",
        "unidade_gestao": "",
        "nota_2025": "4 / AP",
        "avaliacao_2025": "4 / AP",
        "score_2025": "4",
        "potencial_2025": "AP",
        "ceo3": "CEO3",
        "ceo4": "CEO4",
    }


def _legacy_employee(matricula: str, nome: str) -> dict[str, str]:
    employee = _employee(matricula, nome)
    for field in (
        "formacao",
        "nota_2025",
        "avaliacao_2025",
        "score_2025",
        "potencial_2025",
        "ceo3",
        "ceo4",
    ):
        employee[field] = ""
    return employee


def _load_employees(screen: CaromScreen) -> None:
    screen._handle_worker_success(
        {
            "schema": {
                "matricula": "Matricula",
                "nome": "Nome",
                "idade": "Idade",
                "cargo": "Cargo",
                "formacao": "Formacao",
                "nota_2025": "Nota 2025",
                "potencial_2025": "Potencial 2025",
                "ceo3": "CEO3",
                "ceo4": "CEO4",
            },
            "employees": [_employee("101", "Ana Martins"), _employee("102", "Carlos Souza")],
            "source_result": None,
            "employee_count": 2,
        }
    )


def _load_legacy_employees(screen: CaromScreen) -> None:
    screen._handle_worker_success(
        {
            "schema": {
                "matricula": "Matricula",
                "nome": "Nome",
                "idade": "Idade",
                "cargo": "Cargo",
            },
            "employees": [_legacy_employee("101", "Ana Martins")],
            "source_result": None,
            "employee_count": 1,
        }
    )


def _preset_item_enabled(screen: CaromScreen, index: int) -> bool:
    item = screen.model_selector.model().item(index)
    assert item is not None
    return bool(item.isEnabled())


def test_carom_screen_get_generation_payload_uses_default_output_dir(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    _load_employees(screen)
    screen._add_employee("matricula:101")
    screen.title_field.setText("Carometro QA 2026")

    received = []
    screen.generate_requested.connect(received.append)
    screen._start_generation()

    assert received[0]["output_dir"] == str(get_default_output_dir())
    assert received[0]["preset_id"] == "big"
    assert received[0]["file_basename"] == normalize_filename("Carometro QA 2026")
    assert received[0]["schema_fields"]["ceo3"] == "CEO3"


def test_carom_screen_switches_legacy_schema_to_mini_and_disables_strict_presets(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    _load_legacy_employees(screen)
    screen._add_employee("matricula:101")

    received = []
    screen.generate_requested.connect(received.append)
    screen._start_generation()

    assert screen.current_preset_id == "mini"
    assert _preset_item_enabled(screen, 0) is True
    assert _preset_item_enabled(screen, 1) is False
    assert _preset_item_enabled(screen, 2) is False
    assert _preset_item_enabled(screen, 3) is False
    assert received[0]["preset_id"] == "mini"


def test_carom_screen_updates_completion_indicator_for_big_capacity(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    _load_employees(screen)
    screen._add_employee("matricula:101")

    assert screen.current_slide_label.text() == "Faltam 7 pessoas para completar o slide atual"


def test_carom_screen_prevents_duplicate_selection(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    _load_employees(screen)
    screen._add_employee("matricula:101")
    screen._add_employee("matricula:101")

    assert len(screen._selected_employees) == 1
    assert "ja esta selecionada" in screen.status_label.text()


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

    assert "Informe um titulo" in screen.status_label.text()
    assert screen.btn_generate.isEnabled() is False


def test_carom_screen_locks_title_for_fixed_templates(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)

    screen.model_selector.setCurrentIndex(2)

    assert screen.current_preset_id == "projeto_trainee"
    assert screen.title_field.isEnabled() is False
    assert screen.title_field.text() == "Carometro Projeto Trainee"


def test_carom_screen_blocks_generation_when_current_template_schema_is_incomplete(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    _load_legacy_employees(screen)
    screen.model_selector.setCurrentIndex(1)
    screen._add_employee("matricula:101")

    assert screen.btn_generate.isEnabled() is False
    assert "colunas ausentes" in screen.schema_status_label.text()


def test_carom_screen_handles_sidebar_collapsed_state(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)

    screen.set_sidebar_collapsed(True)
    assert screen.results_hint.isHidden() is True

    screen.set_sidebar_collapsed(False)
    assert screen.results_hint.isHidden() is False
