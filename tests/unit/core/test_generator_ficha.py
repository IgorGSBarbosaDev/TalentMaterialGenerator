from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image
from pptx.presentation import Presentation as PptxPresentation
from pptx.util import Inches

from app.core import generator_ficha


def _employee(**overrides: str) -> dict[str, str]:
    base: dict[str, str] = {
        "nome": "Ana Martins",
        "cargo": "Analista",
        "antiguidade": "5 anos",
        "formacao": "Engenharia",
        "trajetoria": "2020 - Analista",
        "resumo_perfil": "Perfil profissional",
        "performance": "Acima do esperado",
        "foto": "",
    }
    base.update(overrides)
    return base


def _shape_texts(slide) -> list[str]:
    texts: list[str] = []
    for shape in slide.shapes:
        if hasattr(shape, "has_text_frame") and shape.has_text_frame:
            value = shape.text.strip()
            if value:
                texts.append(value)
    return texts


# GROUP A - create_presentation


def test_create_presentation_returns_presentation_object() -> None:
    prs = generator_ficha.create_presentation()

    assert isinstance(prs, PptxPresentation)


def test_create_presentation_slide_width_is_13_271_inches() -> None:
    prs = generator_ficha.create_presentation()

    assert prs.slide_width == Inches(13.271)


def test_create_presentation_slide_height_is_7_5_inches() -> None:
    prs = generator_ficha.create_presentation()

    assert prs.slide_height == Inches(7.500)


# GROUP B - build_slide


def test_build_slide_does_not_raise_with_complete_data(tmp_path: Path) -> None:
    prs = generator_ficha.create_presentation()

    generator_ficha.build_slide(prs, _employee(), str(tmp_path))

    assert len(prs.slides) == 1


def test_build_slide_does_not_raise_with_none_photo_path(tmp_path: Path) -> None:
    prs = generator_ficha.create_presentation()

    generator_ficha.build_slide(prs, _employee(foto=""), None)

    assert len(prs.slides) == 1


def test_build_slide_does_not_raise_with_all_empty_optional_fields(
    tmp_path: Path,
) -> None:
    prs = generator_ficha.create_presentation()

    generator_ficha.build_slide(
        prs,
        _employee(formacao="", trajetoria="", performance="", resumo_perfil=""),
        str(tmp_path),
    )

    assert len(prs.slides) == 1


def test_build_slide_with_empty_formacao_omits_formacao_label(tmp_path: Path) -> None:
    prs = generator_ficha.create_presentation()

    slide = generator_ficha.build_slide(prs, _employee(formacao=""), str(tmp_path))

    assert "FORMACAO" not in [text.upper() for text in _shape_texts(slide)]


def test_build_slide_with_empty_trajetoria_omits_trajetoria_label(
    tmp_path: Path,
) -> None:
    prs = generator_ficha.create_presentation()

    slide = generator_ficha.build_slide(prs, _employee(trajetoria=""), str(tmp_path))

    assert all("TRAJET" not in text.upper() for text in _shape_texts(slide))


def test_build_slide_with_empty_performance_omits_performance_label(
    tmp_path: Path,
) -> None:
    prs = generator_ficha.create_presentation()

    slide = generator_ficha.build_slide(prs, _employee(performance=""), str(tmp_path))

    assert "PERFORMANCE" not in _shape_texts(slide)


# GROUP C - generate_ficha_pptx


def test_generate_ficha_pptx_creates_one_pptx_per_employee(tmp_path: Path) -> None:
    employees = [_employee(nome="Ana Martins"), _employee(nome="Pedro Souza")]

    created = generator_ficha.generate_ficha_pptx(
        employees, str(tmp_path), str(tmp_path)
    )

    assert len(created) == 2
    assert all(Path(path).exists() for path in created)


def test_generate_ficha_pptx_output_filename_has_no_accents(tmp_path: Path) -> None:
    employees = [_employee(nome="Jo\u00e3o B\u00e1rbara")]

    created = generator_ficha.generate_ficha_pptx(
        employees, str(tmp_path), str(tmp_path)
    )

    assert Path(created[0]).name == "Joao_Barbara.pptx"


def test_generate_ficha_pptx_output_filename_replaces_spaces_with_underscore(
    tmp_path: Path,
) -> None:
    employees = [_employee(nome="Ana Maria")]

    created = generator_ficha.generate_ficha_pptx(
        employees, str(tmp_path), str(tmp_path)
    )

    assert Path(created[0]).name == "Ana_Maria.pptx"


def test_generate_ficha_pptx_creates_fichas_subfolder(tmp_path: Path) -> None:
    employees = [_employee(nome="Ana")]

    generator_ficha.generate_ficha_pptx(employees, str(tmp_path), str(tmp_path))

    assert (tmp_path / "fichas").exists()


def test_generate_ficha_pptx_returns_list_of_created_file_paths(tmp_path: Path) -> None:
    employees = [_employee(nome="Ana"), _employee(nome="Pedro")]

    created = generator_ficha.generate_ficha_pptx(
        employees, str(tmp_path), str(tmp_path)
    )

    assert isinstance(created, list)
    assert all(str(tmp_path / "fichas") in path for path in created)


