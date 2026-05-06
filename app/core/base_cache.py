from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.core import reader


class BaseCacheError(RuntimeError):
    pass


@dataclass(frozen=True)
class BaseCacheResult:
    status: str
    message: str
    config: dict[str, Any]


def get_default_base_cache_path() -> Path:
    return settings.get_cache_dir() / "default_base.xlsx"


def _file_signature(path: Path) -> tuple[float, int]:
    stat = path.stat()
    return stat.st_mtime, stat.st_size


def _validate_spreadsheet(path: Path) -> int:
    try:
        rows = reader.read_spreadsheet(str(path))
        headers = reader.extract_headers(rows)
        reader.validate_standardized_ficha_schema(headers)
        reader.validate_standardized_carom_schema(headers)
        return len(rows)
    except Exception as exc:
        raise BaseCacheError(
            "A planilha selecionada nao parece ser uma base valida. "
            "Confira se o arquivo .xlsx contem as colunas obrigatorias: "
            "Matricula, Nome e Cargo."
        ) from exc


def _store_valid_base(path: Path, row_count: int) -> dict[str, Any]:
    cache_path = get_default_base_cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, cache_path)
    mtime, size = _file_signature(path)
    updates: dict[str, Any] = {
        "spreadsheet_source": "local",
        "default_spreadsheet_path": str(path),
        "default_spreadsheet_name": path.name,
        "default_spreadsheet_mtime": mtime,
        "default_spreadsheet_size": size,
        "default_base_cache_path": str(cache_path),
        "default_base_row_count": row_count,
        "default_base_status": "ready",
        "last_cache_sync": datetime.now(UTC).isoformat(),
    }
    return settings.update_config(updates)


def describe_config_status(config: dict[str, Any]) -> str:
    source = str(config.get("default_spreadsheet_path", "")).strip()
    cache_path = str(config.get("default_base_cache_path", "")).strip()
    if source == "":
        return "not_configured"
    if not Path(source).is_file():
        return "missing"
    if cache_path == "" or not Path(cache_path).is_file():
        return "modified"
    try:
        mtime, size = _file_signature(Path(source))
    except OSError:
        return "missing"
    if (
        float(config.get("default_spreadsheet_mtime", 0.0) or 0.0) == mtime
        and int(config.get("default_spreadsheet_size", 0) or 0) == size
    ):
        return "ready"
    return "modified"


def get_effective_base_path(config: dict[str, Any]) -> str:
    cache_path = str(config.get("default_base_cache_path", "")).strip()
    if cache_path and Path(cache_path).is_file():
        return cache_path
    source = str(config.get("default_spreadsheet_path", "")).strip()
    if source and Path(source).is_file():
        return source
    return ""


def update_default_base_from_file(path: str) -> BaseCacheResult:
    spreadsheet = Path(path)
    if not spreadsheet.is_file():
        raise BaseCacheError(
            "Arquivo nao encontrado. Selecione uma planilha .xlsx valida."
        )
    if spreadsheet.suffix.lower() != ".xlsx":
        raise BaseCacheError("Selecione um arquivo Excel no formato .xlsx.")

    row_count = _validate_spreadsheet(spreadsheet)
    config = _store_valid_base(spreadsheet, row_count)
    return BaseCacheResult(
        status="updated",
        message="Base atualizada com sucesso.",
        config=config,
    )


def refresh_default_base(config: dict[str, Any] | None = None) -> BaseCacheResult:
    current = dict(config or settings.load_config())
    source = str(current.get("default_spreadsheet_path", "")).strip()
    if source == "":
        updated = settings.update_config({"default_base_status": "not_configured"})
        return BaseCacheResult(
            status="not_configured",
            message="Nenhuma base configurada. Selecione uma planilha em Configuracoes.",
            config=updated,
        )

    spreadsheet = Path(source)
    if not spreadsheet.is_file():
        updated = settings.update_config({"default_base_status": "missing"})
        return BaseCacheResult(
            status="missing",
            message="Arquivo da base nao encontrado. Selecione outra planilha.",
            config=updated,
        )

    mtime, size = _file_signature(spreadsheet)
    cached = str(current.get("default_base_cache_path", "")).strip()
    if (
        cached
        and Path(cached).is_file()
        and float(current.get("default_spreadsheet_mtime", 0.0) or 0.0) == mtime
        and int(current.get("default_spreadsheet_size", 0) or 0) == size
    ):
        updated = settings.update_config({"default_base_status": "ready"})
        return BaseCacheResult(
            status="unchanged",
            message="A base ja esta atualizada.",
            config=updated,
        )

    row_count = _validate_spreadsheet(spreadsheet)
    updated = _store_valid_base(spreadsheet, row_count)
    return BaseCacheResult(
        status="updated",
        message="Base atualizada com sucesso.",
        config=updated,
    )
