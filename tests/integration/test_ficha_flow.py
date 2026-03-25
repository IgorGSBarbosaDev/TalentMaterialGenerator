from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

from app.core.generator_ficha import generate_ficha_pptx
from app.core.reader import normalize_filename, read_spreadsheet

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
SPREADSHEET_FIXTURE = FIXTURES_DIR / "colaboradores_sample.xlsx"


def _normalize_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "nome": row.get("nome", ""),
            "idade": row.get("idade", ""),
            "cargo": row.get("cargo", ""),
            "antiguidade": row.get("antiguidade", ""),
            "formacao": row.get("formacao", ""),
            "resumo_perfil": row.get("resumo_perfil", ""),
            "trajetoria": row.get("trajetoria", ""),
            "performance": row.get("performance", ""),
        }
        for row in rows
    ]


def test_full_ficha_flow_generates_pptx_files(tmp_path: Path) -> None:
    employees = _normalize_rows(read_spreadsheet(str(SPREADSHEET_FIXTURE)))

    generated_files = generate_ficha_pptx(employees, str(tmp_path))

    assert len(generated_files) == len(employees)
    assert all(Path(path).exists() for path in generated_files)


def test_generated_slide_has_wide_dimensions(tmp_path: Path) -> None:
    employees = _normalize_rows(read_spreadsheet(str(SPREADSHEET_FIXTURE)))
    generated_files = generate_ficha_pptx([employees[0]], str(tmp_path))

    presentation = Presentation(generated_files[0])
    assert presentation.slide_width == Inches(13.271)
    assert presentation.slide_height == Inches(7.5)


def test_output_filename_is_normalized(tmp_path: Path) -> None:
    employee = {
        "nome": "João Bárbara",
        "idade": "",
        "cargo": "Analista",
        "antiguidade": "",
        "formacao": "",
        "resumo_perfil": "",
        "trajetoria": "",
        "performance": "",
    }
    generated_files = generate_ficha_pptx([employee], str(tmp_path))

    assert Path(generated_files[0]).stem == normalize_filename(employee["nome"])
