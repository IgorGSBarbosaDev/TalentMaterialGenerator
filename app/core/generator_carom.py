from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Final, TypedDict
import unicodedata

from pptx import Presentation as PresentationFactory
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.presentation import Presentation
from pptx.slide import Slide
from pptx.util import Inches, Pt

from app.core.reader import normalize_filename

SLIDE_WIDTH: Final = Inches(13.271)
SLIDE_HEIGHT: Final = Inches(7.500)

HEADER_COLOR: Final = "#4A6E00"
HEADER_TEXT_COLOR: Final = "#FFFFFF"
CARD_BG_COLOR: Final = "#F5F5F5"
TEXT_COLOR: Final = "#111827"
UNKNOWN_POTENTIAL_COLOR: Final = "#9CA3AF"

CORES_POTENCIAL: Final[dict[str, str]] = {
    "alto": "#84BD00",
    "medio": "#F59E0B",
    "médio": "#F59E0B",
    "baixo": "#EF4444",
}


class CaromConfig(TypedDict):
    colunas: int
    agrupamento: str | None
    titulo: str
    show_nota: bool
    show_potencial: bool
    show_cargo: bool
    cores_automaticas: bool


def create_presentation() -> Presentation:
    """Create a carometro presentation with required dimensions."""
    prs = PresentationFactory()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT
    return prs


