from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Final

from PIL import Image
from pptx import Presentation as PresentationFactory
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.presentation import Presentation
from pptx.slide import Slide
from pptx.util import Inches, Pt

from app.core.image_utils import generate_avatar, make_circular_image, save_temp_png
from app.core.reader import normalize_filename

SLIDE_WIDTH: Final = Inches(13.271)
SLIDE_HEIGHT: Final = Inches(7.500)

VERDE_TITULO: Final = "#92D050"
CINZA_TRAJETORIA: Final = "#666666"

CINZA_GRANDE: Final = "#D9D9D9"
CINZA_MENOR: Final = "#ECECEC"
BRANCO: Final = "#FFFFFF"
PRETO: Final = "#000000"

PHOTO_LEFT: Final = Inches(0.385)
PHOTO_TOP: Final = Inches(1.000)
PHOTO_WIDTH: Final = Inches(1.382)
PHOTO_HEIGHT: Final = Inches(1.344)


def create_presentation() -> Presentation:
    """Create a ficha presentation with required WIDE dimensions."""
    prs = PresentationFactory()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT
    return prs


def _rgb_from_hex(hex_color: str) -> RGBColor:
    value = hex_color.strip().lstrip("#")
    return RGBColor(int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def _add_rect(
    slide, *, left: float, top: float, width: float, height: float, color: str
) -> None:
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(left),
        Inches(top),
        Inches(width),
        Inches(height),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb_from_hex(color)
    shape.line.fill.background()


def _add_line(slide, *, left: float, top: float, height: float, color: str) -> None:
    connector = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT,
        Inches(left),
        Inches(top),
        Inches(left),
        Inches(top + height),
    )
    connector.line.width = Pt(1)
    connector.line.color.rgb = _rgb_from_hex(color)


def _add_text(
    slide,
    *,
    text: str,
    left: float,
    top: float,
    width: float,
    height: float,
    color: str,
    size_pt: int,
    bold: bool = False,
) -> None:
    text_box = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    frame = text_box.text_frame
    frame.clear()
    paragraph = frame.paragraphs[0]
    paragraph.text = text
    paragraph.font.bold = bold
    paragraph.font.size = Pt(size_pt)
    paragraph.font.color.rgb = _rgb_from_hex(color)


def _clean(value: str | None) -> str:
    return "" if value is None else value.strip()


def _candidate_photo_paths(
    employee: dict[str, str], photos_dir: str | None
) -> list[Path]:
    if not photos_dir:
        return []

    photos_base = Path(photos_dir)
    if not photos_base.exists():
        return []

    candidates: list[Path] = []

    foto_field = _clean(employee.get("foto"))
    if foto_field:
        foto_path = Path(foto_field)
        if foto_path.is_absolute():
            candidates.append(foto_path)
        else:
            candidates.append(photos_base / foto_field)

    normalized_name = normalize_filename(_clean(employee.get("nome")))
    if normalized_name:
        for extension in (".jpg", ".png", ".jpeg", ".JPG", ".PNG", ".JPEG"):
            candidates.append(photos_base / f"{normalized_name}{extension}")

    return candidates


def _resolve_profile_image(
    employee: dict[str, str], photos_dir: str | None
) -> Image.Image:
    for candidate in _candidate_photo_paths(employee, photos_dir):
        if candidate.exists():
            image = make_circular_image(str(candidate))
            if image is not None:
                return image

    return generate_avatar(_clean(employee.get("nome")))


