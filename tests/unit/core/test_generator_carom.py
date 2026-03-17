from __future__ import annotations

from pathlib import Path

import pytest
from pptx import Presentation

from app.core import generator_carom


def _employee(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "nome": "Ana Martins",
        "cargo": "Analista",
        "nota": 4.2,
        "potencial": "Alto",
        "area": "Operacao",
        "foto": "",
    }
    base.update(overrides)
    return base


def _shape_texts(slide) -> list[str]:
    texts: list[str] = []
    for shape in slide.shapes:
        if hasattr(shape, "has_text_frame") and shape.has_text_frame:
            value = shape.text.strip()
            if value:
                texts.append(value)
    return texts


def _find_shape_left_by_exact_text(slide, text: str) -> int:
    for shape in slide.shapes:
        if hasattr(shape, "has_text_frame") and shape.has_text_frame:
            if shape.text.strip() == text:
                return shape.left
    raise AssertionError(f"Text not found in slide: {text}")


# GROUP A - color logic


@pytest.mark.parametrize("score", [4.0, 4.5, 5.0])
def test_get_score_color_returns_green_for_4_or_above(score: float) -> None:
    assert generator_carom.get_score_color(score) == "#84BD00"


@pytest.mark.parametrize("score", [3.0, 3.5, 3.9])
def test_get_score_color_returns_amber_for_3_to_39(score: float) -> None:
    assert generator_carom.get_score_color(score) == "#F59E0B"


@pytest.mark.parametrize("score", [0.0, 1.5, 2.9])
def test_get_score_color_returns_red_for_below_3(score: float) -> None:
    assert generator_carom.get_score_color(score) == "#EF4444"


def test_get_potential_color_alto_returns_green() -> None:
    assert generator_carom.get_potential_color("Alto") == "#84BD00"


@pytest.mark.parametrize("potential", ["Médio", "medio", "MÉDIO"])
def test_get_potential_color_medio_returns_amber(potential: str) -> None:
    assert generator_carom.get_potential_color(potential) == "#F59E0B"


def test_get_potential_color_baixo_returns_red() -> None:
    assert generator_carom.get_potential_color("Baixo") == "#EF4444"


def test_get_potential_color_unknown_returns_gray() -> None:
    assert generator_carom.get_potential_color("Sem mapeamento") == "#9CA3AF"


# GROUP B - group_employees


def test_group_by_area_creates_correct_groups() -> None:
    employees = [
        _employee(nome="Ana", area="A"),
        _employee(nome="Pedro", area="B"),
        _employee(nome="Maria", area="A"),
    ]

    groups = generator_carom.group_employees(employees, "area")

    assert set(groups.keys()) == {"A", "B"}
    assert [item["nome"] for item in groups["A"]] == ["Ana", "Maria"]
    assert [item["nome"] for item in groups["B"]] == ["Pedro"]


def test_group_by_none_returns_single_group_with_all_employees() -> None:
    employees = [_employee(nome="Ana"), _employee(nome="Pedro")]

    groups = generator_carom.group_employees(employees, None)

    assert list(groups.keys()) == ["Todos"]
    assert len(groups["Todos"]) == 2


def test_group_employees_each_group_sorted_descending_by_nota() -> None:
    employees = [
        _employee(nome="Ana", area="A", nota=3.2),
        _employee(nome="Pedro", area="A", nota=4.8),
        _employee(nome="Maria", area="A", nota=4.0),
    ]

    groups = generator_carom.group_employees(employees, "area")

    assert [item["nome"] for item in groups["A"]] == ["Pedro", "Maria", "Ana"]


def test_group_employees_empty_list_returns_empty_dict() -> None:
    assert generator_carom.group_employees([], "area") == {}


def test_group_by_area_missing_group_value_goes_to_sem_grupo_and_invalid_nota() -> None:
    employees = [
        _employee(nome="Ana", area=None, nota="invalida"),
        _employee(nome="Pedro", area="", nota=3.2),
    ]

    groups = generator_carom.group_employees(employees, "area")

    assert "Sem Grupo" in groups
    assert [item["nome"] for item in groups["Sem Grupo"]] == ["Pedro", "Ana"]


