from __future__ import annotations

from pathlib import Path

from pptx import Presentation

from app.core import generator_carom


def _employee(index: int) -> dict[str, str]:
    return {
        "matricula": str(100 + index),
        "nome": f"Colab {index}",
        "cargo": "Analista",
        "foto": "",
        "area": "Operacao",
        "localizacao": "",
        "unidade_gestao": "",
    }


def test_get_carom_preset_returns_fixed_regular_template() -> None:
    preset = generator_carom.get_carom_preset("regular")

    assert preset["columns"] == 2
    assert preset["rows"] == 5
    assert preset["capacity"] == 10


def test_compute_projected_slide_count_uses_capacity() -> None:
    assert generator_carom.compute_projected_slide_count(0, 10) == 0
    assert generator_carom.compute_projected_slide_count(10, 10) == 1
    assert generator_carom.compute_projected_slide_count(23, 10) == 3


def test_compute_current_slide_status_reports_remaining_people() -> None:
    assert (
        generator_carom.compute_current_slide_status(3, 10)
        == "Faltam 7 pessoas para completar o slide atual"
    )
    assert generator_carom.compute_current_slide_status(10, 10) == "Slide atual completo"
    assert (
        generator_carom.compute_current_slide_status(11, 10)
        == "Faltam 9 pessoas para completar o slide atual"
    )


def test_generate_carom_pptx_creates_single_file(tmp_path: Path) -> None:
    files = generator_carom.generate_carom_pptx(
        [_employee(1), _employee(2)],
        str(tmp_path),
        {"preset_id": "regular", "titulo": "Leadership Board", "file_basename": "Leadership_Board"},
    )

    assert len(files) == 1
    assert Path(files[0]).exists()


def test_generate_carom_pptx_breaks_selection_into_multiple_slides(tmp_path: Path) -> None:
    files = generator_carom.generate_carom_pptx(
        [_employee(index) for index in range(1, 24)],
        str(tmp_path),
        {"preset_id": "regular", "titulo": "Leadership Board", "file_basename": "Leadership_Board"},
    )

    prs = Presentation(files[0])
    assert len(prs.slides) == 3


def test_generate_carom_pptx_uses_title_on_every_slide(tmp_path: Path) -> None:
    files = generator_carom.generate_carom_pptx(
        [_employee(index) for index in range(1, 12)],
        str(tmp_path),
        {"preset_id": "regular", "titulo": "Leadership Board", "file_basename": "Leadership_Board"},
    )

    prs = Presentation(files[0])
    slide_titles = [slide.shapes[1].text for slide in prs.slides]
    assert slide_titles == ["Leadership Board", "Leadership Board"]
