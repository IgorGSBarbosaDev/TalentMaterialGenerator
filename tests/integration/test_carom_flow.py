from __future__ import annotations

from pathlib import Path

from pptx import Presentation

from app.core.generator_carom import CaromConfig, generate_carom_pptx
from app.core.reader import read_spreadsheet

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
SPREADSHEET_FIXTURE = FIXTURES_DIR / "colaboradores_sample.xlsx"


def _normalize_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    return [
        {
            "nome": row.get("nome", ""),
            "cargo": row.get("cargo", ""),
            "area": row.get("area", ""),
            "potencial": row.get("potencial", ""),
            "nota": row.get("nota", ""),
        }
        for row in rows
    ]


def test_full_carom_flow_generates_file(tmp_path: Path) -> None:
    employees = _normalize_rows(read_spreadsheet(str(SPREADSHEET_FIXTURE)))
    config: CaromConfig = {
        "colunas": 5,
        "agrupamento": "area",
        "titulo": "Carometro",
        "show_nota": True,
        "show_potencial": True,
        "show_cargo": True,
        "cores_automaticas": True,
    }

    generated_files = generate_carom_pptx(employees, str(tmp_path), config)

    assert len(generated_files) >= 1
    assert all(Path(path).exists() for path in generated_files)


def test_carom_flow_creates_slides(tmp_path: Path) -> None:
    employees = _normalize_rows(read_spreadsheet(str(SPREADSHEET_FIXTURE)))
    config: CaromConfig = {
        "colunas": 5,
        "agrupamento": None,
        "titulo": "Carometro",
        "show_nota": True,
        "show_potencial": True,
        "show_cargo": True,
        "cores_automaticas": True,
    }

    generated_files = generate_carom_pptx(employees, str(tmp_path), config)
    presentation = Presentation(generated_files[0])

    assert len(presentation.slides) == 1