def _rgb_from_hex(hex_color: str) -> RGBColor:
    value = hex_color.strip().lstrip("#")
    return RGBColor(int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def _clean_str(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return default


def _normalize_token(value: object) -> str:
    text = _clean_str(value).lower()
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _add_rect(
    slide, *, left: float, top: float, width: float, height: float, color: str
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
    textbox = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    frame = textbox.text_frame
    frame.clear()
    paragraph = frame.paragraphs[0]
    paragraph.text = text
    paragraph.font.size = Pt(size_pt)
    paragraph.font.bold = bold
    paragraph.font.color.rgb = _rgb_from_hex(color)


def get_score_color(score: float) -> str:
    """Return semantic score color by threshold."""
    if score >= 4.0:
        return "#84BD00"
    if score >= 3.0:
        return "#F59E0B"
    return "#EF4444"


def get_potential_color(potential: str) -> str:
    """Return semantic potential color for alto/medio/baixo values."""
    normalized = _normalize_token(potential)
    return CORES_POTENCIAL.get(normalized, UNKNOWN_POTENTIAL_COLOR)


def group_employees(
    employees: list[dict[str, object]], grouping_field: str | None
) -> dict[str, list[dict[str, object]]]:
    """Group employees and sort each group by descending score."""
    if not employees:
        return {}

    groups: dict[str, list[dict[str, object]]] = {}

    if not grouping_field:
        groups["Todos"] = list(employees)
    else:
        for employee in employees:
            raw_group = _clean_str(employee.get(grouping_field))
            group_name = raw_group or "Sem Grupo"
            groups.setdefault(group_name, []).append(employee)

    for items in groups.values():
        items.sort(key=lambda item: _safe_float(item.get("nota"), 0.0), reverse=True)

    return groups


def build_card(
    slide: Slide,
    employee: dict[str, object],
    photos_dir: str | None,
    card_x: float,
    card_y: float,
    card_width: float,
    card_height: float,
    config: CaromConfig,
) -> None:
    """Render one employee card in the carometro grid."""
    del photos_dir

    _add_rect(
        slide,
        left=card_x,
        top=card_y,
        width=card_width,
        height=card_height,
        color=CARD_BG_COLOR,
    )

    name = _clean_str(employee.get("nome")) or "Sem Nome"
    cargo = _clean_str(employee.get("cargo"))
    potential = _clean_str(employee.get("potencial"))
    score_value = _safe_float(employee.get("nota"), 0.0)
    score_text = f"{score_value:.1f}"

    _add_text(
        slide,
        text=name,
        left=card_x + 0.08,
        top=card_y + 0.08,
        width=card_width - 0.16,
        height=0.28,
        color=TEXT_COLOR,
        size_pt=12,
        bold=True,
    )

    if config["show_cargo"] and cargo:
        _add_text(
            slide,
            text=cargo,
            left=card_x + 0.08,
            top=card_y + 0.38,
            width=card_width - 0.16,
            height=0.24,
            color=TEXT_COLOR,
            size_pt=10,
        )

    if config["show_nota"]:
        score_color = get_score_color(score_value)
        if not config["cores_automaticas"]:
            score_color = TEXT_COLOR
        _add_text(
            slide,
            text=score_text,
            left=card_x + 0.08,
            top=card_y + card_height - 0.34,
            width=0.50,
            height=0.24,
            color=score_color,
            size_pt=12,
            bold=True,
        )

    if config["show_potencial"] and potential:
        badge_color = get_potential_color(potential)
        if not config["cores_automaticas"]:
            badge_color = TEXT_COLOR
        _add_text(
            slide,
            text=potential,
            left=card_x + card_width - 0.95,
            top=card_y + card_height - 0.34,
            width=0.87,
            height=0.24,
            color=badge_color,
            size_pt=10,
            bold=True,
        )


def _send_callback(callback: Callable[[dict], None] | None, payload: dict) -> None:
    if callback is not None:
        callback(payload)


def _build_group_slide(
    prs: Presentation,
    group_name: str,
    employees: list[dict[str, object]],
    photos_dir: str | None,
    config: CaromConfig,
) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    margin = 0.30
    header_height = 0.80
    card_height = 1.45
    n_columns = max(1, config["colunas"])

    slide_width = prs.slide_width / Inches(1)

    # Required grid layout formulas for card sizing and placement.
    card_width = (slide_width - 2 * margin) / n_columns

    _add_rect(
        slide,
        left=0.0,
        top=0.0,
        width=slide_width,
        height=header_height,
        color=HEADER_COLOR,
    )

    title = f"{config['titulo']} - {group_name}" if config["titulo"] else group_name
    _add_text(
        slide,
        text=title,
        left=margin,
        top=0.20,
        width=slide_width - (2 * margin),
        height=0.35,
        color=HEADER_TEXT_COLOR,
        size_pt=16,
        bold=True,
    )

    for index, employee in enumerate(employees):
        row_index = index // n_columns
        col_index = index % n_columns

        card_x = margin + col_index * card_width
        card_y = header_height + margin + row_index * card_height

        build_card(
            slide,
            employee,
            photos_dir,
            card_x,
            card_y,
            card_width,
            card_height,
            config,
        )


def generate_carom_pptx(
    employees: list[dict[str, object]],
    photos_dir: str | None,
    output_dir: str,
    config: CaromConfig,
    callback: Callable[[dict], None] | None = None,
) -> list[str]:
    """Generate carometro PPTX files, one per group."""
    output_root = Path(output_dir) / "carometros"
    output_root.mkdir(parents=True, exist_ok=True)

    groups = group_employees(employees, config["agrupamento"])
    if not groups:
        return []

    created_files: list[str] = []
    total = len(groups)

    for current, (group_name, group_members) in enumerate(groups.items(), start=1):
        prs = create_presentation()
        _build_group_slide(prs, group_name, group_members, photos_dir, config)

        safe_group = normalize_filename(group_name) or f"grupo_{current}"
        output_path = output_root / f"{safe_group}.pptx"
        prs.save(str(output_path))
        created_files.append(str(output_path))

        _send_callback(
            callback,
            {
                "type": "log",
                "message": f"\u2713 Gerando carometro: {group_name}",
                "level": "success",
            },
        )
        _send_callback(
            callback,
            {
                "type": "progress",
                "current": current,
                "total": total,
                "name": group_name,
            },
        )

    return created_files
