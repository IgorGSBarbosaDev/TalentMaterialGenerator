from __future__ import annotations

from pathlib import Path

import pytest

from app.core import reader


def _fixture_path(filename: str) -> Path:
    return Path(__file__).resolve().parents[2] / "fixtures" / filename


def test_read_spreadsheet_returns_rows() -> None:
    rows = reader.read_spreadsheet(str(_fixture_path("colaboradores_sample.xlsx")))

    assert len(rows) == 3
    assert "nome" in rows[0]


def test_detect_columns_maps_known_headers() -> None:
    mapping = reader.detect_columns(["Nome", "Função", "Área"])

    assert mapping["nome"] == "Nome"
    assert mapping["cargo"] == "Função"
    assert mapping["area"] == "Área"


def test_validate_required_columns_returns_missing_fields() -> None:
    missing = reader.validate_required_columns({"nome": None, "cargo": "Cargo"})

    assert missing == ["nome"]


def test_parse_multiline_field_splits_semicolon_and_newline() -> None:
    assert reader.parse_multiline_field("A;B\nC") == ["A", "B", "C"]


def test_normalize_filename_removes_accents() -> None:
    assert reader.normalize_filename("João Silva") == "Joao_Silva"


def test_resolve_local_spreadsheet_source_returns_local_file(tmp_path: Path) -> None:
    path = tmp_path / "file.xlsx"
    path.write_bytes(b"x")

    result = reader.resolve_spreadsheet_source(str(path))

    assert result.source_kind == "local"
    assert result.path == str(path)


def test_convert_onedrive_link_adds_download_flag() -> None:
    converted = reader.convert_onedrive_link("https://example.com/file.xlsx")

    assert "download=1" in converted


def test_resolve_remote_source_uses_recent_cache(monkeypatch, tmp_path: Path) -> None:
    url = "https://example.com/data.xlsx"
    cache_path = tmp_path / "cache.xlsx"
    cache_path.write_bytes(b"cached")

    monkeypatch.setattr(reader, "get_cache_file_path", lambda _url: cache_path)

    result = reader.resolve_spreadsheet_source(url, cache_enabled=True)

    assert result.used_cache is True
    assert result.path == str(cache_path)


def test_resolve_remote_source_downloads_when_cache_expired(monkeypatch, tmp_path: Path) -> None:
    url = "https://example.com/data.xlsx"
    cache_path = tmp_path / "cache.xlsx"
    content = b"new"

    monkeypatch.setattr(reader, "get_cache_file_path", lambda _url: cache_path)
    monkeypatch.setattr(reader, "cache_is_fresh", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(reader, "download_spreadsheet", lambda *_args, **_kwargs: content)

    result = reader.resolve_spreadsheet_source(url, cache_enabled=True)

    assert result.used_cache is False
    assert cache_path.read_bytes() == content


def test_resolve_remote_source_falls_back_to_existing_cache_on_error(
    monkeypatch, tmp_path: Path
) -> None:
    url = "https://example.com/data.xlsx"
    cache_path = tmp_path / "cache.xlsx"
    cache_path.write_bytes(b"cached")

    monkeypatch.setattr(reader, "get_cache_file_path", lambda _url: cache_path)
    monkeypatch.setattr(reader, "cache_is_fresh", lambda *_args, **_kwargs: False)

    def _raise(*_args, **_kwargs):
        raise RuntimeError("network")

    monkeypatch.setattr(reader, "download_spreadsheet", _raise)

    result = reader.resolve_spreadsheet_source(url, cache_enabled=True)

    assert result.used_cache is True
    assert "usando cache local" in result.message.lower()


def test_remap_rows_returns_normalized_field_names() -> None:
    rows = [{"Nome": "Ana", "Cargo": "Analista"}]
    mapping = {"nome": "Nome", "cargo": "Cargo", "idade": None}

    result = reader.remap_rows(rows, mapping)

    assert result == [{"nome": "Ana", "cargo": "Analista", "idade": ""}]
