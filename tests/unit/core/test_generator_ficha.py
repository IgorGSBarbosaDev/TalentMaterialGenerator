from __future__ import annotations

from pathlib import Path

from pptx import Presentation

from app.core import generator_ficha


def _employee(**overrides: str) -> dict[str, str]:
    base = {
        "nome": "Ana Martins",
        "idade": "30",
        "cargo": "Analista",
        "antiguidade": "5 anos",
        "formacao": "Engenharia",
        "trajetoria": "2024-2025 - Coordenadora; 2022-2024 - Analista",
        "resumo_perfil": "Resumo profissional",
        "performance": "2023: 5PROM; 2024: 4AP",
    }
    base.update(overrides)
    return base


def _shape_texts(slide) -> list[str]:
    texts: list[str] = []
    for shape in slide.shapes:
        if getattr(shape, "has_text_frame", False):
            value = shape.text.strip()
            if value:
                texts.append(value)
    return texts


def test_build_slide_creates_slide() -> None:
    prs = generator_ficha.create_presentation()
    slide = generator_ficha.build_slide(prs, _employee())

    assert slide is not None
    assert len(prs.slides) == 1


def test_build_slide_adds_placeholder_shape() -> None:
    prs = generator_ficha.create_presentation()
    slide = generator_ficha.build_slide(prs, _employee())

    assert any(shape.auto_shape_type is not None for shape in slide.shapes if shape.shape_type == 1)


def test_build_slide_omits_empty_optional_sections() -> None:
    prs = generator_ficha.create_presentation()
    slide = generator_ficha.build_slide(
        prs, _employee(formacao="", trajetoria="", performance="", resumo_perfil="")
    )

    texts = [text.upper() for text in _shape_texts(slide)]
    assert "FORMACAO" not in texts
    assert "TRAJETORIA" not in texts
    assert "PERFORMANCE" not in texts


def test_generate_ficha_pptx_creates_individual_files(tmp_path: Path) -> None:
    created = generator_ficha.generate_ficha_pptx(
        [_employee(nome="Ana"), _employee(nome="Pedro")], str(tmp_path)
    )

    assert len(created) == 2
    assert all(Path(path).exists() for path in created)


def test_generate_ficha_pptx_single_deck_creates_single_file(tmp_path: Path) -> None:
    created = generator_ficha.generate_ficha_pptx(
        [_employee(nome="Ana"), _employee(nome="Pedro")],
        str(tmp_path),
        output_mode="single_deck",
    )

    prs = Presentation(created[0])
    assert len(created) == 1
    assert len(prs.slides) == 2