def build_slide(
    prs: Presentation,
    employee: dict[str, str],
    photos_dir: str | None,
) -> Slide:
    """Build one ficha slide for a single employee and return the slide object."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    _add_rect(
        slide, left=0.149, top=2.427, width=11.214, height=4.921, color=CINZA_GRANDE
    )
    _add_rect(
        slide, left=1.908, top=0.922, width=10.966, height=6.417, color=CINZA_MENOR
    )
    _add_rect(
        slide, left=2.309, top=0.980, width=0.202, height=1.279, color=VERDE_TITULO
    )
    _add_rect(
        slide, left=12.358, top=0.364, width=0.778, height=0.477, color=VERDE_TITULO
    )
    _add_rect(
        slide, left=0.000, top=7.118, width=4.797, height=0.388, color=VERDE_TITULO
    )

    nome = _clean(employee.get("nome"))
    cargo = _clean(employee.get("cargo"))
    antiguidade = _clean(employee.get("antiguidade"))

    _add_text(
        slide,
        text=nome,
        left=0.397,
        top=0.251,
        width=11.833,
        height=0.477,
        color=VERDE_TITULO,
        size_pt=24,
        bold=True,
    )

    info_parts = [part for part in (nome, cargo, antiguidade) if part]
    _add_text(
        slide,
        text="\n".join(info_parts),
        left=1.922,
        top=1.009,
        width=3.740,
        height=0.791,
        color=PRETO,
        size_pt=11,
        bold=False,
    )

    _add_line(slide, left=5.719, top=1.009, height=6.220, color=BRANCO)

    resumo_perfil = _clean(employee.get("resumo_perfil"))
    if resumo_perfil:
        _add_text(
            slide,
            text="RESUMO PERFIL",
            left=5.737,
            top=1.022,
            width=1.817,
            height=0.337,
            color=VERDE_TITULO,
            size_pt=12,
            bold=True,
        )
        _add_text(
            slide,
            text=resumo_perfil,
            left=5.737,
            top=1.423,
            width=6.898,
            height=1.745,
            color=PRETO,
            size_pt=11,
            bold=False,
        )

    formacao = _clean(employee.get("formacao"))
    if formacao:
        _add_text(
            slide,
            text="FORMACAO",
            left=0.240,
            top=3.075,
            width=4.400,
            height=0.337,
            color=VERDE_TITULO,
            size_pt=12,
            bold=True,
        )
        _add_text(
            slide,
            text=formacao,
            left=0.240,
            top=3.361,
            width=4.739,
            height=0.303,
            color=PRETO,
            size_pt=11,
            bold=False,
        )

    trajetoria = _clean(employee.get("trajetoria"))
    if trajetoria:
        _add_text(
            slide,
            text="TRAJETORIA",
            left=0.332,
            top=4.186,
            width=1.455,
            height=0.337,
            color=VERDE_TITULO,
            size_pt=12,
            bold=True,
        )
        _add_text(
            slide,
            text=trajetoria,
            left=0.326,
            top=4.640,
            width=5.411,
            height=2.128,
            color=CINZA_TRAJETORIA,
            size_pt=11,
            bold=False,
        )

    performance = _clean(employee.get("performance"))
    if performance:
        _add_text(
            slide,
            text="PERFORMANCE",
            left=5.775,
            top=3.341,
            width=1.860,
            height=0.337,
            color=VERDE_TITULO,
            size_pt=12,
            bold=True,
        )
        _add_text(
            slide,
            text=performance,
            left=5.867,
            top=3.694,
            width=1.835,
            height=0.505,
            color=PRETO,
            size_pt=11,
            bold=False,
        )

    profile_image = _resolve_profile_image(employee, photos_dir)
    temp_path = save_temp_png(profile_image)
    slide.shapes.add_picture(
        temp_path, PHOTO_LEFT, PHOTO_TOP, PHOTO_WIDTH, PHOTO_HEIGHT
    )

    temp_paths = getattr(prs, "_ficha_temp_png_paths", None)
    if temp_paths is None:
        temp_paths = []
        setattr(prs, "_ficha_temp_png_paths", temp_paths)
    temp_paths.append(temp_path)

    return slide


def _send_callback(callback: Callable[[dict], None] | None, payload: dict) -> None:
    if callback is not None:
        callback(payload)


def _cleanup_temp_files(paths: list[str]) -> None:
    for temp_path in paths:
        try:
            os.unlink(temp_path)
        except OSError:
            continue


def generate_ficha_pptx(
    employees: list[dict[str, str]],
    photos_dir: str | None,
    output_dir: str,
    callback: Callable[[dict], None] | None = None,
) -> list[str]:
    """Generate one ficha presentation file per employee in output_dir/fichas."""
    output_root = Path(output_dir) / "fichas"
    output_root.mkdir(parents=True, exist_ok=True)

    created_files: list[str] = []
    total = len(employees)

    for index, employee in enumerate(employees, start=1):
        temp_png_paths: list[str] = []
        name = _clean(employee.get("nome")) or f"Colaborador_{index}"

        try:
            _send_callback(
                callback,
                {
                    "type": "log",
                    "message": f"\u2713 Gerando slide: {name}",
                    "level": "success",
                },
            )

            prs = create_presentation()
            build_slide(prs, employee, photos_dir)
            temp_png_paths = list(getattr(prs, "_ficha_temp_png_paths", []))

            file_stem = normalize_filename(name) or f"Colaborador_{index}"
            output_path = output_root / f"{file_stem}.pptx"
            prs.save(str(output_path))
            created_files.append(str(output_path))

            _send_callback(
                callback,
                {"type": "progress", "current": index, "total": total, "name": name},
            )
        except Exception as exc:
            _send_callback(
                callback,
                {
                    "type": "log",
                    "message": f"Erro ao gerar slide para {name}: {exc}",
                    "level": "error",
                },
            )
        finally:
            _cleanup_temp_files(temp_png_paths)

    return created_files
