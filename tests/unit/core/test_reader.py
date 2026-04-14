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


def test_detect_columns_maps_all_ceo_headers_from_new_spreadsheet() -> None:
    mapping = reader.detect_columns(["CEO1", "CEO2", "CEO3", "CEO4"])

    assert mapping["ceo1"] == "CEO1"
    assert mapping["ceo2"] == "CEO2"
    assert mapping["ceo3"] == "CEO3"
    assert mapping["ceo4"] == "CEO4"


def test_resolve_ficha_schema_maps_new_evaluation_layout_without_ambiguity() -> None:
    schema = reader.resolve_ficha_schema(
        [
            "Matricula",
            "Nome",
            "Cargo",
            "Avaliação 2025",
            "Nota 2025",
            "Potencial 2025",
            "Avaliação 2024",
            "Nota 2024",
            "Potencial 2024",
        ]
    )

    assert schema["avaliacao_2025"] == "Avaliação 2025"
    assert schema["score_2025"] == "Nota 2025"
    assert schema["potencial_2025"] == "Potencial 2025"
    assert schema["nota_2025"] is None
    assert schema["avaliacao_2024"] == "Avaliação 2024"
    assert schema["score_2024"] == "Nota 2024"
    assert schema["potencial_2024"] == "Potencial 2024"


def test_detect_columns_maps_resumo_do_perfil_header() -> None:
    mapping = reader.detect_columns(["Resumo do perfil"])

    assert mapping["resumo_perfil"] == "Resumo do perfil"


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


def test_validate_carom_required_columns_uses_standardized_contract() -> None:
    missing = reader.validate_carom_required_columns(
        {"matricula": None, "nome": "Nome", "cargo": None}
    )

    assert missing == ["matricula", "cargo"]


def test_validate_standardized_ficha_schema_requires_matricula_nome_and_cargo() -> None:
    with pytest.raises(ValueError, match="Colunas ausentes: matricula"):
        reader.validate_standardized_ficha_schema(["Nome", "Cargo"])


def test_validate_standardized_carom_schema_requires_matricula_nome_and_cargo() -> None:
    with pytest.raises(ValueError, match="Colunas ausentes: matricula"):
        reader.validate_standardized_carom_schema(["Nome", "Cargo"])


def test_has_expected_ficha_column_order_accepts_planilha_teste_contract() -> None:
    headers = [
        "Matricula",
        "Nome",
        "Idade",
        "Cargo",
        "Antiguidade",
        "Formacao",
        "Resumo do perfil",
        "Trajetoria",
        "Nota 2025",
        "Nota 2024",
        "Nota 2023",
    ]

    assert reader.has_expected_ficha_column_order(headers) is True


def test_has_expected_ficha_column_order_accepts_new_reference_contract() -> None:
    headers = [
        "Matricula",
        "Nome",
        "Cargo",
        "Idade",
        "Antiguidade",
        "Formacao",
        "Resumo do perfil",
        "Trajetoria",
        "Avaliação 2025",
        "Avaliação 2024",
        "Avaliação 2023",
        "Nota 2025",
        "Potencial 2025",
        "Nota 2024",
        "Potencial 2024",
        "Nota 2023",
        "Potencial 2023",
    ]

    assert reader.has_expected_ficha_column_order(headers) is True


def test_has_expected_ficha_column_order_accepts_new_reference_contract_with_ceos() -> None:
    headers = [
        "Matricula",
        "Nome",
        "Cargo",
        "Idade",
        "Antiguidade",
        "Formacao",
        "Resumo do perfil",
        "Trajetoria",
        "Avaliação 2025",
        "Avaliação 2024",
        "Avaliação 2023",
        "Nota 2025",
        "Potencial 2025",
        "Nota 2024",
        "Potencial 2024",
        "Nota 2023",
        "Potencial 2023",
        "CEO1",
        "CEO2",
        "CEO3",
        "CEO4",
    ]

    assert reader.has_expected_ficha_column_order(headers) is True


def test_has_expected_ficha_column_order_rejects_different_order() -> None:
    headers = [
        "Nome",
        "Matricula",
        "Idade",
        "Cargo",
        "Antiguidade",
        "Formacao",
        "Resumo do perfil",
        "Trajetoria",
        "Nota 2025",
        "Nota 2024",
        "Nota 2023",
    ]

    assert reader.has_expected_ficha_column_order(headers) is False


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


def test_load_standardized_ficha_rows_preserves_annual_notes() -> None:
    rows = [
        {
            "Matricula": "123",
            "Nome": "Ana",
            "Cargo": "Analista",
            "Nota 2025": "2 / MN-",
            "Nota 2024": "5 / AP",
            "Nota 2023": "",
        }
    ]

    result = reader.load_standardized_ficha_rows(rows)

    assert result[0]["nota_2025"] == "2 / MN-"
    assert result[0]["nota_2024"] == "5 / AP"
    assert result[0]["nota_2023"] == ""
    assert result[0]["score_2025"] == ""
    assert result[0]["potencial_2025"] == ""