# GROUP C - build_card


def test_build_card_does_not_raise_with_full_data(tmp_path: Path) -> None:
    prs = generator_carom.create_presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    generator_carom.build_card(
        slide,
        _employee(),
        photos_dir=str(tmp_path),
        card_x=0.3,
        card_y=1.1,
        card_width=2.3,
        card_height=1.6,
        config={
            "colunas": 5,
            "agrupamento": "area",
            "titulo": "Carometro",
            "show_nota": True,
            "show_potencial": True,
            "show_cargo": True,
            "cores_automaticas": True,
        },
    )

    assert len(slide.shapes) > 0


def test_build_card_does_not_raise_with_none_photo(tmp_path: Path) -> None:
    prs = generator_carom.create_presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    generator_carom.build_card(
        slide,
        _employee(foto=None),
        photos_dir=str(tmp_path),
        card_x=0.3,
        card_y=1.1,
        card_width=2.3,
        card_height=1.6,
        config={
            "colunas": 5,
            "agrupamento": "area",
            "titulo": "Carometro",
            "show_nota": True,
            "show_potencial": True,
            "show_cargo": True,
            "cores_automaticas": True,
        },
    )

    assert len(slide.shapes) > 0


def test_build_card_show_nota_false_does_not_add_score_text(tmp_path: Path) -> None:
    prs = generator_carom.create_presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    generator_carom.build_card(
        slide,
        _employee(nota=4.7),
        photos_dir=str(tmp_path),
        card_x=0.3,
        card_y=1.1,
        card_width=2.3,
        card_height=1.6,
        config={
            "colunas": 5,
            "agrupamento": "area",
            "titulo": "Carometro",
            "show_nota": False,
            "show_potencial": True,
            "show_cargo": True,
            "cores_automaticas": True,
        },
    )

    assert "4.7" not in _shape_texts(slide)


def test_build_card_show_potencial_false_does_not_add_badge(tmp_path: Path) -> None:
    prs = generator_carom.create_presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    generator_carom.build_card(
        slide,
        _employee(potencial="Alto"),
        photos_dir=str(tmp_path),
        card_x=0.3,
        card_y=1.1,
        card_width=2.3,
        card_height=1.6,
        config={
            "colunas": 5,
            "agrupamento": "area",
            "titulo": "Carometro",
            "show_nota": True,
            "show_potencial": False,
            "show_cargo": True,
            "cores_automaticas": True,
        },
    )

    assert "Alto" not in _shape_texts(slide)


def test_build_card_cores_automaticas_false_uses_neutral_text_colors(
    tmp_path: Path,
) -> None:
    prs = generator_carom.create_presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    generator_carom.build_card(
        slide,
        _employee(nota=4.7, potencial="Alto"),
        photos_dir=str(tmp_path),
        card_x=0.3,
        card_y=1.1,
        card_width=2.3,
        card_height=1.6,
        config={
            "colunas": 5,
            "agrupamento": "area",
            "titulo": "Carometro",
            "show_nota": True,
            "show_potencial": True,
            "show_cargo": True,
            "cores_automaticas": False,
        },
    )

    texts = _shape_texts(slide)
    assert "4.7" in texts
    assert "Alto" in texts


# GROUP D - generate_carom_pptx


def test_generate_carom_pptx_creates_one_slide_per_group(tmp_path: Path) -> None:
    employees = [
        _employee(nome="Ana", area="A"),
        _employee(nome="Pedro", area="B"),
        _employee(nome="Maria", area="A"),
    ]

    files = generator_carom.generate_carom_pptx(
        employees,
        photos_dir=str(tmp_path),
        output_dir=str(tmp_path),
        config={
            "colunas": 5,
            "agrupamento": "area",
            "titulo": "Carometro",
            "show_nota": True,
            "show_potencial": True,
            "show_cargo": True,
            "cores_automaticas": True,
        },
    )

    assert len(files) == 2
    for path in files:
        prs = Presentation(path)
        assert len(prs.slides) == 1


