from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Final, Literal

from pptx import Presentation as PresentationFactory
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE, MSO_CONNECTOR, MSO_SHAPE
from pptx.presentation import Presentation
from pptx.slide import Slide
from pptx.util import Inches, Pt

from app.core.reader import normalize_filename, parse_multiline_field

SlideOutputMode = Literal["one_file_per_employee", "single_deck"]

SLIDE_WIDTH: Final = Inches(13.271)
SLIDE_HEIGHT: Final = Inches(7.500)
VERDE_TITULO: Final = "#92D050"
VERDE_USIMINAS: Final = "#84BD00"
CINZA_TRAJETORIA: Final = "#666666"
CINZA_GRANDE: Final = "#D9D9D9"
CINZA_MENOR: Final = "#ECECEC"
BRANCO: Final = "#FFFFFF"
PRETO: Final = "#000000"


def create_presentation() -> Presentation:
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
    paragraph = text_box.text_frame.paragraphs[0]
    paragraph.text = text
    paragraph.font.bold = bold
    paragraph.font.size = Pt(size_pt)
    paragraph.font.color.rgb = _rgb_from_hex(color)


def _add_multiline_with_bold_dates(
    slide,
    *,
    entries: list[str],
    left: float,
    top: float,
    width: float,
    height: float,
    color: str,
    size_pt: int,
) -> None:
    text_box = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    frame = text_box.text_frame
    frame.clear()

    for index, entry in enumerate(entries):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        if " - " in entry:
            period, role = entry.split(" - ", 1)
            run_period = paragraph.add_run()
            run_period.text = f"{period} - "
            run_period.font.bold = True
            run_period.font.size = Pt(size_pt)
            run_period.font.color.rgb = _rgb_from_hex(color)

            run_role = paragraph.add_run()
            run_role.text = role
            run_role.font.size = Pt(size_pt)
            run_role.font.color.rgb = _rgb_from_hex(color)
        else:
            paragraph.text = entry
            paragraph.font.size = Pt(size_pt)
            paragraph.font.color.rgb = _rgb_from_hex(color)


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


def _add_photo_placeholder(slide) -> None:
    oval = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.OVAL,
        Inches(0.385),
        Inches(1.000),
        Inches(1.382),
        Inches(1.344),
    )
    oval.fill.solid()
    oval.fill.fore_color.rgb = _rgb_from_hex(BRANCO)
    oval.line.color.rgb = _rgb_from_hex(VERDE_USIMINAS)
    oval.line.width = Pt(2)


def _clean(value: str | None) -> str:
    return "" if value is None else value.strip()


def build_slide(prs: Presentation, employee: dict[str, str]) -> Slide:
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
        slide, left=0.000, top=7.118, width=4.797, height=0.388, color=VERDE_USIMINAS
    )
    _add_photo_placeholder(slide)

    nome = _clean(employee.get("nome"))
    idade = _clean(employee.get("idade"))
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

    info_lines = []
    if nome:
        info_lines.append(f"{nome} ({idade})" if idade else nome)
    if cargo:
        info_lines.append(cargo)
    if antiguidade:
        info_lines.append(f"Antiguidade: {antiguidade}")
    _add_text(
        slide,
        text="\n".join(info_lines),
        left=1.922,
        top=1.009,
        width=3.740,
        height=0.791,
        color=PRETO,
        size_pt=11,
    )

    _add_line(slide, left=5.719, top=1.009, height=6.220, color=BRANCO)

    resumo = _clean(employee.get("resumo_perfil"))
    if resumo:
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
            text=resumo,
            left=5.737,
            top=1.423,
            width=6.898,
            height=1.745,
            color=PRETO,
            size_pt=11,
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
        )

    trajetoria_items = parse_multiline_field(_clean(employee.get("trajetoria")))
    if trajetoria_items:
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
            text="USIMINAS",
            left=0.326,
            top=4.430,
            width=1.500,
            height=0.220,
            color=CINZA_TRAJETORIA,
            size_pt=11,
            bold=True,
        )
        _add_multiline_with_bold_dates(
            slide,
            entries=trajetoria_items,
            left=0.326,
            top=4.640,
            width=5.411,
            height=2.128,
            color=CINZA_TRAJETORIA,
            size_pt=10,
        )

    performance_items = parse_multiline_field(_clean(employee.get("performance")))
    if performance_items:
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
            text="\n".join(performance_items),
            left=5.867,
            top=3.694,
            width=1.835,
            height=0.505,
            color=PRETO,
            size_pt=11,
        )

    return slide


def _send_callback(callback: Callable[[dict], None] | None, payload: dict) -> None:
    if callback is not None:
        callback(payload)


def generate_ficha_pptx(
    employees: list[dict[str, str]],
    output_dir: str,
    *,
    output_mode: SlideOutputMode = "one_file_per_employee",
    callback: Callable[[dict], None] | None = None,
) -> list[str]:
    output_root = Path(output_dir) / "fichas"
    output_root.mkdir(parents=True, exist_ok=True)
    created_files: list[str] = []
    total = len(employees)

    if output_mode == "single_deck":
        prs = create_presentation()
        for index, employee in enumerate(employees, start=1):
            name = _clean(employee.get("nome")) or f"Colaborador_{index}"
            _send_callback(
                callback,
                {"type": "log", "message": f"Gerando ficha: {name}", "level": "success"},
            )
            build_slide(prs, employee)
            _send_callback(
                callback,
                {"type": "progress", "current": index, "total": total, "name": name},
            )
        output_path = output_root / "Fichas_Consolidadas.pptx"
        prs.save(str(output_path))
        created_files.append(str(output_path))
        return created_files

    for index, employee in enumerate(employees, start=1):
        name = _clean(employee.get("nome")) or f"Colaborador_{index}"
        try:
            _send_callback(
                callback,
                {"type": "log", "message": f"Gerando ficha: {name}", "level": "success"},
            )
            prs = create_presentation()
            build_slide(prs, employee)
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
                    "message": f"Erro ao gerar ficha para {name}: {exc}",
                    "level": "error",
                },
            )

    return created_files
