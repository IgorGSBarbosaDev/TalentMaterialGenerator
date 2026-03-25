from __future__ import annotations

from pathlib import Path

from pptx import Presentation

from app.core import generator_carom


def _employee(**overrides: object) -> dict[str, object]:
    base = {
        "nome": "Ana Martins",
        "cargo": "Analista",
        "nota": 4.2,
        "potencial": "Alto",
        "area": "Operacao",
    }
    base.update(overrides)
    return base


BASE_CONFIG: generator_carom.CaromConfig = {
    "colunas": 5,
    "agrupamento": "area",
    "titulo": "Carometro",
    "show_nota": True,
    "show_potencial": True,
    "show_cargo": True,
    "cores_automaticas": True,
}


def test_get_score_color_by_threshold() -> None:
    assert generator_carom.get_score_color(4.5) == "#84BD00"
    assert generator_carom.get_score_color(3.5) == "#F59E0B"
    assert generator_carom.get_score_color(2.5) == "#EF4444"


def test_group_employees_sorts_descending_by_score() -> None:
    groups = generator_carom.group_employees(
        [
            _employee(nome="A", area="X", nota=3.2),
            _employee(nome="B", area="X", nota=4.9),
        ],
        "area",
    )

    assert [item["nome"] for item in groups["X"]] == ["B", "A"]


def test_generate_carom_pptx_creates_one_file_per_group(tmp_path: Path) -> None:
    files = generator_carom.generate_carom_pptx(
        [_employee(nome="A", area="X"), _employee(nome="B", area="Y")],
        str(tmp_path),
        BASE_CONFIG,
    )

    assert len(files) == 2
    assert all(Path(path).exists() for path in files)


def test_generate_carom_pptx_breaks_large_group_into_multiple_slides(tmp_path: Path) -> None:
    employees = [_employee(nome=f"Colab {index}", area="X") for index in range(20)]
    files = generator_carom.generate_carom_pptx(employees, str(tmp_path), BASE_CONFIG)

    prs = Presentation(files[0])
    assert len(prs.slides) >= 2
