from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from PySide6.QtWidgets import QLabel

from app.config.settings import get_default_output_dir
from app.ui.screen_carom import CaromScreen


def _make_local_spreadsheet_stub() -> Path:
    temp_dir = Path.cwd() / ".tmp-test-ui"
    temp_dir.mkdir(exist_ok=True)
    file_path = temp_dir / f"dados-{uuid4().hex}.xlsx"
    file_path.write_bytes(b"x")
    return file_path


def test_carom_screen_validates_local_file_and_mapping(qtbot) -> None:
    file_path = _make_local_spreadsheet_stub()
    try:
        screen = CaromScreen({})
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


def test_carom_screen_source_fields_use_shared_runtime_states(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)

    assert screen.entry_source.isReadOnly() is False
    assert screen.entry_source.isEnabled() is True
    assert screen.entry_source.styleSheet() == ""
    assert screen.entry_output.isReadOnly() is True
    assert screen.entry_output.isEnabled() is True
    assert screen.entry_output.styleSheet() == ""


def test_carom_screen_get_config_uses_default_output_dir(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    screen.entry_source.setText("https://example.com/file.xlsx")
    screen._column_selectors["nome"].addItem("Nome")
    screen._column_selectors["cargo"].addItem("Cargo")
    screen._column_selectors["nome"].setCurrentText("Nome")
    screen._column_selectors["cargo"].setCurrentText("Cargo")

    received = []
    screen.generate_requested.connect(received.append)
    screen._start_generation()

    assert received[0]["output_dir"] == str(get_default_output_dir())


def test_carom_screen_has_no_preview_or_sample_text(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)

    labels = [label.text().lower() for label in screen.findChildren(QLabel)]
    assert all("preview" not in text for text in labels)
    assert all("amostra" not in text for text in labels)


def test_carom_screen_handles_sidebar_collapsed_state(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)

    screen.set_sidebar_collapsed(True)
    assert screen.source_hint.isHidden() is True
    assert screen.mapping_hint.isHidden() is True
    assert screen.options_hint.isHidden() is True

    screen.set_sidebar_collapsed(False)
    assert screen.source_hint.isHidden() is False
    assert screen.mapping_hint.isHidden() is False
    assert screen.options_hint.isHidden() is False
