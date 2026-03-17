import importlib
import re

import pytest


def _load_theme_module():
    try:
        return importlib.import_module("app.config.theme")
    except ModuleNotFoundError as exc:
        pytest.fail(f"Theme module not found: {exc}")


def test_verde_usiminas_equals_84BD00():
    theme = _load_theme_module()
    assert theme.VERDE_USIMINAS == "#84BD00"


def test_verde_slide_equals_92D050():
    theme = _load_theme_module()
    assert theme.VERDE_SLIDE == "#92D050"


def test_verde_slide_is_different_from_verde_usiminas():
    theme = _load_theme_module()
    assert theme.VERDE_SLIDE != theme.VERDE_USIMINAS


def test_all_color_constants_match_hex_pattern():
    theme = _load_theme_module()
    pattern = re.compile(r"#[0-9A-Fa-f]{6}")
    color_constants = [
        theme.VERDE_USIMINAS,
        theme.VERDE_SLIDE,
        theme.VERDE_ESCURO,
        theme.VERDE_PROFUNDO,
        theme.FUNDO,
        theme.SUPERFICIE,
        theme.SUPERFICIE_2,
        theme.BORDA,
        theme.TEXTO_PRIMARIO,
        theme.TEXTO_SECUNDARIO,
        theme.TEXTO_TERCIARIO,
        theme.FUNDO_L,
        theme.SUPERFICIE_L,
        theme.SUPERFICIE_2_L,
        theme.BORDA_L,
        theme.TEXTO_PRIMARIO_L,
        theme.TEXTO_SECUNDARIO_L,
        theme.SUCESSO,
        theme.AVISO,
        theme.ERRO,
    ]

    assert all(pattern.fullmatch(color) for color in color_constants)


def test_dark_mode_constants_all_defined():
    theme = _load_theme_module()
    expected_names = [
        "FUNDO",
        "SUPERFICIE",
        "SUPERFICIE_2",
        "BORDA",
        "TEXTO_PRIMARIO",
        "TEXTO_SECUNDARIO",
        "TEXTO_TERCIARIO",
    ]
    assert all(hasattr(theme, name) for name in expected_names)


def test_light_mode_constants_all_defined():
    theme = _load_theme_module()
    expected_names = [
        "FUNDO_L",
        "SUPERFICIE_L",
        "SUPERFICIE_2_L",
        "BORDA_L",
        "TEXTO_PRIMARIO_L",
        "TEXTO_SECUNDARIO_L",
    ]
    assert all(hasattr(theme, name) for name in expected_names)


def test_semantic_colors_defined():
    theme = _load_theme_module()
    expected_names = ["SUCESSO", "AVISO", "ERRO"]
    assert all(hasattr(theme, name) for name in expected_names)


def test_font_tuples_are_three_element_tuples():
    theme = _load_theme_module()
    assert isinstance(theme.FONTE_TITULO, tuple)
    assert isinstance(theme.FONTE_CORPO, tuple)
    assert isinstance(theme.FONTE_LOG, tuple)
    assert len(theme.FONTE_TITULO) == 3
    assert len(theme.FONTE_CORPO) == 2
    assert len(theme.FONTE_LOG) == 2


def test_sidebar_width_is_200():
    theme = _load_theme_module()
    assert theme.SIDEBAR_WIDTH == 200


def test_topbar_height_is_48():
    theme = _load_theme_module()
    assert theme.TOPBAR_HEIGHT == 48
