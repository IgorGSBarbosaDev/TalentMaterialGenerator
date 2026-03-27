from __future__ import annotations

from pathlib import Path

from app.config.settings import get_default_output_dir
from app.ui.screen_carom import CaromScreen


def test_carom_screen_validates_local_file_and_mapping(tmp_path: Path, qtbot) -> None:
    file_path = tmp_path / "dados.xlsx"
    file_path.write_bytes(b"x")

    screen = CaromScreen({})
    qtbot.addWidget(screen)
    screen.source_type.setCurrentText("Arquivo local")
    screen.entry_source.setText(str(file_path))
    screen._column_selectors["nome"].addItem("Nome")
    screen._column_selectors["cargo"].addItem("Cargo")
    screen._column_selectors["nome"].setCurrentText("Nome")
    screen._column_selectors["cargo"].setCurrentText("Cargo")

    assert screen._validate_inputs() is True


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
