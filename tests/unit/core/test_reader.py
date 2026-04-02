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
    mapping = reader.detect_columns(["Matricula", "Nome", "Funcao", "Area"])

    assert mapping["matricula"] == "Matricula"
    assert mapping["nome"] == "Nome"
    assert mapping["cargo"] == "Funcao"
    assert mapping["area"] == "Area"


def test_detect_columns_maps_annual_note_headers() -> None:
    mapping = reader.detect_columns(["Nota 2025", "Nota 2024", "Nota 2023"])

    assert mapping["nota_2025"] == "Nota 2025"
    assert mapping["nota_2024"] == "Nota 2024"
    assert mapping["nota_2023"] == "Nota 2023"


def test_validate_required_columns_returns_missing_fields() -> None:
    missing = reader.validate_required_columns({"nome": None, "cargo": "Cargo"})

    assert missing == ["nome"]


def test_validate_required_columns_does_not_require_matricula() -> None:
    missing = reader.validate_required_columns(
        {"matricula": None, "nome": "Nome", "cargo": "Cargo"}
    )

    assert missing == []


def test_validate_ficha_required_columns_uses_standardized_contract() -> None:
    missing = reader.validate_ficha_required_columns(
        {"matricula": None, "nome": "Nome", "cargo": None}
    )

    assert missing == ["matricula", "cargo"]


def test_validate_standardized_ficha_schema_requires_matricula_nome_and_cargo() -> None:
    with pytest.raises(ValueError, match="Colunas ausentes: matricula"):
        reader.validate_standardized_ficha_schema(["Nome", "Cargo"])


def test_parse_multiline_field_splits_semicolon_and_newline() -> None:
    assert reader.parse_multiline_field("A;B\nC") == ["A", "B", "C"]


def test_normalize_filename_removes_accents() -> None:
    assert reader.normalize_filename("Joao Silva") == "Joao_Silva"


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


def test_resolve_remote_source_downloads_when_cache_expired(
    monkeypatch, tmp_path: Path
) -> None:
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


def test_remap_ficha_row_returns_ficha_only_fields() -> None:
    row = {
        "Matricula": "123",
        "Nome": "Ana",
        "Cargo": "Analista",
        "Resumo": "Perfil",
        "Performance": "Legado",
    }
    mapping = {
        "matricula": "Matricula",
        "nome": "Nome",
        "cargo": "Cargo",
        "resumo_perfil": "Resumo",
        "performance": "Performance",
    }

    result = reader.remap_ficha_row(row, mapping)

    assert result["matricula"] == "123"
    assert result["nome"] == "Ana"
    assert "performance" not in result


def test_load_standardized_ficha_rows_uses_detected_headers() -> None:
    rows = [
        {
            "Matricula": "123",
            "Nome": "Ana",
            "Cargo": "Analista",
            "Resumo": "Perfil",
        }
    ]

    result = reader.load_standardized_ficha_rows(rows)

    assert result[0]["matricula"] == "123"
    assert result[0]["nome"] == "Ana"


def test_validate_ficha_employee_requires_nome_and_cargo() -> None:
    employee = {
        "matricula": "",
        "nome": "",
        "idade": "",
        "cargo": "",
        "antiguidade": "",
        "formacao": "",
        "resumo_perfil": "",
        "trajetoria": "",
    }

    assert reader.validate_ficha_employee(employee) == ["matricula", "nome", "cargo"]


def test_lookup_ficha_employees_matches_partial_name_case_and_accents() -> None:
    rows = [
        {"Nome": "Ana Maria", "Cargo": "Analista", "Matricula": "123"},
        {"Nome": "Carlos", "Cargo": "Coordenador", "Matricula": "456"},
    ]

    result = reader.lookup_ficha_employees(rows, name_query="mari")

    assert len(result) == 1
    assert result[0]["nome"] == "Ana Maria"


def test_lookup_ficha_employees_blocks_duplicate_matricula() -> None:
    rows = [
        {"Nome": "Ana", "Cargo": "Analista", "Matricula": "123"},
        {"Nome": "Ana B", "Cargo": "Analista", "Matricula": "123"},
    ]

    with pytest.raises(ValueError, match="mais de um colaborador"):
        reader.lookup_ficha_employees(rows, matricula_query="123")


def test_lookup_ficha_employees_rejects_empty_search() -> None:
    rows = [{"Matricula": "123", "Nome": "Ana", "Cargo": "Analista"}]

    with pytest.raises(ValueError, match="Informe nome ou matricula"):
        reader.lookup_ficha_employees(rows)


def test_lookup_ficha_employees_blocks_when_schema_missing_matricula() -> None:
    rows = [{"Nome": "Ana", "Cargo": "Analista"}]

    with pytest.raises(ValueError, match="schema padrao da ficha"):
        reader.lookup_ficha_employees(rows, name_query="ana")


def test_remap_rows_builds_performance_from_annual_notes() -> None:
    rows = [
        {
            "Matricula": "123",
            "Nome": "Ana",
            "Cargo": "Analista",
            "Nota 2025": "3/PROM",
            "Nota 2024": "5/MN+",
            "Nota 2023": "4/AP",
        }
    ]
    mapping = {
        "matricula": "Matricula",
        "nome": "Nome",
        "cargo": "Cargo",
        "nota_2025": "Nota 2025",
        "nota_2024": "Nota 2024",
        "nota_2023": "Nota 2023",
        "performance": None,
    }

    result = reader.remap_rows(rows, mapping)

    assert result[0]["matricula"] == "123"
    assert result[0]["performance"] == "2025 - 3/PROM\n2024 - 5/MN+\n2023 - 4/AP"


def test_remap_rows_uses_available_annual_notes_only() -> None:
    rows = [{"Nome": "Ana", "Cargo": "Analista", "Nota 2024": "5/MN+"}]
    mapping = {
        "nome": "Nome",
        "cargo": "Cargo",
        "nota_2025": None,
        "nota_2024": "Nota 2024",
        "nota_2023": None,
        "performance": None,
    }

    result = reader.remap_rows(rows, mapping)

    assert result[0]["performance"] == "2024 - 5/MN+"


def test_remap_rows_preserves_direct_performance_when_annual_notes_absent() -> None:
    rows = [{"Nome": "Ana", "Cargo": "Analista", "Performance": "Historico legado"}]
    mapping = {
        "nome": "Nome",
        "cargo": "Cargo",
        "nota_2025": None,
        "nota_2024": None,
        "nota_2023": None,
        "performance": "Performance",
    }

    result = reader.remap_rows(rows, mapping)

    assert result[0]["performance"] == "Historico legado"
