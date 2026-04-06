from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from pptx import Presentation

from app.core.generator_carom import CaromConfig, generate_carom_pptx
from app.core.reader import load_standardized_carom_rows, read_spreadsheet


def _build_standardized_carom_spreadsheet(path: Path, total_rows: int) -> Path:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.append(["Matricula", "Nome", "Cargo", "Area"])
    for index in range(1, total_rows + 1):
        sheet.append([str(100 + index), f"Colab {index}", "Analista", "Operacao"])
    workbook.save(path)
    return path


def test_full_carom_flow_generates_single_file(tmp_path: Path) -> None:
    spreadsheet = _build_standardized_carom_spreadsheet(tmp_path / "carom.xlsx", 3)
    employees = load_standardized_carom_rows(read_spreadsheet(str(spreadsheet)))
    config: CaromConfig = {
        "preset_id": "regular",
        "titulo": "Carometro",
        "file_basename": "Carometro",
    }

    generated_files = generate_carom_pptx(employees, str(tmp_path), config)

    assert len(generated_files) == 1
    assert Path(generated_files[0]).exists()


def test_carom_flow_creates_expected_slide_count(tmp_path: Path) -> None:
    spreadsheet = _build_standardized_carom_spreadsheet(tmp_path / "carom-large.xlsx", 9)
    employees = load_standardized_carom_rows(read_spreadsheet(str(spreadsheet)))
    config: CaromConfig = {
        "preset_id": "large",
        "titulo": "Carometro",
        "file_basename": "Carometro",
    }

    generated_files = generate_carom_pptx(employees, str(tmp_path), config)
    presentation = Presentation(generated_files[0])

    assert len(presentation.slides) == 2
