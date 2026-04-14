from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path
from typing import Final, TypedDict

from pptx import Presentation as PresentationFactory
from pptx.slide import Slide

from app.core.carom_templates import CaromTemplate, get_carom_preset
from app.core.pptx_template_utils import (
    clear_text,
    clone_slide,
    placeholder_picture_bytes,
    replace_picture,
    replace_text,
    resolve_shape_path,
)
from app.core.reader import (
    CaromEmployee,
    normalize_filename,
    resolve_carom_display_score_potential,
    validate_carom_employee_for_preset,
)

PROJETO_TRAINEE_BODY_TEXT: Final = "insira projeto trainee aqui"


class CaromConfig(TypedDict):
    preset_id: str
    titulo: str
    file_basename: str


def compute_projected_slide_count(selected_count: int, capacity: int) -> int:
    if selected_count <= 0:
        return 0
    return math.ceil(selected_count / max(capacity, 1))


def compute_current_slide_status(selected_count: int, capacity: int) -> str:
    safe_capacity = max(capacity, 1)
    if selected_count <= 0:
        return f"Faltam {safe_capacity} pessoas para completar o slide atual"
    position_in_current_slide = selected_count % safe_capacity
    if position_in_current_slide == 0:
        return "Slide atual completo"
    return f"Faltam {safe_capacity - position_in_current_slide} pessoas para completar o slide atual"


def _clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def _compose_non_empty(parts: list[str], separator: str) -> str:
    return separator.join(part for part in parts if part)


def _employee_name(employee: CaromEmployee) -> str:
    return _clean(employee.get("nome")) or "Sem Nome"


def _employee_age(employee: CaromEmployee) -> str:
    return _clean(employee.get("idade"))


def _employee_role(employee: CaromEmployee) -> str:
    return _clean(employee.get("cargo"))


def _employee_formation(employee: CaromEmployee) -> str:
    return _clean(employee.get("formacao"))


def _employee_ceo3(employee: CaromEmployee) -> str:
    return _clean(employee.get("ceo3"))


def _employee_ceo4(employee: CaromEmployee) -> str:
    return _clean(employee.get("ceo4"))


def _employee_score(employee: CaromEmployee) -> str:
    return _clean(resolve_carom_display_score_potential(employee))


def _mini_lines(employee: CaromEmployee) -> list[str]:
    return [
        _employee_name(employee),
        _compose_non_empty([_employee_role(employee), _employee_age(employee)], " | "),
        _employee_ceo3(employee),
    ]


def _big_lines(employee: CaromEmployee) -> list[str]:
    headline = _compose_non_empty(
        [
            _employee_name(employee),
            _compose_non_empty(
                [_employee_age(employee), _employee_score(employee)],
                " - ",
            ),
        ],
        " | ",
    )
    return [
        headline,
        _employee_formation(employee),
        _employee_role(employee),
        _employee_ceo3(employee),
    ]


def _trainee_identity_lines(employee: CaromEmployee) -> list[str]:
    headline = _compose_non_empty(
        [
            _employee_name(employee),
            _compose_non_empty(
                [_employee_age(employee), _employee_score(employee)],
                " - ",
            ),
        ],
        " | ",
    )
    return [
        headline,
        _employee_role(employee),
        _employee_formation(employee),
        _employee_ceo4(employee),
    ]


def _talent_review_lines(employee: CaromEmployee) -> list[str]:
    headline = _compose_non_empty(
        [
            _employee_name(employee),
            _compose_non_empty(
                [_employee_age(employee), _employee_score(employee)],
                " - ",
            ),
        ],
        " | ",
    )
    return [
        headline,
        _employee_role(employee),
        "Sucessor Imediato",
        _employee_ceo3(employee),
        "Em desenvolvimento",
        _employee_ceo4(employee),
    ]


def _picture_bytes_for_employee(employee: CaromEmployee) -> bytes:
    foto = _clean(employee.get("foto"))
    if foto:
        photo_path = Path(foto)
        if photo_path.is_file():
            return photo_path.read_bytes()
    return placeholder_picture_bytes()


def _replace_picture_at_path(slide: Slide, picture_path: tuple[int, ...], image_bytes: bytes) -> None:
    picture_shape = resolve_shape_path(slide, picture_path)
    replace_picture(slide, picture_shape, image_bytes)


def _set_title_if_editable(slide: Slide, preset: CaromTemplate, title: str) -> None:
    if not preset.editable_title or preset.title_path is None:
        return
    replace_text(resolve_shape_path(slide, preset.title_path), [title])
    if preset.subtitle_path is not None:
        clear_text(resolve_shape_path(slide, preset.subtitle_path))


