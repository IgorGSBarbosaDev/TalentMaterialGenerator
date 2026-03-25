from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import main as app_main


class _FakeEntry:
    def __init__(self) -> None:
        self.insert_calls: list[tuple[int, str]] = []

    def insert(self, index: int, value: str) -> None:
        self.insert_calls.append((index, value))


class _FakeScreen:
    def __init__(self, _master) -> None:
        self.entry_spreadsheet = _FakeEntry()
        self.entry_photos_dir = _FakeEntry()
        self.entry_output_dir = _FakeEntry()
        self.pack = MagicMock()


class _FakeApp:
    def __init__(self) -> None:
        self.title = MagicMock()
        self.geometry = MagicMock()
        self.minsize = MagicMock()
        self.mainloop = MagicMock()


def test_create_app_uses_light_mode_when_config_is_light(monkeypatch) -> None:
    set_mode = MagicMock()
    set_theme = MagicMock()
    fake_app = _FakeApp()

    monkeypatch.setattr(
        app_main,
        "ctk",
        SimpleNamespace(
            set_appearance_mode=set_mode,
            set_default_color_theme=set_theme,
            CTk=lambda: fake_app,
        ),
    )
    monkeypatch.setattr(
        app_main.settings,
        "load_config",
        lambda: {"theme": "light"},
    )
    monkeypatch.setattr(app_main, "FichaScreen", _FakeScreen)

    app = app_main.create_app()

    assert app is fake_app
    set_mode.assert_called_once_with("Light")
    set_theme.assert_called_once_with("green")


def test_create_app_uses_dark_mode_by_default(monkeypatch) -> None:
    set_mode = MagicMock()
    fake_app = _FakeApp()

    monkeypatch.setattr(
        app_main,
        "ctk",
        SimpleNamespace(
            set_appearance_mode=set_mode,
            set_default_color_theme=MagicMock(),
            CTk=lambda: fake_app,
        ),
    )
    monkeypatch.setattr(app_main.settings, "load_config", lambda: {})
    monkeypatch.setattr(app_main, "FichaScreen", _FakeScreen)

    app_main.create_app()

    set_mode.assert_called_once_with("Dark")


def test_create_app_populates_default_paths(monkeypatch) -> None:
    fake_app = _FakeApp()

    monkeypatch.setattr(
        app_main,
        "ctk",
        SimpleNamespace(
            set_appearance_mode=MagicMock(),
            set_default_color_theme=MagicMock(),
            CTk=lambda: fake_app,
        ),
    )
    monkeypatch.setattr(
        app_main.settings,
        "load_config",
        lambda: {
            "theme": "dark",
            "default_spreadsheet_path": "C:/dados/planilha.xlsx",
            "default_photos_dir": "C:/dados/fotos",
            "default_output_dir": "C:/saida",
        },
    )

    holder: dict[str, _FakeScreen] = {}

    class _CaptureScreen(_FakeScreen):
        def __init__(self, master) -> None:
            super().__init__(master)
            holder["screen"] = self

    monkeypatch.setattr(app_main, "FichaScreen", _CaptureScreen)

    app_main.create_app()

    screen = holder["screen"]
    assert screen.entry_spreadsheet.insert_calls == [(0, "C:/dados/planilha.xlsx")]
    assert screen.entry_photos_dir.insert_calls == [(0, "C:/dados/fotos")]
    assert screen.entry_output_dir.insert_calls == [(0, "C:/saida")]


def test_main_returns_zero_when_mainloop_finishes(monkeypatch) -> None:
    fake_app = _FakeApp()
    monkeypatch.setattr(app_main, "create_app", lambda: fake_app)

    result = app_main.main()

    assert result == 0
    fake_app.mainloop.assert_called_once()


def test_main_returns_one_when_create_app_raises(monkeypatch) -> None:
    def _raise() -> _FakeApp:
        raise RuntimeError("boom")

    monkeypatch.setattr(app_main, "create_app", _raise)

    result = app_main.main()

    assert result == 1
