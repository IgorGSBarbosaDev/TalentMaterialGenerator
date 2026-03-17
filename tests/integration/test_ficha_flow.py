from __future__ import annotations

import time
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

from app.core.generator_ficha import generate_ficha_pptx
from app.core.reader import normalize_filename, read_spreadsheet

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
SPREADSHEET_FIXTURE = FIXTURES_DIR / "colaboradores_sample.xlsx"
PHOTOS_FIXTURE_DIR = FIXTURES_DIR / "fotos"
MAX_TEST_SECONDS = 10.0


def _load_fixture_employees() -> list[dict[str, str]]:
    employees = read_spreadsheet(str(SPREADSHEET_FIXTURE))
    assert len(employees) == 3
    return employees


def _assert_elapsed_under_limit(start_time: float, end_time: float) -> None:
    elapsed_seconds = end_time - start_time
    assert elapsed_seconds < MAX_TEST_SECONDS


def test_full_flow_reads_spreadsheet_and_generates_pptx_files(tmp_path: Path) -> None:
    employees = _load_fixture_employees()

    start = time.monotonic()
    generated_files = generate_ficha_pptx(
        employees,
        str(PHOTOS_FIXTURE_DIR),
        str(tmp_path),
    )
    end = time.monotonic()

    assert len(generated_files) == len(employees)
    assert all(Path(file_path).exists() for file_path in generated_files)
    assert all(Path(file_path).suffix == ".pptx" for file_path in generated_files)
    assert all(Path(file_path).parent == (tmp_path / "fichas") for file_path in generated_files)
    _assert_elapsed_under_limit(start, end)


def test_generated_pptx_slide_width_is_13_271_inches(tmp_path: Path) -> None:
    employee = _load_fixture_employees()[0]

    start = time.monotonic()
    generated_files = generate_ficha_pptx(
        [employee],
        str(PHOTOS_FIXTURE_DIR),
        str(tmp_path),
    )
    end = time.monotonic()

    presentation = Presentation(generated_files[0])
    assert presentation.slide_width == Inches(13.271)
    _assert_elapsed_under_limit(start, end)


def test_generated_pptx_slide_height_is_7_5_inches(tmp_path: Path) -> None:
    employee = _load_fixture_employees()[0]

    start = time.monotonic()
    generated_files = generate_ficha_pptx(
        [employee],
        str(PHOTOS_FIXTURE_DIR),
        str(tmp_path),
    )
    end = time.monotonic()

    presentation = Presentation(generated_files[0])
    assert presentation.slide_height == Inches(7.5)
    _assert_elapsed_under_limit(start, end)


def test_output_filenames_have_no_accents_or_spaces(tmp_path: Path) -> None:
    employees = _load_fixture_employees()

    start = time.monotonic()
    generated_files = generate_ficha_pptx(
        employees,
        str(PHOTOS_FIXTURE_DIR),
        str(tmp_path),
    )
    end = time.monotonic()

    stems = [Path(file_path).stem for file_path in generated_files]

    for employee, stem in zip(employees, stems):
        expected_stem = normalize_filename(employee.get("nome", ""))
        assert stem == expected_stem
        assert " " not in stem
        assert stem.isascii()

    _assert_elapsed_under_limit(start, end)


def test_generation_continues_when_one_employee_has_no_photo(tmp_path: Path) -> None:
    employees = _load_fixture_employees()
    employees[0] = {**employees[0], "foto": "nonexistent.jpg"}

    start = time.monotonic()
    generated_files = generate_ficha_pptx(
        employees,
        str(PHOTOS_FIXTURE_DIR),
        str(tmp_path),
    )
    end = time.monotonic()

    assert len(generated_files) == len(employees)

    missing_photo_employee_name = employees[0]["nome"]
    expected_stem = normalize_filename(missing_photo_employee_name)
    expected_file = tmp_path / "fichas" / f"{expected_stem}.pptx"
    assert expected_file.exists()

    _assert_elapsed_under_limit(start, end)
