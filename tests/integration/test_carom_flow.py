from __future__ import annotations

import time
from pathlib import Path
from typing import cast

from pptx import Presentation

from app.core.generator_carom import CaromConfig, generate_carom_pptx
from app.core.reader import read_spreadsheet

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
SPREADSHEET_FIXTURE = FIXTURES_DIR / "colaboradores_sample.xlsx"
PHOTOS_FIXTURE_DIR = FIXTURES_DIR / "fotos"
MAX_TEST_SECONDS = 10.0


CAROM_BASE_CONFIG = {
    "colunas": 5,
    "titulo": "Carometro",
    "show_nota": True,
    "show_potencial": True,
    "show_cargo": True,
    "cores_automaticas": True,
}


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return default


def _load_fixture_employees() -> list[dict[str, str]]:
    employees = read_spreadsheet(str(SPREADSHEET_FIXTURE))
    assert len(employees) == 3
    return employees


def _assert_elapsed_under_limit(start_time: float, end_time: float) -> None:
    elapsed_seconds = end_time - start_time
    assert elapsed_seconds < MAX_TEST_SECONDS


def _extract_names_in_visual_order(slide, expected_names: set[str]) -> list[str]:
    positioned_names: list[tuple[int, int, str]] = []

    for shape in slide.shapes:
        if not getattr(shape, "has_text_frame", False):
            continue

        text = shape.text.strip()
        if text in expected_names:
            positioned_names.append((int(shape.top), int(shape.left), text))

    positioned_names.sort()
    return [name for _, _, name in positioned_names]


def test_full_carom_flow_creates_one_file_per_group(tmp_path: Path) -> None:
    fixture_employees = _load_fixture_employees()
    employees = fixture_employees[:2]
    area_groups = {
        employee.get("area", "").strip()
        for employee in employees
        if employee.get("area", "").strip()
    }
    assert len(area_groups) == 2

    config = cast(CaromConfig, {**CAROM_BASE_CONFIG, "agrupamento": "area"})

    start = time.monotonic()
    generated_files = generate_carom_pptx(
        cast(list[dict[str, object]], employees),
        str(PHOTOS_FIXTURE_DIR),
        str(tmp_path),
        config,
    )
    end = time.monotonic()

    assert len(generated_files) == 2
    assert all(Path(file_path).exists() for file_path in generated_files)
    assert all(Path(file_path).suffix == ".pptx" for file_path in generated_files)
    assert all(
        Path(file_path).parent == (tmp_path / "carometros")
        for file_path in generated_files
    )
    _assert_elapsed_under_limit(start, end)


def test_carom_flow_no_grouping_creates_single_file(tmp_path: Path) -> None:
    employees = _load_fixture_employees()
    config = cast(CaromConfig, {**CAROM_BASE_CONFIG, "agrupamento": None})

    start = time.monotonic()
    generated_files = generate_carom_pptx(
        cast(list[dict[str, object]], employees),
        str(PHOTOS_FIXTURE_DIR),
        str(tmp_path),
        config,
    )
    end = time.monotonic()

    assert len(generated_files) == 1
    assert Path(generated_files[0]).exists()
    assert Path(generated_files[0]).parent == (tmp_path / "carometros")
    _assert_elapsed_under_limit(start, end)


def test_carom_slide_employees_sorted_descending_by_nota(tmp_path: Path) -> None:
    employees = _load_fixture_employees()
    config = cast(CaromConfig, {**CAROM_BASE_CONFIG, "agrupamento": None})

    start = time.monotonic()
    generated_files = generate_carom_pptx(
        cast(list[dict[str, object]], employees),
        str(PHOTOS_FIXTURE_DIR),
        str(tmp_path),
        config,
    )
    end = time.monotonic()

    presentation = Presentation(generated_files[0])
    slide = presentation.slides[0]

    expected_order = [
        employee["nome"]
        for employee in sorted(
            employees,
            key=lambda employee: _safe_float(employee.get("nota", "")),
            reverse=True,
        )
    ]
    expected_names = set(expected_order)

    names_in_visual_order = _extract_names_in_visual_order(slide, expected_names)

    assert names_in_visual_order == expected_order
    _assert_elapsed_under_limit(start, end)
