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


def test_stylesheet_uses_shared_input_surfaces_and_ficha_specific_display_rules() -> (
    None
):
    stylesheet = theme.build_stylesheet("dark")

    assert "QFrame#panel QLineEdit" not in stylesheet
    assert "QLineEdit:read-only" in stylesheet
    assert "QFrame#fichaSourceCard" in stylesheet
    assert "QFrame#fichaActionBar" in stylesheet
    assert "QLineEdit#fichaDisplayField" in stylesheet
    assert "QFrame#metricCard QLineEdit" in stylesheet
    assert "QFrame#logPanel QTextEdit#logBox" in stylesheet


def test_stylesheet_has_no_global_transparent_input_override() -> None:
    stylesheet = theme.build_stylesheet("dark")

    transparent_input_rule = (
        "QLineEdit, QComboBox, QTextEdit, QListWidget, QSpinBox {{\n"
        "    background-color: transparent;"
    )
    assert transparent_input_rule not in stylesheet


def test_stylesheet_keeps_labels_transparent_and_section_cards_themable() -> None:
    stylesheet = theme.build_stylesheet("light")

    assert "QLabel {\n    background-color: transparent;\n}" in stylesheet
    assert "QFrame#sectionCard" in stylesheet
    assert "QFrame#heroCard" in stylesheet
    assert "QFrame#statusPanel" in stylesheet
    assert "QFrame#logPanel" in stylesheet
    assert "QFrame#settingsPanel" in stylesheet


def test_light_stylesheet_uses_dedicated_input_tokens() -> None:
    stylesheet = theme.build_stylesheet("light")

    assert "QLineEdit,\nQComboBox,\nQSpinBox,\nQTextEdit,\nQListWidget {" in stylesheet
    assert "background-color: #FFFFFF;" in stylesheet
    assert "border: 1px solid #BFC6B3;" in stylesheet
    assert "border-color: #95A08A;" in stylesheet
    assert "QLineEdit:read-only,\nQTextEdit:read-only {" in stylesheet
    assert "background-color: #F2F5EC;" in stylesheet
    assert "border-color: #AAB49E;" in stylesheet


def test_stylesheet_has_sidebar_compact_and_toggle_rules() -> None:
    stylesheet = theme.build_stylesheet("dark")

    assert 'QFrame#sidebar[collapsed="true"]' in stylesheet
    assert "QPushButton#sidebar_toggle" in stylesheet
    assert 'QFrame#sidebar[collapsed="true"] QPushButton#navButton' in stylesheet
