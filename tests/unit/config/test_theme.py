from __future__ import annotations

from app.config import theme


def test_get_palette_returns_dark_by_default() -> None:
    assert theme.get_palette("anything")["bg"] == "#141414"


def test_get_palette_returns_light_when_requested() -> None:
    assert theme.get_palette("light")["bg"] == "#f0f0f0"


def test_stylesheet_contains_core_brand_colors() -> None:
    stylesheet = theme.build_stylesheet("dark")

    assert theme.VERDE_USIMINAS in stylesheet
    assert "#111111" in stylesheet


def test_stylesheet_changes_between_modes() -> None:
    assert theme.build_stylesheet("dark") != theme.build_stylesheet("light")
