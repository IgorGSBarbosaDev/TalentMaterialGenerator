from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import Workbook

from app.config import settings
from app.core import base_cache


def _build_valid_base(path: Path, *, extra_rows: int = 1) -> Path:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.append(["Matricula", "Nome", "Cargo"])
    for index in range(extra_rows):
        sheet.append([str(100 + index), f"Colab {index}", "Analista"])
    workbook.save(path)
    return path


def test_update_default_base_caches_valid_file_and_stores_metadata(
    tmp_path: Path, monkeypatch
) -> None:
    config_path = tmp_path / "config.json"
    cache_dir = tmp_path / "cache"
    spreadsheet = _build_valid_base(tmp_path / "base.xlsx", extra_rows=2)
    monkeypatch.setattr(settings, "get_config_path", lambda: config_path)
    monkeypatch.setattr(settings, "get_cache_dir", lambda: cache_dir)
    monkeypatch.setattr(settings, "get_repo_default_spreadsheet_path", lambda: None)

    result = base_cache.update_default_base_from_file(str(spreadsheet))

    loaded = settings.load_config()
    cached_path = Path(loaded["default_base_cache_path"])
    assert result.status == "updated"
    assert loaded["default_spreadsheet_path"] == str(spreadsheet)
    assert loaded["default_spreadsheet_name"] == "base.xlsx"
    assert loaded["default_spreadsheet_size"] == spreadsheet.stat().st_size
    assert loaded["default_base_row_count"] == 2
    assert cached_path == cache_dir / "default_base.xlsx"
    assert cached_path.read_bytes() == spreadsheet.read_bytes()


def test_refresh_default_base_skips_unchanged_file(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    cache_dir = tmp_path / "cache"
    spreadsheet = _build_valid_base(tmp_path / "base.xlsx")
    monkeypatch.setattr(settings, "get_config_path", lambda: config_path)
    monkeypatch.setattr(settings, "get_cache_dir", lambda: cache_dir)
    monkeypatch.setattr(settings, "get_repo_default_spreadsheet_path", lambda: None)
    base_cache.update_default_base_from_file(str(spreadsheet))

    result = base_cache.refresh_default_base(settings.load_config())

    assert result.status == "unchanged"
    assert "ja esta atualizada" in result.message.lower()


def test_refresh_default_base_reports_missing_file_and_preserves_cache(
    tmp_path: Path, monkeypatch
) -> None:
    config_path = tmp_path / "config.json"
    cache_dir = tmp_path / "cache"
    spreadsheet = _build_valid_base(tmp_path / "base.xlsx")
    monkeypatch.setattr(settings, "get_config_path", lambda: config_path)
    monkeypatch.setattr(settings, "get_cache_dir", lambda: cache_dir)
    monkeypatch.setattr(settings, "get_repo_default_spreadsheet_path", lambda: None)
    base_cache.update_default_base_from_file(str(spreadsheet))
    cached_path = Path(settings.load_config()["default_base_cache_path"])
    before = cached_path.read_bytes()
    spreadsheet.unlink()

    result = base_cache.refresh_default_base(settings.load_config())

    assert result.status == "missing"
    assert cached_path.read_bytes() == before
    assert settings.load_config()["default_base_cache_path"] == str(cached_path)


def test_invalid_spreadsheet_does_not_replace_last_valid_cache(
    tmp_path: Path, monkeypatch
) -> None:
    config_path = tmp_path / "config.json"
    cache_dir = tmp_path / "cache"
    valid = _build_valid_base(tmp_path / "valid.xlsx")
    invalid = tmp_path / "invalid.xlsx"
    invalid.write_bytes(b"not a workbook")
    monkeypatch.setattr(settings, "get_config_path", lambda: config_path)
    monkeypatch.setattr(settings, "get_cache_dir", lambda: cache_dir)
    monkeypatch.setattr(settings, "get_repo_default_spreadsheet_path", lambda: None)
    base_cache.update_default_base_from_file(str(valid))
    cached_path = Path(settings.load_config()["default_base_cache_path"])
    before = cached_path.read_bytes()

    with pytest.raises(base_cache.BaseCacheError):
        base_cache.update_default_base_from_file(str(invalid))

    loaded = settings.load_config()
    assert loaded["default_spreadsheet_path"] == str(valid)
    assert cached_path.read_bytes() == before
