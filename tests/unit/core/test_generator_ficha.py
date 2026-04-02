from __future__ import annotations

from pathlib import Path

from app.core import generator_ficha
from app.core.reader import FichaEmployee, normalize_filename


def _employee(**overrides: str) -> FichaEmployee:
    base: FichaEmployee = {
        "matricula": "123",
        "nome": "Ana Martins",
        "idade": "30",
        "cargo": "Analista",
        "antiguidade": "5 anos",
        "formacao": "Engenharia",
        "trajetoria": "2024-2025 - Coordenadora; 2022-2024 - Analista",
        "resumo_perfil": "Resumo profissional",
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


def test_build_slide_omits_empty_optional_sections() -> None:
    prs = generator_ficha.create_presentation()
    slide = generator_ficha.build_slide(
        prs,
        _employee(formacao="", trajetoria="", resumo_perfil=""),
    )

    texts = [text.upper() for text in _shape_texts(slide)]
    assert "FORMACAO" not in texts
    assert "TRAJETORIA" not in texts
    assert "PERFORMANCE" not in texts


def test_generate_ficha_pptx_creates_single_file(tmp_path: Path) -> None:
    created = generator_ficha.generate_ficha_pptx(_employee(nome="Ana"), str(tmp_path))

    assert Path(created).exists()


def test_generate_ficha_pptx_uses_normalized_filename(tmp_path: Path) -> None:
    employee = _employee(nome="João Bárbara")

    created = generator_ficha.generate_ficha_pptx(employee, str(tmp_path))

    assert Path(created).stem == normalize_filename(employee["nome"])


def test_generate_ficha_pptx_reports_single_progress_event(tmp_path: Path) -> None:
    messages: list[dict] = []

    created = generator_ficha.generate_ficha_pptx(
        _employee(nome="Ana"),
        str(tmp_path),
        callback=messages.append,
    )

    assert Path(created).exists()
    assert any(
        message.get("type") == "progress"
        and message.get("current") == 1
        and message.get("total") == 1
        for message in messages
    )
