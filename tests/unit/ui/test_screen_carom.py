from __future__ import annotations

from pathlib import Path
from uuid import uuid4

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


def test_carom_screen_exposes_new_schema_fields(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)

    for field in ("matricula", "nota_2025", "nota_2024", "nota_2023"):
        assert field in screen._column_selectors


def test_carom_screen_refreshes_preview_when_layout_changes(qtbot) -> None:
    screen = CaromScreen({})
    qtbot.addWidget(screen)
    screen._preview_rows = [
        {
            "Nome Coluna": "Marina Souza",
            "Cargo Coluna": "Especialista",
            "Nota Coluna": "4.8",
            "Potencial Coluna": "Alto",
        }
    ]
    for field, header in (
        ("nome", "Nome Coluna"),
        ("cargo", "Cargo Coluna"),
        ("nota", "Nota Coluna"),
        ("potencial", "Potencial Coluna"),
    ):
        screen._column_selectors[field].addItem(header)
        screen._column_selectors[field].setCurrentText(header)

    screen.columns.setCurrentText("3")
    screen.title_field.setText("Carometro Lideranca")
    screen._refresh_preview()

    assert screen.preview_header.text() == "Carometro Lideranca"
    assert screen.layout_badge.text() == "3 colunas"
