from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from app.ui.screen_ficha import FichaScreen


def _build_screen() -> FichaScreen:
    screen = FichaScreen.__new__(FichaScreen)
    screen.entry_spreadsheet = MagicMock()
    screen.entry_photos_dir = MagicMock()
    screen.entry_output_dir = MagicMock()
    screen.btn_gerar = MagicMock()
    screen.after = MagicMock()
    screen.column_mapping = {"nome": "Nome"}
    screen.var_include_photo = MagicMock()
    screen.var_include_photo.get.return_value = True
    screen.var_gerar_pdf = MagicMock()
    screen.var_gerar_pdf.get.return_value = False
    return screen


def test_validate_inputs_returns_false_when_spreadsheet_empty(tmp_path: Path) -> None:
    screen = _build_screen()
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()

    screen.entry_spreadsheet.get.return_value = ""
    screen.entry_photos_dir.get.return_value = str(photos_dir)

    assert screen._validate_inputs() is False


def test_validate_inputs_returns_false_when_photos_dir_empty(tmp_path: Path) -> None:
    screen = _build_screen()
    spreadsheet = tmp_path / "colaboradores.xlsx"
    spreadsheet.write_text("placeholder")

    screen.entry_spreadsheet.get.return_value = str(spreadsheet)
    screen.entry_photos_dir.get.return_value = ""

    assert screen._validate_inputs() is False


def test_validate_inputs_returns_false_when_spreadsheet_file_not_found(
    tmp_path: Path,
) -> None:
    screen = _build_screen()
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()

    screen.entry_spreadsheet.get.return_value = str(tmp_path / "inexistente.xlsx")
    screen.entry_photos_dir.get.return_value = str(photos_dir)

    assert screen._validate_inputs() is False


def test_validate_inputs_returns_true_when_both_valid_paths_provided(
    tmp_path: Path,
) -> None:
    screen = _build_screen()
    spreadsheet = tmp_path / "colaboradores.xlsx"
    spreadsheet.write_text("placeholder")
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()

    screen.entry_spreadsheet.get.return_value = str(spreadsheet)
    screen.entry_photos_dir.get.return_value = str(photos_dir)

    assert screen._validate_inputs() is True


def test_get_config_returns_dict_with_key_spreadsheet_path() -> None:
    screen = _build_screen()
    screen.entry_spreadsheet.get.return_value = "C:/dados/colaboradores.xlsx"
    screen.entry_photos_dir.get.return_value = "C:/dados/fotos"
    screen.entry_output_dir.get.return_value = "C:/saida"

    config = screen._get_config()

    assert "spreadsheet_path" in config


def test_get_config_returns_dict_with_key_photos_dir() -> None:
    screen = _build_screen()
    screen.entry_spreadsheet.get.return_value = "C:/dados/colaboradores.xlsx"
    screen.entry_photos_dir.get.return_value = "C:/dados/fotos"
    screen.entry_output_dir.get.return_value = "C:/saida"

    config = screen._get_config()

    assert "photos_dir" in config


def test_get_config_returns_dict_with_key_output_dir() -> None:
    screen = _build_screen()
    screen.entry_spreadsheet.get.return_value = "C:/dados/colaboradores.xlsx"
    screen.entry_photos_dir.get.return_value = "C:/dados/fotos"
    screen.entry_output_dir.get.return_value = "C:/saida"

    config = screen._get_config()

    assert "output_dir" in config


def test_get_config_returns_dict_with_key_column_mapping() -> None:
    screen = _build_screen()
    screen.entry_spreadsheet.get.return_value = "C:/dados/colaboradores.xlsx"
    screen.entry_photos_dir.get.return_value = "C:/dados/fotos"
    screen.entry_output_dir.get.return_value = "C:/saida"

    config = screen._get_config()

    assert "column_mapping" in config


def test_get_config_returns_dict_with_key_include_photo_bool() -> None:
    screen = _build_screen()
    screen.entry_spreadsheet.get.return_value = "C:/dados/colaboradores.xlsx"
    screen.entry_photos_dir.get.return_value = "C:/dados/fotos"
    screen.entry_output_dir.get.return_value = "C:/saida"

    config = screen._get_config()

    assert "include_photo" in config
    assert isinstance(config["include_photo"], bool)


def test_get_config_returns_dict_with_key_gerar_pdf_bool() -> None:
    screen = _build_screen()
    screen.entry_spreadsheet.get.return_value = "C:/dados/colaboradores.xlsx"
    screen.entry_photos_dir.get.return_value = "C:/dados/fotos"
    screen.entry_output_dir.get.return_value = "C:/saida"

    config = screen._get_config()

    assert "gerar_pdf" in config
    assert isinstance(config["gerar_pdf"], bool)


def test_auto_detect_columns_calls_reader_detect_columns(
    tmp_path: Path,
    monkeypatch,
) -> None:
    screen = _build_screen()
    spreadsheet = tmp_path / "colaboradores.xlsx"
    spreadsheet.write_text("placeholder")
    screen.entry_spreadsheet.get.return_value = str(spreadsheet)

    monkeypatch.setattr(
        "app.ui.screen_ficha.reader.read_spreadsheet",
        lambda _path: [{"Nome": "Ana"}],
    )
    detect_mock = MagicMock(return_value={"nome": "Nome"})
    monkeypatch.setattr("app.ui.screen_ficha.reader.detect_columns", detect_mock)

    screen._auto_detect_columns()

    detect_mock.assert_called_once_with(["Nome"])


def test_start_generation_disables_btn_gerar(monkeypatch) -> None:
    screen = _build_screen()
    screen._validate_inputs = MagicMock(return_value=True)
    screen._get_config = MagicMock(
        return_value={
            "spreadsheet_path": "C:/dados/colaboradores.xlsx",
            "photos_dir": "C:/dados/fotos",
            "output_dir": "C:/saida",
            "column_mapping": {},
            "include_photo": True,
            "gerar_pdf": False,
        }
    )

    thread_instance = MagicMock()
    thread_cls = MagicMock(return_value=thread_instance)
    monkeypatch.setattr("app.ui.screen_ficha.threading.Thread", thread_cls)

    screen._start_generation()

    screen.btn_gerar.configure.assert_any_call(state="disabled")
    thread_cls.assert_called_once()
    thread_instance.start.assert_called_once()


def test_start_generation_does_not_start_when_inputs_invalid(monkeypatch) -> None:
    screen = _build_screen()
    screen._validate_inputs = MagicMock(return_value=False)

    thread_cls = MagicMock()
    monkeypatch.setattr("app.ui.screen_ficha.threading.Thread", thread_cls)

    screen._start_generation()

    thread_cls.assert_not_called()