def test_generate_ficha_pptx_calls_callback_for_each_employee(tmp_path: Path) -> None:
    employees = [_employee(nome="Ana"), _employee(nome="Pedro")]
    received: list[dict] = []

    def callback(message: dict) -> None:
        received.append(message)

    generator_ficha.generate_ficha_pptx(
        employees, str(tmp_path), str(tmp_path), callback
    )

    progress_items = [item for item in received if item.get("type") == "progress"]
    log_items = [item for item in received if item.get("type") == "log"]

    assert len(progress_items) == 2
    assert progress_items[0] == {
        "type": "progress",
        "current": 1,
        "total": 2,
        "name": "Ana",
    }
    assert progress_items[1] == {
        "type": "progress",
        "current": 2,
        "total": 2,
        "name": "Pedro",
    }
    assert log_items[0]["message"] == "\u2713 Gerando slide: Ana"
    assert log_items[0]["level"] == "success"


def test_generate_ficha_pptx_continues_on_single_employee_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    employees = [_employee(nome="Ana"), _employee(nome="Pedro")]

    original_build_slide = generator_ficha.build_slide

    def flaky_build_slide(prs, employee: dict[str, str], photos_dir: str | None):
        if employee.get("nome") == "Ana":
            raise RuntimeError("forced error")
        return original_build_slide(prs, employee, photos_dir)

    monkeypatch.setattr(generator_ficha, "build_slide", flaky_build_slide)

    received: list[dict] = []

    generator_ficha.generate_ficha_pptx(
        employees,
        str(tmp_path),
        str(tmp_path),
        callback=received.append,
    )

    created = list((tmp_path / "fichas").glob("*.pptx"))
    assert len(created) == 1
    assert created[0].name == "Pedro.pptx"
    assert any(
        item.get("level") == "error" for item in received if item.get("type") == "log"
    )


# GROUP D - photo resolution


def test_photo_lookup_uses_foto_field_first(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()
    foto_path = photos_dir / "custom_name.png"
    Image.new("RGB", (30, 30), (255, 0, 0)).save(foto_path)

    called_paths: list[str] = []

    original_make_circular = generator_ficha.make_circular_image

    def tracking_make_circular(path: str):
        called_paths.append(path)
        return original_make_circular(path)

    monkeypatch.setattr(generator_ficha, "make_circular_image", tracking_make_circular)

    prs = generator_ficha.create_presentation()
    generator_ficha.build_slide(prs, _employee(foto="custom_name.png"), str(photos_dir))

    assert called_paths
    assert Path(called_paths[0]).name == "custom_name.png"


def test_photo_lookup_falls_back_to_normalized_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()
    expected = photos_dir / "Ana_Martins.jpg"
    Image.new("RGB", (30, 30), (255, 0, 0)).save(expected)

    called_paths: list[str] = []

    original_make_circular = generator_ficha.make_circular_image

    def tracking_make_circular(path: str):
        called_paths.append(path)
        return original_make_circular(path)

    monkeypatch.setattr(generator_ficha, "make_circular_image", tracking_make_circular)

    prs = generator_ficha.create_presentation()
    generator_ficha.build_slide(prs, _employee(foto=""), str(photos_dir))

    assert any(Path(path).name == "Ana_Martins.jpg" for path in called_paths)


def test_photo_lookup_generates_avatar_when_no_photo_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generated_for: list[str] = []

    original_generate_avatar = generator_ficha.generate_avatar

    def tracking_generate_avatar(name: str):
        generated_for.append(name)
        return original_generate_avatar(name)

    monkeypatch.setattr(generator_ficha, "generate_avatar", tracking_generate_avatar)

    prs = generator_ficha.create_presentation()
    generator_ficha.build_slide(prs, _employee(nome="Sem Foto"), str(tmp_path))

    assert generated_for == ["Sem Foto"]


def test_photo_lookup_uses_absolute_foto_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()
    absolute_photo = tmp_path / "absolute_photo.png"
    Image.new("RGB", (30, 30), (255, 0, 0)).save(absolute_photo)

    called_paths: list[str] = []

    original_make_circular = generator_ficha.make_circular_image

    def tracking_make_circular(path: str):
        called_paths.append(path)
        return original_make_circular(path)

    monkeypatch.setattr(generator_ficha, "make_circular_image", tracking_make_circular)

    prs = generator_ficha.create_presentation()
    generator_ficha.build_slide(
        prs, _employee(foto=str(absolute_photo)), str(photos_dir)
    )

    assert called_paths
    assert Path(called_paths[0]) == absolute_photo


def test_photo_lookup_with_missing_photos_dir_generates_avatar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generated_for: list[str] = []

    original_generate_avatar = generator_ficha.generate_avatar

    def tracking_generate_avatar(name: str):
        generated_for.append(name)
        return original_generate_avatar(name)

    monkeypatch.setattr(generator_ficha, "generate_avatar", tracking_generate_avatar)

    non_existing_photos_dir = tmp_path / "does_not_exist"
    prs = generator_ficha.create_presentation()
    generator_ficha.build_slide(
        prs, _employee(nome="Sem Diretorio"), str(non_existing_photos_dir)
    )

    assert generated_for == ["Sem Diretorio"]


def test_generate_ficha_pptx_does_not_raise_when_temp_unlink_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    employees = [_employee(nome="Ana")]

    original_unlink = generator_ficha.os.unlink

    def flaky_unlink(path: str) -> None:
        if str(path).lower().endswith(".png"):
            raise OSError("simulated unlink failure")
        original_unlink(path)

    monkeypatch.setattr(generator_ficha.os, "unlink", flaky_unlink)

    created = generator_ficha.generate_ficha_pptx(
        employees, str(tmp_path), str(tmp_path)
    )

    assert len(created) == 1
    assert Path(created[0]).exists()
