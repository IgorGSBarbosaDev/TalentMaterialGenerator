from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from PySide6.QtWidgets import QLabel

from app.config.settings import get_default_output_dir
from app.ui.screen_ficha import FichaScreen


def _make_local_spreadsheet_stub() -> Path:
    temp_dir = Path.cwd() / ".tmp-test-ui"
    temp_dir.mkdir(exist_ok=True)
    file_path = temp_dir / f"dados-{uuid4().hex}.xlsx"
    file_path.write_bytes(b"x")
    return file_path


def test_ficha_screen_validates_local_file_and_mapping(qtbot) -> None:
    file_path = _make_local_spreadsheet_stub()
    try:
        screen = FichaScreen({})
        qtbot.addWidget(screen)
        screen.source_type.setCurrentText("Arquivo local")
        screen.entry_source.setText(str(file_path))
        screen._column_selectors["nome"].addItem("Nome")
        screen._column_selectors["cargo"].addItem("Cargo")
        screen._column_selectors["nome"].setCurrentText("Nome")
        screen._column_selectors["cargo"].setCurrentText("Cargo")

        assert screen._validate_inputs() is True
    finally:
        file_path.unlink(missing_ok=True)


def test_ficha_screen_get_config_returns_output_mode(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)
    screen.entry_source.setText("https://example.com/file.xlsx")

    config = screen._get_config()

    assert "output_mode" in config
    assert config["output_dir"] == str(get_default_output_dir())


def test_ficha_screen_has_no_preview_placeholder_text(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)

    labels = [label.text().lower() for label in screen.findChildren(QLabel)]
    assert all("preview" not in text.lower() for text in labels)
    assert all("origem, saida e modo" not in text for text in labels)
    assert all("mapeie campos obrigatorios" not in text for text in labels)


def test_ficha_screen_handles_sidebar_collapsed_state(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)

    screen.set_sidebar_collapsed(True)
    assert screen._root_layout.spacing() == 12

    screen.set_sidebar_collapsed(False)
    assert screen._root_layout.spacing() == 16


def test_ficha_screen_form_controls_live_inside_panel_container(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)

    assert screen.entry_source.parentWidget().objectName() == "panel"
    assert screen.source_type.parentWidget().objectName() == "panel"
