from __future__ import annotations

from pathlib import Path
from uuid import uuid4

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


def test_ficha_screen_exposes_new_schema_fields(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)

    for field in ("matricula", "nota_2025", "nota_2024", "nota_2023", "performance"):
        assert field in screen._column_selectors


def test_ficha_screen_refreshes_preview_from_selected_mapping(qtbot) -> None:
    screen = FichaScreen({})
    qtbot.addWidget(screen)
    screen._preview_rows = [
        {
            "Nome Coluna": "Marina Souza",
            "Cargo Coluna": "Especialista de Desenvolvimento",
            "Resumo": "Atua na consolidacao de trilhas de aprendizagem.",
        }
    ]
    for field, header in (
        ("nome", "Nome Coluna"),
        ("cargo", "Cargo Coluna"),
        ("resumo_perfil", "Resumo"),
    ):
        screen._column_selectors[field].addItem(header)
        screen._column_selectors[field].setCurrentText(header)

    screen._refresh_preview()

    assert screen.preview_name.text() == "Marina Souza"
    assert "Especialista" in screen.preview_role.text()
    assert "aprendizagem" in screen.preview_summary.text()
