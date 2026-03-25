from __future__ import annotations

import json

from app.config import settings


def test_load_config_returns_defaults_when_missing(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    monkeypatch.setattr(settings, "get_config_path", lambda: config_path)

    assert settings.load_config() == settings.DEFAULT_CONFIG


def test_save_and_load_round_trip(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    monkeypatch.setattr(settings, "get_config_path", lambda: config_path)
    payload = {**settings.DEFAULT_CONFIG, "theme": "light", "cache_ttl_hours": 12}

    settings.save_config(payload)

    assert json.loads(config_path.read_text(encoding="utf-8")) == payload
    assert settings.load_config() == payload


def test_reset_to_defaults_returns_default_config(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    monkeypatch.setattr(settings, "get_config_path", lambda: config_path)

    assert settings.reset_to_defaults() == settings.DEFAULT_CONFIG


def test_get_cache_dir_uses_app_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "get_app_dir", lambda: tmp_path / "USIGenerator")

    assert settings.get_cache_dir() == tmp_path / "USIGenerator" / "cache"
