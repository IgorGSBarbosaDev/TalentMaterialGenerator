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
    _load_employee_list(
        screen,
        [_employee("101", "Ana Martins"), _employee("102", "Carlos Souza")],
    )


def _load_employee_list(screen: CaromScreen, employees: list[dict[str, str]]) -> None:
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
            "employees": employees,
            "source_result": None,
            "employee_count": len(employees),
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


def _load_talent_review_ready_employees(screen: CaromScreen) -> None:
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
            },
            "employees": [_employee("101", "Ana Martins")],
            "source_result": None,
            "employee_count": 1,
        }
    )


def _preset_item_enabled(screen: CaromScreen, index: int) -> bool:
    item = screen.model_selector.model().item(index)
    assert item is not None
    return bool(item.isEnabled())


def _visible_result_names(screen: CaromScreen) -> list[str]:
    names = []
    for index in range(screen.results_list.count()):
        item = screen.results_list.item(index)
        card = screen.results_list.itemWidget(item)
        assert card is not None
        names.append(card.preview.title_label.text())
    return names


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


def test_carom_screen_allows_talent_review_without_ceo_fields(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    _load_talent_review_ready_employees(screen)
    screen.model_selector.setCurrentIndex(3)
    screen._add_employee("matricula:101")

    assert _preset_item_enabled(screen, 3) is True

    received = []
    screen.generate_requested.connect(received.append)
    screen._start_generation()

    assert received[0]["preset_id"] == "talent_review"


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


def test_carom_screen_search_filters_only_when_requested(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    _load_employees(screen)

    screen.search_input.setText("carl")

    assert len(screen._filtered_employees) == 2

    screen.btn_search.click()

    assert len(screen._filtered_employees) == 1
    assert screen._filtered_employees[0]["nome"] == "Carlos Souza"

    screen.search_input.setText("ana")

    assert screen._filtered_employees[0]["nome"] == "Carlos Souza"

    screen.search_input.returnPressed.emit()

    assert len(screen._filtered_employees) == 1
    assert screen._filtered_employees[0]["nome"] == "Ana Martins"


def test_carom_screen_keeps_full_dataset_but_renders_only_first_page(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    employees = [_employee(str(100 + index), f"Colab {index:03}") for index in range(1, 56)]

    _load_employee_list(screen, employees)

    assert len(screen._loaded_employees) == 55
    assert len(screen._filtered_employees) == 55
    assert screen.results_list.count() == 50
    assert screen.page_indicator.text() == "Pagina 1 de 2"
    assert screen.pagination_count_label.text() == "Mostrando 1-50 de 55 colaborador(es)."


def test_carom_screen_moves_between_pages_without_reloading_dataset(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    employees = [_employee(str(100 + index), f"Colab {index:03}") for index in range(1, 61)]
    _load_employee_list(screen, employees)

    assert _visible_result_names(screen)[0] == "Colab 001"

    screen._go_to_next_page()

    assert len(screen._loaded_employees) == 60
    assert screen._current_page == 2
    assert screen.results_list.count() == 10
    assert _visible_result_names(screen)[0] == "Colab 051"
    assert screen.page_indicator.text() == "Pagina 2 de 2"

    screen._go_to_previous_page()

    assert screen._current_page == 1
    assert screen.results_list.count() == 50
    assert _visible_result_names(screen)[0] == "Colab 001"


def test_carom_screen_searches_full_dataset_beyond_first_visible_page(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    employees = [_employee(str(100 + index), f"Colab {index:03}") for index in range(1, 61)]
    employees[55] = _employee("999", "Zelda Rocha")
    _load_employee_list(screen, employees)

    assert "Zelda Rocha" not in _visible_result_names(screen)

    screen.search_input.setText("zelda")
    screen.btn_search.click()

    assert len(screen._loaded_employees) == 60
    assert len(screen._filtered_employees) == 1
    assert _visible_result_names(screen) == ["Zelda Rocha"]


def test_carom_screen_empty_search_resets_to_full_paginated_dataset(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    employees = [_employee(str(100 + index), f"Colab {index:03}") for index in range(1, 61)]
    employees[55] = _employee("999", "Zelda Rocha")
    _load_employee_list(screen, employees)
    screen.search_input.setText("zelda")
    screen.btn_search.click()

    screen.search_input.clear()
    assert len(screen._filtered_employees) == 1

    screen.btn_search.click()

    assert len(screen._filtered_employees) == 60
    assert screen.results_list.count() == 50
    assert screen._current_page == 1
    assert screen.page_indicator.text() == "Pagina 1 de 2"


def test_carom_screen_paginates_search_results(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    employees = [_employee(str(100 + index), f"Ana {index:03}") for index in range(1, 76)]
    employees.extend(_employee(str(300 + index), f"Bruno {index:03}") for index in range(1, 6))
    _load_employee_list(screen, employees)

    screen.search_input.setText("ana")
    screen.btn_search.click()

    assert len(screen._filtered_employees) == 75
    assert screen.results_list.count() == 50
    assert screen.page_indicator.text() == "Pagina 1 de 2"

    screen._go_to_next_page()

    assert screen.results_list.count() == 25
    assert _visible_result_names(screen)[0] == "Ana 051"
    assert screen.page_indicator.text() == "Pagina 2 de 2"


def test_carom_screen_selected_records_survive_paging_search_and_generation(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    employees = [_employee(str(100 + index), f"Colab {index:03}") for index in range(1, 61)]
    _load_employee_list(screen, employees)
    screen._add_employee("matricula:101")
    screen._go_to_next_page()
    screen._add_employee("matricula:151")

    screen.search_input.setText("sem resultado")
    screen.btn_search.click()

    assert [employee["nome"] for employee in screen._selected_employees] == [
        "Colab 001",
        "Colab 051",
    ]
    assert screen.results_list.count() == 0

    received = []
    screen.generate_requested.connect(received.append)
    screen._start_generation()

    assert [employee["nome"] for employee in received[0]["selected_employees"]] == [
        "Colab 001",
        "Colab 051",
    ]


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
