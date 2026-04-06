from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path
from typing import Final, TypedDict

from pptx import Presentation as PresentationFactory
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE, MSO_SHAPE
from pptx.presentation import Presentation
from pptx.slide import Slide
from pptx.util import Inches, Pt

from app.core.reader import CaromEmployee, normalize_filename

SLIDE_WIDTH: Final = Inches(13.271)
SLIDE_HEIGHT: Final = Inches(7.500)
HEADER_COLOR: Final = "#2D4200"
HEADER_TEXT_COLOR: Final = "#FFFFFF"
CARD_BG_COLOR: Final = "#F5F5F5"
TEXT_COLOR: Final = "#111827"
META_COLOR: Final = "#4B5563"
PLACEHOLDER_BORDER: Final = "#84BD00"


class CaromPreset(TypedDict):
    id: str
    label: str
    columns: int
    rows: int
    capacity: int
    rendered_fields: tuple[str, ...]


class CaromConfig(TypedDict):
    preset_id: str
    titulo: str
    file_basename: str


CAROM_PRESETS: Final[dict[str, CaromPreset]] = {
    "mini": {
        "id": "mini",
        "label": "Mini",
        "columns": 3,
        "rows": 6,
        "capacity": 18,
        "rendered_fields": ("nome", "cargo", "matricula"),
    },
    "regular": {
        "id": "regular",
        "label": "Regular",
        "columns": 2,
        "rows": 5,
        "capacity": 10,
        "rendered_fields": ("nome", "cargo", "matricula"),
    },
    "large": {
        "id": "large",
        "label": "Large",
        "columns": 2,
        "rows": 4,
        "capacity": 8,
        "rendered_fields": ("nome", "cargo", "matricula"),
    },
}


def create_presentation() -> Presentation:
    prs = PresentationFactory()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT
    return prs


def get_carom_preset(preset_id: str) -> CaromPreset:
    normalized = preset_id.strip().lower()
    if normalized not in CAROM_PRESETS:
        raise ValueError(f"Preset de carometro desconhecido: {preset_id}")
    return CAROM_PRESETS[normalized]


def compute_projected_slide_count(selected_count: int, capacity: int) -> int:
    if selected_count <= 0:
        return 0
    return math.ceil(selected_count / max(capacity, 1))


def compute_current_slide_status(selected_count: int, capacity: int) -> str:
    safe_capacity = max(capacity, 1)
    if selected_count <= 0:
        return f"{safe_capacity} people left to complete the current slide"
    position_in_current_slide = selected_count % safe_capacity
    if position_in_current_slide == 0:
        return "Current slide complete"
    return (
        f"{safe_capacity - position_in_current_slide} people left to complete the current slide"
    )


def _rgb_from_hex(hex_color: str) -> RGBColor:
    value = hex_color.strip().lstrip("#")
    return RGBColor(int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def _clean_str(value: object) -> str:
    return "" if value is None else str(value).strip()


def _add_rect(
    slide: Slide, *, left: float, top: float, width: float, height: float, color: str
) -> None:
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left),
        Inches(top),
        Inches(width),
        Inches(height),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb_from_hex(color)
    shape.line.fill.background()


def _add_text(
    slide: Slide,
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
    textbox = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    paragraph = textbox.text_frame.paragraphs[0]
    paragraph.text = text
    paragraph.font.size = Pt(size_pt)
    paragraph.font.bold = bold
    paragraph.font.color.rgb = _rgb_from_hex(color)


def _add_placeholder(slide: Slide, left: float, top: float, size: float) -> None:
    oval = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.OVAL,
        Inches(left),
        Inches(top),
        Inches(size),
        Inches(size),
    )
    oval.fill.solid()
    oval.fill.fore_color.rgb = _rgb_from_hex("#FFFFFF")
    oval.line.color.rgb = _rgb_from_hex(PLACEHOLDER_BORDER)
    oval.line.width = Pt(2)


