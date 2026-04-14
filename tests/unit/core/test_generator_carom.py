from __future__ import annotations

from pathlib import Path

from pptx import Presentation

from app.core import generator_carom


def _employee(index: int) -> dict[str, str]:
    return {
        "matricula": str(100 + index),
        "nome": f"Colab {index}",
        "idade": str(20 + index),
        "cargo": "Analista",
        "formacao": "Engenharia",
        "resumo_perfil": "Resumo",
        "trajetoria": "Trajetoria",
        "foto": "",
        "area": "Operacao",
        "localizacao": "",
        "unidade_gestao": "",
        "nota_2025": "4 / AP",
        "avaliacao_2025": "4 / AP",
        "score_2025": "4",
        "potencial_2025": "AP",
        "ceo3": f"CEO3 {index}",
        "ceo4": f"CEO4 {index}",
    }


def _all_slide_text(slide) -> str:
    values: list[str] = []
    for shape in slide.shapes:
        if hasattr(shape, "text"):
            values.append(shape.text)
    return "\n".join(values)


def test_get_carom_preset_maps_legacy_regular_to_big_template() -> None:
    preset = generator_carom.get_carom_preset("regular")

    assert preset.id == "big"
    assert preset.capacity == 8
    assert preset.template_path.name == "Carometro-big.pptx"


def test_compute_projected_slide_count_uses_capacity() -> None:
    assert generator_carom.compute_projected_slide_count(0, 8) == 0
    assert generator_carom.compute_projected_slide_count(8, 8) == 1
    assert generator_carom.compute_projected_slide_count(23, 8) == 3


def test_compute_current_slide_status_reports_remaining_people() -> None:
    assert (
        generator_carom.compute_current_slide_status(3, 8)
        == "Faltam 5 pessoas para completar o slide atual"
    )
    assert generator_carom.compute_current_slide_status(8, 8) == "Slide atual completo"
    assert (
        generator_carom.compute_current_slide_status(9, 8)
        == "Faltam 7 pessoas para completar o slide atual"
    )


def test_generate_carom_pptx_creates_single_file(tmp_path: Path) -> None:
    files = generator_carom.generate_carom_pptx(
        [_employee(1), _employee(2)],
        str(tmp_path),
        {"preset_id": "big", "titulo": "Leadership Board", "file_basename": "Leadership_Board"},
    )

    assert len(files) == 1
    assert Path(files[0]).exists()


def test_generate_carom_pptx_breaks_big_selection_into_multiple_slides(tmp_path: Path) -> None:
    files = generator_carom.generate_carom_pptx(
        [_employee(index) for index in range(1, 10)],
        str(tmp_path),
        {"preset_id": "big", "titulo": "Leadership Board", "file_basename": "Leadership_Board"},
    )

    prs = Presentation(files[0])
    assert len(prs.slides) == 2


def test_generate_carom_pptx_uses_title_on_every_big_slide(tmp_path: Path) -> None:
    files = generator_carom.generate_carom_pptx(
        [_employee(index) for index in range(1, 12)],
        str(tmp_path),
        {"preset_id": "regular", "titulo": "Leadership Board", "file_basename": "Leadership_Board"},
    )

    prs = Presentation(files[0])
    slide_titles = [slide.shapes[17].text for slide in prs.slides]
    assert slide_titles == ["Leadership Board", "Leadership Board"]


def test_generate_carom_pptx_clears_unused_big_slots_without_sample_text(tmp_path: Path) -> None:
    files = generator_carom.generate_carom_pptx(
        [_employee(1)],
        str(tmp_path),
        {"preset_id": "big", "titulo": "Leadership Board", "file_basename": "Leadership_Board"},
    )

    prs = Presentation(files[0])
    text = _all_slide_text(prs.slides[0])

    assert "Ana Carolina Alves Melo Gouveia" not in text
    assert "Fernando Augusto Rodrigues Machado" not in text
    assert "Colab 1" in text


def test_generate_carom_pptx_uses_literal_body_text_for_projeto_trainee(tmp_path: Path) -> None:
    files = generator_carom.generate_carom_pptx(
        [_employee(1), _employee(2)],
        str(tmp_path),
        {"preset_id": "projeto_trainee", "titulo": "Ignored", "file_basename": "Projeto_Trainee"},
    )

    prs = Presentation(files[0])
    slide = prs.slides[0]

    assert slide.shapes[9].text.splitlines()[0] == "insira projeto trainee aqui"
    assert slide.shapes[13].text.splitlines()[0] == "insira projeto trainee aqui"
    assert slide.shapes[3].text == "CEO3 - Programa GT & GP"


def test_generate_carom_pptx_maps_talent_review_ceo_fields(tmp_path: Path) -> None:
    files = generator_carom.generate_carom_pptx(
        [_employee(1)],
        str(tmp_path),
        {"preset_id": "talent_review", "titulo": "Ignored", "file_basename": "Talent_Review"},
    )

    prs = Presentation(files[0])
    text_box = prs.slides[0].shapes[4]
    paragraphs = [paragraph.text for paragraph in text_box.text_frame.paragraphs]

    assert paragraphs[0] == "Colab 1 | 21 - 4 / AP"
    assert paragraphs[1] == "Analista"
    assert paragraphs[2] == "Sucessor Imediato"
    assert paragraphs[3] == "CEO3 1"
    assert paragraphs[4] == "Em desenvolvimento"
    assert paragraphs[5] == "CEO4 1"


def test_generate_carom_pptx_paginates_full_talent_review_capacity(tmp_path: Path) -> None:
    files = generator_carom.generate_carom_pptx(
        [_employee(index) for index in range(1, 14)],
        str(tmp_path),
        {"preset_id": "talent_review", "titulo": "Ignored", "file_basename": "Talent_Review"},
    )

    prs = Presentation(files[0])
    assert len(prs.slides) == 2
