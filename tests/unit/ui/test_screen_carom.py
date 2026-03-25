from __future__ import annotations

from pathlib import Path

from app.ui.screen_carom import CaromScreen


def test_carom_screen_validates_local_file_and_mapping(tmp_path: Path, qtbot) -> None:
    file_path = tmp_path / "dados.xlsx"
    file_path.write_bytes(b"x")

    screen = CaromScreen({})
    qtbot.addWidget(screen)
    screen.source_type.setCurrentText("Arquivo local")
    screen.entry_source.setText(str(file_path))
    screen.entry_output.setText(str(tmp_path))
    screen._column_selectors["nome"].addItem("Nome")
    screen._column_selectors["cargo"].addItem("Cargo")
    screen._column_selectors["nome"].setCurrentText("Nome")
    screen._column_selectors["cargo"].setCurrentText("Cargo")

    assert screen._validate_inputs() is True
