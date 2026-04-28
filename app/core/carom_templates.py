from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from app.core.resource_paths import resolve_existing_resource_path


@dataclass(frozen=True)
class CaromTemplate:
    id: str
    label: str
    output_type: str
    template_name: str
    capacity: int
    editable_title: bool
    default_title: str
    title_path: tuple[int, ...] | None
    subtitle_path: tuple[int, ...] | None
    required_fields: tuple[str, ...]
    requires_display_score: bool
    slots: tuple[dict[str, tuple[int, ...]], ...]

    @property
    def template_path(self) -> Path:
        return resolve_carom_template_path(self.template_name)


CAROM_TEMPLATE_ALIASES: Final[dict[str, str]] = {
    "regular": "mini",
    "large": "big",
}


CAROM_TEMPLATES: Final[dict[str, CaromTemplate]] = {
    "mini": CaromTemplate(
        id="mini",
        label="Mini",
        output_type="Mini",
        template_name="Carometro-mini.pptx",
        capacity=18,
        editable_title=True,
        default_title="Carometro",
        title_path=(1,),
        subtitle_path=(3, 1),
        required_fields=("nome", "cargo"),
        requires_display_score=False,
        slots=(
            {"picture": (4, 0), "text": (4, 1)},
            {"picture": (10, 0), "text": (10, 1)},
            {"picture": (8, 0), "text": (8, 1)},
            {"picture": (5, 0), "text": (5, 1)},
            {"picture": (11, 1), "text": (11, 0)},
            {"picture": (9, 0), "text": (9, 1)},
            {"picture": (6, 0), "text": (6, 1)},
            {"picture": (13, 1), "text": (13, 0)},
            {"picture": (14, 0), "text": (14, 1)},
            {"picture": (7, 0), "text": (7, 1)},
            {"picture": (20, 1), "text": (20, 0)},
            {"picture": (18, 0), "text": (18, 1)},
            {"picture": (16, 0), "text": (16, 1)},
            {"picture": (12, 0), "text": (12, 1)},
            {"picture": (19, 0), "text": (19, 1)},
            {"picture": (17, 0), "text": (17, 1)},
            {"picture": (15, 0), "text": (15, 1)},
            {"picture": (21, 0), "text": (21, 1)},
        ),
    ),
    "big": CaromTemplate(
        id="big",
        label="Big",
        output_type="Big",
        template_name="Carometro-big.pptx",
        capacity=8,
        editable_title=True,
        default_title="Carometro",
        title_path=(17,),
        subtitle_path=None,
        required_fields=("nome", "cargo", "idade", "formacao", "ceo3"),
        requires_display_score=True,
        slots=(
            {"picture": (1,), "text": (0,)},
            {"picture": (9,), "text": (8,)},
            {"picture": (3,), "text": (2,)},
            {"picture": (11,), "text": (10,)},
            {"picture": (5,), "text": (4,)},
            {"picture": (13,), "text": (12,)},
            {"picture": (7,), "text": (6,)},
            {"picture": (15,), "text": (14,)},
        ),
    ),
    "projeto_trainee": CaromTemplate(
        id="projeto_trainee",
        label="Projeto Trainee",
        output_type="ProjetoTrainee",
        template_name="CarometroProjetoTrainee.pptx",
        capacity=2,
        editable_title=False,
        default_title="Carometro Projeto Trainee",
        title_path=None,
        subtitle_path=None,
        required_fields=("nome", "cargo", "idade", "formacao", "ceo4"),
        requires_display_score=True,
        slots=(
            {"picture": (10,), "identity": (8,), "body": (9,)},
            {"picture": (12,), "identity": (11,), "body": (13,)},
        ),
    ),
    "talent_review": CaromTemplate(
        id="talent_review",
        label="Talent Review",
        output_type="TalentReview",
        template_name="CarometroTalentReview.pptx",
        capacity=12,
        editable_title=False,
        default_title="Talent Review",
        title_path=None,
        subtitle_path=None,
        required_fields=("nome", "cargo", "idade"),
        requires_display_score=True,
        slots=(
            {"picture": (3,), "text": (5,)},
            {"picture": (28,), "text": (24,)},
            {"picture": (16,), "text": (17,)},
            {"picture": (22,), "text": (23,)},
            {"picture": (9,), "text": (11,)},
            {"picture": (18,), "text": (19,)},
            {"picture": (6,), "text": (8,)},
            {"picture": (12,), "text": (13,)},
            {"picture": (30,), "text": (31,)},
            {"picture": (7,), "text": (10,)},
            {"picture": (29,), "text": (26,)},
            {"picture": (33,), "text": (32,)},
        ),
    ),
}


def resolve_carom_template_path(template_name: str) -> Path:
    return resolve_existing_resource_path(
        "carometros",
        template_name,
        resource_label=f"Template de carometro '{template_name}'",
    )


def get_carom_preset(preset_id: str) -> CaromTemplate:
    normalized = preset_id.strip().lower()
    normalized = CAROM_TEMPLATE_ALIASES.get(normalized, normalized)
    if normalized not in CAROM_TEMPLATES:
        raise ValueError(f"Preset de carometro desconhecido: {preset_id}")
    return CAROM_TEMPLATES[normalized]