def _build_card(
    slide: Slide,
    employee: CaromEmployee,
    *,
    card_x: float,
    card_y: float,
    card_width: float,
    card_height: float,
) -> None:
    _add_rect(
        slide,
        left=card_x,
        top=card_y,
        width=card_width,
        height=card_height,
        color=CARD_BG_COLOR,
    )

    placeholder_size = min(card_width * 0.30, card_height * 0.44)
    placeholder_x = card_x + 0.12
    placeholder_y = card_y + 0.12
    _add_placeholder(slide, placeholder_x, placeholder_y, placeholder_size)

    text_left = placeholder_x + placeholder_size + 0.14
    text_width = max(card_width - (text_left - card_x) - 0.12, 0.5)

    name = _clean_str(employee.get("nome")) or "Sem Nome"
    cargo = _clean_str(employee.get("cargo")) or "Cargo nao informado"
    matricula = _clean_str(employee.get("matricula")) or "-"

    _add_text(
        slide,
        text=name,
        left=text_left,
        top=card_y + 0.18,
        width=text_width,
        height=0.28,
        color=TEXT_COLOR,
        size_pt=11,
        bold=True,
    )
    _add_text(
        slide,
        text=cargo,
        left=text_left,
        top=card_y + 0.48,
        width=text_width,
        height=0.28,
        color=META_COLOR,
        size_pt=9,
    )
    _add_text(
        slide,
        text=f"Matricula {matricula}",
        left=text_left,
        top=card_y + 0.78,
        width=text_width,
        height=0.24,
        color=META_COLOR,
        size_pt=8,
    )


def _build_slide(
    prs: Presentation,
    title: str,
    employees: list[CaromEmployee],
    preset: CaromPreset,
) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide_width = prs.slide_width / Inches(1)
    slide_height = prs.slide_height / Inches(1)
    margin_x = 0.38
    margin_bottom = 0.34
    header_height = 0.82
    gutter_x = 0.16
    gutter_y = 0.14
    columns = preset["columns"]
    rows = preset["rows"]
    available_height = slide_height - header_height - margin_x - margin_bottom
    card_width = (slide_width - (2 * margin_x) - (gutter_x * (columns - 1))) / columns
    card_height = (available_height - (gutter_y * (rows - 1))) / rows

    _add_rect(
        slide,
        left=0.0,
        top=0.0,
        width=slide_width,
        height=header_height,
        color=HEADER_COLOR,
    )
    _add_text(
        slide,
        text=title,
        left=margin_x,
        top=0.22,
        width=slide_width - (2 * margin_x),
        height=0.32,
        color=HEADER_TEXT_COLOR,
        size_pt=16,
        bold=True,
    )

    for index, employee in enumerate(employees):
        row_index = index // columns
        col_index = index % columns
        card_x = margin_x + col_index * (card_width + gutter_x)
        card_y = header_height + margin_x + row_index * (card_height + gutter_y)
        _build_card(
            slide,
            employee,
            card_x=card_x,
            card_y=card_y,
            card_width=card_width,
            card_height=card_height,
        )


def _send_callback(callback: Callable[[dict], None] | None, payload: dict) -> None:
    if callback is not None:
        callback(payload)


def generate_carom_pptx(
    employees: list[CaromEmployee],
    output_dir: str,
    config: CaromConfig,
    callback: Callable[[dict], None] | None = None,
) -> list[str]:
    if not employees:
        return []

    preset = get_carom_preset(config["preset_id"])
    title = _clean_str(config.get("titulo", "")) or "Carometro"
    safe_name = normalize_filename(_clean_str(config.get("file_basename", "")) or title) or "Carometro"
    output_root = Path(output_dir) / "carometros"
    output_root.mkdir(parents=True, exist_ok=True)

    prs = create_presentation()
    capacity = preset["capacity"]
    total_slides = compute_projected_slide_count(len(employees), capacity)

    for slide_index in range(total_slides):
        start = slide_index * capacity
        end = start + capacity
        _build_slide(prs, title, employees[start:end], preset)
        _send_callback(
            callback,
            {
                "type": "log",
                "message": f"Montando slide {slide_index + 1} de {total_slides}",
                "level": "info",
            },
        )
        _send_callback(
            callback,
            {
                "type": "progress",
                "current": slide_index + 1,
                "total": total_slides,
                "name": title,
            },
        )

    output_path = output_root / f"{safe_name}.pptx"
    prs.save(str(output_path))
    return [str(output_path)]