def test_load_standardized_ficha_rows_prefers_consolidated_evaluations() -> None:
    rows = [
        {
            "Matricula": "123",
            "Nome": "Ana",
            "Cargo": "Analista",
            "Avaliação 2025": "5 /  AP",
            "Nota 2025": "4",
            "Potencial 2025": "PROM",
            "Avaliação 2024": "3 / MN+",
            "Nota 2024": "3",
            "Potencial 2024": "MN+",
        }
    ]

    result = reader.load_standardized_ficha_rows(rows)

    assert result[0]["avaliacao_2025"] == "5 / AP"
    assert result[0]["score_2025"] == "4"
    assert result[0]["potencial_2025"] == "PROM"
    assert result[0]["nota_2025"] == "5 / AP"
    assert result[0]["nota_2024"] == "3 / MN+"


def test_load_standardized_ficha_rows_falls_back_to_score_and_potential_when_needed() -> None:
    rows = [
        {
            "Matricula": "123",
            "Nome": "Ana",
            "Cargo": "Analista",
            "Avaliação 2025": "",
            "Nota 2025": "4",
            "Potencial 2025": "PROM",
            "Avaliação 2024": "",
            "Nota 2024": "",
            "Potencial 2024": "MN+",
            "Avaliação 2023": "",
            "Nota 2023": "5",
            "Potencial 2023": "",
        }
    ]

    result = reader.load_standardized_ficha_rows(rows)

    assert result[0]["nota_2025"] == "4 / PROM"
    assert result[0]["nota_2024"] == "MN+"
    assert result[0]["nota_2023"] == "5"


def test_load_standardized_ficha_rows_treats_na_values_as_missing() -> None:
    rows = [
        {
            "Matricula": "123",
            "Nome": "Ana",
            "Cargo": "Analista",
            "Avaliação 2025": "#N/A",
            "Nota 2025": "#N/A",
            "Potencial 2025": "#N/A",
            "Avaliação 2024": "#N/A",
            "Nota 2024": "4",
            "Potencial 2024": "AP",
        }
    ]

    result = reader.load_standardized_ficha_rows(rows)

    assert result[0]["nota_2025"] == ""
    assert result[0]["avaliacao_2025"] == ""
    assert result[0]["score_2025"] == ""
    assert result[0]["potencial_2025"] == ""
    assert result[0]["nota_2024"] == "4 / AP"


def test_load_standardized_ficha_rows_ignores_appended_ceo_columns() -> None:
    rows = [
        {
            "Matricula": "123",
            "Nome": "Ana",
            "Cargo": "Analista",
            "Avaliação 2025": "5 / AP",
            "Avaliação 2024": "",
            "Avaliação 2023": "",
            "Nota 2025": "5",
            "Potencial 2025": "AP",
            "Nota 2024": "",
            "Potencial 2024": "",
            "Nota 2023": "",
            "Potencial 2023": "",
            "CEO1": "Diretoria",
            "CEO2": "VP",
            "CEO3": "Sucessor Imediato",
            "CEO4": "Em desenvolvimento",
        }
    ]

    result = reader.load_standardized_ficha_rows(rows)

    assert result[0]["nota_2025"] == "5 / AP"
    assert "ceo1" not in result[0]
    assert "ceo2" not in result[0]
    assert "ceo3" not in result[0]
    assert "ceo4" not in result[0]


def test_load_standardized_carom_rows_uses_detected_headers() -> None:
    rows = [
        {
            "Matricula": "123",
            "Nome": "Ana",
            "Idade": "31",
            "Cargo": "Analista",
            "Area": "Operacao",
            "CEO1": "CEO1 Ana",
            "CEO2": "CEO2 Ana",
            "CEO3": "CEO3 Ana",
            "CEO4": "CEO4 Ana",
        }
    ]

    result = reader.load_standardized_carom_rows(rows)

    assert result[0]["matricula"] == "123"
    assert result[0]["nome"] == "Ana"
    assert result[0]["area"] == "Operacao"
    assert result[0]["idade"] == "31"
    assert result[0]["ceo1"] == "CEO1 Ana"
    assert result[0]["ceo2"] == "CEO2 Ana"
    assert result[0]["ceo3"] == "CEO3 Ana"
    assert result[0]["ceo4"] == "CEO4 Ana"


def test_resolve_carom_schema_includes_evaluation_and_ceo_fields() -> None:
    schema = reader.resolve_carom_schema(
        [
            "Matricula",
            "Nome",
            "Idade",
            "Cargo",
            "Formacao",
            "Avaliacao 2025",
            "Nota 2025",
            "Potencial 2025",
            "CEO1",
            "CEO2",
            "CEO3",
            "CEO4",
        ]
    )

    assert schema["avaliacao_2025"] == "Avaliacao 2025"
    assert schema["score_2025"] == "Nota 2025"
    assert schema["potencial_2025"] == "Potencial 2025"
    assert schema["ceo1"] == "CEO1"
    assert schema["ceo2"] == "CEO2"
    assert schema["ceo3"] == "CEO3"
    assert schema["ceo4"] == "CEO4"


