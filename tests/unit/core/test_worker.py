from __future__ import annotations

from pathlib import Path

from app.core.reader import SpreadsheetSourceResult
from app.core.worker import FichaLookupWorker, GenerationWorker


def test_ficha_lookup_worker_validates_standardized_schema(monkeypatch) -> None:
    source_result = SpreadsheetSourceResult(
        path="base.xlsx",
        source_kind="local",
        is_temporary=False,
        used_cache=False,
        message="Usando planilha local.",
    )

    monkeypatch.setattr(
        "app.core.worker.resolve_spreadsheet_source",
        lambda *args, **kwargs: source_result,
    )
    monkeypatch.setattr(
        "app.core.worker.read_spreadsheet",
        lambda _path: [{"Matricula": "123", "Nome": "Ana Martins", "Cargo": "Analista"}],
    )

    worker = FichaLookupWorker(
        {
            "spreadsheet_source": "base.xlsx",
            "lookup_name": "",
            "lookup_matricula": "",
            "validate_only": True,
        }
    )
    results: list[dict] = []
    worker.succeeded.connect(results.append)

    worker.run()

    assert results
    assert results[0]["validated"] is True
    assert results[0]["schema"]["matricula"] == "Matricula"


def test_ficha_lookup_worker_returns_matches_without_mapping(monkeypatch) -> None:
    source_result = SpreadsheetSourceResult(
        path="base.xlsx",
        source_kind="local",
        is_temporary=False,
        used_cache=False,
        message="Usando planilha local.",
    )

    monkeypatch.setattr(
        "app.core.worker.resolve_spreadsheet_source",
        lambda *args, **kwargs: source_result,
    )
    monkeypatch.setattr(
        "app.core.worker.read_spreadsheet",
        lambda _path: [{"Matricula": "123", "Nome": "Ana Martins", "Cargo": "Analista"}],
    )

    worker = FichaLookupWorker(
        {
            "spreadsheet_source": "base.xlsx",
            "lookup_name": "ana",
            "lookup_matricula": "",
            "validate_only": False,
        }
    )
    results: list[dict] = []
    worker.succeeded.connect(results.append)

    worker.run()

    assert results
    assert results[0]["match_count"] == 1
    assert results[0]["matches"][0]["nome"] == "Ana Martins"


def test_generation_worker_ficha_uses_selected_employee_only(monkeypatch, tmp_path: Path) -> None:
    selected_employee = {
        "matricula": "123",
        "nome": "Ana Martins",
        "idade": "30",
        "cargo": "Analista",
        "antiguidade": "5 anos",
        "formacao": "Engenharia",
        "resumo_perfil": "Resumo profissional",
        "trajetoria": "2024 - Coordenadora",
    }
    source_result = SpreadsheetSourceResult(
        path="cache.xlsx",
        source_kind="onedrive",
        is_temporary=False,
        used_cache=True,
        message="Usando cache local recente.",
        downloaded_at="2026-04-02T10:00:00+00:00",
    )

    def _raise(*_args, **_kwargs):
        raise AssertionError("Ficha generation should not resolve the spreadsheet again")

    def _generate(employee, output_dir, callback=None):
        assert employee == selected_employee
        output_path = Path(output_dir) / "fichas" / "Ana_Martins.pptx"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"x")
        if callback is not None:
            callback(
                {
                    "type": "progress",
                    "current": 1,
                    "total": 1,
                    "name": employee["nome"],
                }
            )
        return str(output_path)

    monkeypatch.setattr("app.core.worker.resolve_spreadsheet_source", _raise)
    monkeypatch.setattr("app.core.worker.read_spreadsheet", _raise)
    monkeypatch.setattr("app.core.worker.generate_ficha_pptx", _generate)

    worker = GenerationWorker(
        "ficha",
        {
            "spreadsheet_source": "https://example.com/base.xlsx",
            "output_dir": str(tmp_path),
            "selected_employee": selected_employee,
            "source_result": source_result,
        },
    )
    finished: list[dict] = []
    progress: list[tuple[int, int, str]] = []
    worker.finished.connect(finished.append)
    worker.progress.connect(
        lambda current, total, name: progress.append((current, total, name))
    )

    worker.run()

    assert finished
    assert finished[0]["count"] == 1
    assert finished[0]["source_result"] is source_result
    assert progress == [(1, 1, "Ana Martins")]
