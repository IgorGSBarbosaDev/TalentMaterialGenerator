import importlib
import json
from pathlib import Path

import pytest

REQUIRED_KEYS = {
    "theme",
    "default_spreadsheet_path",
    "default_photos_dir",
    "default_output_dir",
    "default_format",
    "default_carom_columns",
    "last_generations",
}


def _load_settings_module():
    try:
        return importlib.import_module("app.config.settings")
    except ModuleNotFoundError as exc:
        pytest.fail(f"Settings module not found: {exc}")


def test_load_config_returns_default_when_file_missing(tmp_path):
    settings = _load_settings_module()
    config_file = tmp_path / "config.json"
    assert not config_file.exists()

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(settings, "get_config_path", lambda: config_file)
        config = settings.load_config()

    assert config == settings.DEFAULT_CONFIG


def test_load_config_returns_dict_with_all_required_keys(tmp_path):
    settings = _load_settings_module()
    config_file = tmp_path / "config.json"

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(settings, "get_config_path", lambda: config_file)
        config = settings.load_config()

    assert isinstance(config, dict)
    assert REQUIRED_KEYS.issubset(config.keys())


def test_load_config_reads_existing_json_correctly(tmp_path):
    settings = _load_settings_module()
    config_file = tmp_path / "config.json"
    payload = {
        "theme": "light",
        "default_spreadsheet_path": "C:/input/data.xlsx",
        "default_photos_dir": "C:/photos",
        "default_output_dir": "C:/output",
        "default_format": "pdf",
        "default_carom_columns": 6,
        "last_generations": ["2026-03-10"],
    }
    config_file.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(settings, "get_config_path", lambda: config_file)
        config = settings.load_config()

    assert config == payload


def test_save_config_creates_file_at_correct_path(tmp_path):
    settings = _load_settings_module()
    config_file = tmp_path / "nested" / "config.json"
    assert not config_file.exists()

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(settings, "get_config_path", lambda: config_file)
        settings.save_config(settings.DEFAULT_CONFIG)

    assert config_file.exists()


def test_save_config_writes_valid_json(tmp_path):
    settings = _load_settings_module()
    config_file = tmp_path / "config.json"
    payload = {
        "theme": "light",
        "default_spreadsheet_path": "",
        "default_photos_dir": "",
        "default_output_dir": "",
        "default_format": "pptx",
        "default_carom_columns": 5,
        "last_generations": [],
    }

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(settings, "get_config_path", lambda: config_file)
        settings.save_config(payload)

    loaded = json.loads(config_file.read_text(encoding="utf-8"))
    assert loaded == payload


def test_reset_to_defaults_overwrites_with_default_config(tmp_path):
    settings = _load_settings_module()
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"theme": "light"}), encoding="utf-8")

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(settings, "get_config_path", lambda: config_file)
        settings.reset_to_defaults()

    loaded = json.loads(config_file.read_text(encoding="utf-8"))
    assert loaded == settings.DEFAULT_CONFIG


def test_get_config_path_contains_appdata_and_usiogenerator(tmp_path):
    settings = _load_settings_module()

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv("APPDATA", str(tmp_path))
        config_path = settings.get_config_path()

    expected = tmp_path / "USIGenerator" / "config.json"
    assert isinstance(config_path, Path)
    assert config_path == expected