def test_generate_carom_pptx_no_grouping_creates_single_pptx(tmp_path: Path) -> None:
    employees = [_employee(nome="Ana"), _employee(nome="Pedro")]

    files = generator_carom.generate_carom_pptx(
        employees,
        photos_dir=str(tmp_path),
        output_dir=str(tmp_path),
        config={
            "colunas": 5,
            "agrupamento": None,
            "titulo": "Carometro",
            "show_nota": True,
            "show_potencial": True,
            "show_cargo": True,
            "cores_automaticas": True,
        },
    )

    assert len(files) == 1
    assert Path(files[0]).exists()


def test_generate_carom_pptx_3_columns_different_from_5_columns(tmp_path: Path) -> None:
    employees = [
        _employee(nome="Ana", area="A"),
        _employee(nome="Pedro", area="A"),
    ]

    files_3 = generator_carom.generate_carom_pptx(
        employees,
        photos_dir=str(tmp_path),
        output_dir=str(tmp_path / "c3"),
        config={
            "colunas": 3,
            "agrupamento": None,
            "titulo": "Carometro",
            "show_nota": True,
            "show_potencial": True,
            "show_cargo": True,
            "cores_automaticas": True,
        },
    )
    files_5 = generator_carom.generate_carom_pptx(
        employees,
        photos_dir=str(tmp_path),
        output_dir=str(tmp_path / "c5"),
        config={
            "colunas": 5,
            "agrupamento": None,
            "titulo": "Carometro",
            "show_nota": True,
            "show_potencial": True,
            "show_cargo": True,
            "cores_automaticas": True,
        },
    )

    prs_3 = Presentation(files_3[0])
    prs_5 = Presentation(files_5[0])

    slide_3 = prs_3.slides[0]
    slide_5 = prs_5.slides[0]

    x_3 = _find_shape_left_by_exact_text(slide_3, "Pedro")
    x_5 = _find_shape_left_by_exact_text(slide_5, "Pedro")

    assert x_3 != x_5


def test_generate_carom_pptx_creates_carometros_subfolder(tmp_path: Path) -> None:
    employees = [_employee(nome="Ana")]

    generator_carom.generate_carom_pptx(
        employees,
        photos_dir=str(tmp_path),
        output_dir=str(tmp_path),
        config={
            "colunas": 5,
            "agrupamento": None,
            "titulo": "Carometro",
            "show_nota": True,
            "show_potencial": True,
            "show_cargo": True,
            "cores_automaticas": True,
        },
    )

    assert (tmp_path / "carometros").exists()


def test_generate_carom_pptx_calls_callback_for_each_group(tmp_path: Path) -> None:
    employees = [
        _employee(nome="Ana", area="A"),
        _employee(nome="Pedro", area="B"),
    ]
    received: list[dict] = []

    generator_carom.generate_carom_pptx(
        employees,
        photos_dir=str(tmp_path),
        output_dir=str(tmp_path),
        config={
            "colunas": 5,
            "agrupamento": "area",
            "titulo": "Carometro",
            "show_nota": True,
            "show_potencial": True,
            "show_cargo": True,
            "cores_automaticas": True,
        },
        callback=received.append,
    )

    progress_items = [item for item in received if item.get("type") == "progress"]

    assert len(progress_items) == 2
    assert [item["name"] for item in progress_items] == ["A", "B"]


def test_generate_carom_pptx_empty_employees_returns_empty_list(tmp_path: Path) -> None:
    created = generator_carom.generate_carom_pptx(
        [],
        photos_dir=str(tmp_path),
        output_dir=str(tmp_path),
        config={
            "colunas": 5,
            "agrupamento": None,
            "titulo": "Carometro",
            "show_nota": True,
            "show_potencial": True,
            "show_cargo": True,
            "cores_automaticas": True,
        },
    )

    assert created == []