def test_load_standardized_carom_rows_builds_display_score_from_score_and_potential() -> None:
    rows = [
        {
            "Matricula": "123",
            "Nome": "Ana",
            "Idade": "31",
            "Cargo": "Analista",
            "Formacao": "Engenharia",
            "Nota 2025": "4",
            "Potencial 2025": "AP",
            "CEO3": "CEO3 Ana",
            "CEO4": "CEO4 Ana",
        }
    ]

    result = reader.load_standardized_carom_rows(rows)

    assert reader.resolve_carom_display_score_potential(result[0]) == "4 / AP"


def test_validate_standardized_carom_schema_accepts_legacy_without_ceo_fields() -> None:
    schema = reader.validate_standardized_carom_schema(
        ["Matricula", "Nome", "Idade", "Cargo"]
    )

    assert schema["matricula"] == "Matricula"
    assert schema["nome"] == "Nome"
    assert schema["cargo"] == "Cargo"
    assert schema["ceo3"] is None
    assert schema["ceo4"] is None


def test_legacy_standardized_carom_schema_has_export_eligible_preset() -> None:
    schema = reader.validate_standardized_carom_schema(
        ["Matricula", "Nome", "Idade", "Cargo"]
    )
    eligible = [
        preset_id
        for preset_id in ("mini", "big", "projeto_trainee", "talent_review")
        if not reader.validate_carom_schema_for_preset(schema, preset_id)
    ]

    assert eligible == ["mini"]


def test_legacy_carom_alias_regular_remains_export_eligible() -> None:
    schema = reader.validate_standardized_carom_schema(
        ["Matricula", "Nome", "Idade", "Cargo"]
    )

    assert reader.validate_carom_schema_for_preset(schema, "regular") == []


def test_ceo_driven_carom_presets_fail_clearly_without_ceo_columns() -> None:
    schema = reader.validate_standardized_carom_schema(
        [
            "Matricula",
            "Nome",
            "Idade",
            "Cargo",
            "Formacao",
            "Nota 2025",
            "Potencial 2025",
        ]
    )

    assert "ceo3" in reader.validate_carom_schema_for_preset(schema, "big")
    assert "ceo4" in reader.validate_carom_schema_for_preset(schema, "projeto_trainee")
    assert reader.validate_carom_schema_for_preset(schema, "talent_review")[:2] == [
        "ceo3",
        "ceo4",
    ]


def test_ceo_driven_carom_presets_accept_complete_schema() -> None:
    schema = reader.validate_standardized_carom_schema(
        [
            "Matricula",
            "Nome",
            "Idade",
            "Cargo",
            "Formacao",
            "Nota 2025",
            "Potencial 2025",
            "CEO3",
            "CEO4",
        ]
    )

    assert reader.validate_carom_schema_for_preset(schema, "big") == []
    assert reader.validate_carom_schema_for_preset(schema, "projeto_trainee") == []
    assert reader.validate_carom_schema_for_preset(schema, "talent_review") == []


def test_validate_carom_schema_for_big_requires_template_fields() -> None:
    missing = reader.validate_carom_schema_for_preset(
        {"matricula": "Matricula", "nome": "Nome", "cargo": "Cargo"},
        "big",
    )

    assert missing == [
        "idade",
        "formacao",
        "ceo3",
        "nota_2025",
        "avaliacao_2025",
        "score_2025",
        "potencial_2025",
    ]


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


def test_carom_employee_key_prefers_matricula() -> None:
    employee = {
        "matricula": "123",
        "nome": "Ana Maria",
        "cargo": "Analista",
        "foto": "",
        "area": "",
        "localizacao": "",
        "unidade_gestao": "",
    }

    assert reader.carom_employee_key(employee) == "matricula:123"


def test_filter_carom_employees_matches_partial_name() -> None:
    employees = [
        {
            "matricula": "123",
            "nome": "Ana Maria",
            "cargo": "Analista",
            "foto": "",
            "area": "",
            "localizacao": "",
            "unidade_gestao": "",
        },
        {
            "matricula": "456",
            "nome": "Carlos Souza",
            "cargo": "Coordenador",
            "foto": "",
            "area": "",
            "localizacao": "",
            "unidade_gestao": "",
        },
    ]

    result = reader.filter_carom_employees(employees, query="mari", mode="nome")

    assert len(result) == 1
    assert result[0]["nome"] == "Ana Maria"


def test_filter_carom_employees_prefers_exact_matricula_match() -> None:
    employees = [
        {
            "matricula": "123",
            "nome": "Ana Maria",
            "cargo": "Analista",
            "foto": "",
            "area": "",
            "localizacao": "",
            "unidade_gestao": "",
        },
        {
            "matricula": "1234",
            "nome": "Ana Souza",
            "cargo": "Analista",
            "foto": "",
            "area": "",
            "localizacao": "",
            "unidade_gestao": "",
        },
    ]

    result = reader.filter_carom_employees(employees, query="123", mode="matricula")

    assert len(result) == 1
    assert result[0]["matricula"] == "123"


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