def _render_slot(slide: Slide, preset: CaromTemplate, slot: dict[str, tuple[int, ...]], employee: CaromEmployee | None) -> None:
    if preset.id == "mini":
        _render_basic_slot(slide, slot, employee, _mini_lines)
        return
    if preset.id == "big":
        _render_basic_slot(slide, slot, employee, _big_lines)
        return
    if preset.id == "projeto_trainee":
        _render_trainee_slot(slide, slot, employee)
        return
    if preset.id == "talent_review":
        _render_talent_review_slot(slide, slot, employee)
        return
    raise ValueError(f"Preset de carometro desconhecido: {preset.id}")


def _render_basic_slot(
    slide: Slide,
    slot: dict[str, tuple[int, ...]],
    employee: CaromEmployee | None,
    formatter: Callable[[CaromEmployee], list[str]],
) -> None:
    if employee is None:
        clear_text(resolve_shape_path(slide, slot["text"]))
        _replace_picture_at_path(slide, slot["picture"], placeholder_picture_bytes())
        return
    replace_text(resolve_shape_path(slide, slot["text"]), formatter(employee))
    _replace_picture_at_path(slide, slot["picture"], _picture_bytes_for_employee(employee))


def _render_trainee_slot(
    slide: Slide,
    slot: dict[str, tuple[int, ...]],
    employee: CaromEmployee | None,
) -> None:
    if employee is None:
        clear_text(resolve_shape_path(slide, slot["identity"]))
        clear_text(resolve_shape_path(slide, slot["body"]))
        _replace_picture_at_path(slide, slot["picture"], placeholder_picture_bytes())
        return
    replace_text(resolve_shape_path(slide, slot["identity"]), _trainee_identity_lines(employee))
    replace_text(resolve_shape_path(slide, slot["body"]), [PROJETO_TRAINEE_BODY_TEXT])
    _replace_picture_at_path(slide, slot["picture"], _picture_bytes_for_employee(employee))


def _render_talent_review_slot(
    slide: Slide,
    slot: dict[str, tuple[int, ...]],
    employee: CaromEmployee | None,
) -> None:
    text_shape = resolve_shape_path(slide, slot["text"])
    if employee is None:
        replace_text(text_shape, ["", "", "", "", "", ""])
        _replace_picture_at_path(slide, slot["picture"], placeholder_picture_bytes())
        return
    replace_text(text_shape, _talent_review_lines(employee))
    _replace_picture_at_path(slide, slot["picture"], _picture_bytes_for_employee(employee))


def _send_callback(callback: Callable[[dict], None] | None, payload: dict) -> None:
    if callback is not None:
        callback(payload)


def _validate_employees_for_preset(employees: list[CaromEmployee], preset_id: str) -> None:
    for employee in employees:
        missing = validate_carom_employee_for_preset(employee, preset_id)
        if missing:
            joined = ", ".join(missing)
            name = _employee_name(employee)
            raise ValueError(
                f"O colaborador '{name}' nao possui os campos obrigatorios "
                f"para o template escolhido: {joined}."
            )


def generate_carom_pptx(
    employees: list[CaromEmployee],
    output_dir: str,
    config: CaromConfig,
    callback: Callable[[dict], None] | None = None,
) -> list[str]:
    if not employees:
        return []

    preset = get_carom_preset(config["preset_id"])
    _validate_employees_for_preset(employees, preset.id)
    title = _clean(config.get("titulo", "")) or preset.default_title
    safe_name = normalize_filename(_clean(config.get("file_basename", "")) or title) or "Carometro"
    output_root = Path(output_dir) / "carometros"
    output_root.mkdir(parents=True, exist_ok=True)

    prs = PresentationFactory(str(preset.template_path))
    template_slide = prs.slides[0]
    capacity = preset.capacity
    total_slides = compute_projected_slide_count(len(employees), capacity)
    slides: list[Slide] = [template_slide]
    for _ in range(total_slides - 1):
        slides.append(clone_slide(prs, template_slide))

    for slide_index, slide in enumerate(slides):
        start = slide_index * capacity
        end = start + capacity
        batch = employees[start:end]
        _set_title_if_editable(slide, preset, title)
        for slot_index, slot in enumerate(preset.slots):
            employee = batch[slot_index] if slot_index < len(batch) else None
            _render_slot(slide, preset, slot, employee)
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
