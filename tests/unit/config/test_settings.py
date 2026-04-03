from __future__ import annotations

import json

from app.config import settings


def test_load_config_returns_defaults_when_missing(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    monkeypatch.setattr(settings, "get_config_path", lambda: config_path)
    monkeypatch.setattr(settings, "get_repo_default_spreadsheet_path", lambda: None)

    assert settings.load_config() == {
        **settings.DEFAULT_CONFIG,
        "default_output_dir": str(settings.get_default_output_dir()),
    }


def test_save_and_load_round_trip(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    monkeypatch.setattr(settings, "get_config_path", lambda: config_path)
    monkeypatch.setattr(settings, "get_repo_default_spreadsheet_path", lambda: None)
    payload = {**settings.DEFAULT_CONFIG, "theme": "light", "cache_ttl_hours": 12}

    settings.save_config(payload)

    expected = {
        **payload,
        "default_output_dir": str(settings.get_default_output_dir()),
    }
    assert json.loads(config_path.read_text(encoding="utf-8")) == expected
    assert settings.load_config() == expected


def test_reset_to_defaults_returns_default_config(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    monkeypatch.setattr(settings, "get_config_path", lambda: config_path)
    monkeypatch.setattr(settings, "get_repo_default_spreadsheet_path", lambda: None)

    assert settings.reset_to_defaults() == {
        **settings.DEFAULT_CONFIG,
        "default_output_dir": str(settings.get_default_output_dir()),
    }


def test_get_cache_dir_uses_app_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "get_app_dir", lambda: tmp_path / "USIGenerator")

    assert settings.get_cache_dir() == tmp_path / "USIGenerator" / "cache"


def test_load_config_ignores_legacy_output_dir(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    monkeypatch.setattr(settings, "get_config_path", lambda: config_path)
    monkeypatch.setattr(settings, "get_repo_default_spreadsheet_path", lambda: None)
    config_path.write_text(
        json.dumps({"default_output_dir": "C:/legado", "theme": "light"}),
        encoding="utf-8",
    )

    loaded = settings.load_config()

    assert loaded["theme"] == "light"
    assert loaded["default_output_dir"] == str(settings.get_default_output_dir())


def test_load_config_uses_repo_default_spreadsheet_when_available(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    spreadsheet = tmp_path / "PlanilhaTeste.xlsx"
    spreadsheet.write_bytes(b"x")
    monkeypatch.setattr(settings, "get_config_path", lambda: config_path)
    monkeypatch.setattr(settings, "get_repo_default_spreadsheet_path", lambda: spreadsheet)

    loaded = settings.load_config()

    assert loaded["default_spreadsheet_path"] == str(spreadsheet)
    assert loaded["spreadsheet_source"] == "local"
