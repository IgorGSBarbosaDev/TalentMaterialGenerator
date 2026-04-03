from __future__ import annotations

from time import monotonic
from typing import Any

from PySide6.QtCore import QThread, Signal

from app.core.generator_carom import CaromConfig, generate_carom_pptx
from app.core.generator_ficha import generate_ficha_pptx
from app.core.reader import (
    FichaEmployee,
    SpreadsheetSourceResult,
    cleanup_source,
    has_expected_ficha_column_order,
    lookup_ficha_employees,
    read_spreadsheet,
    remap_rows,
    resolve_spreadsheet_source,
    validate_standardized_ficha_schema,
    validate_ficha_employee,
)


class FichaLookupWorker(QThread):
    succeeded = Signal(dict)
    error = Signal(str)

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__()
        self.config = config

    def run(self) -> None:
        source_result: SpreadsheetSourceResult | None = None
        try:
            source_result = resolve_spreadsheet_source(
                self.config["spreadsheet_source"],
                cache_enabled=bool(self.config.get("cache_enabled", True)),
                cache_ttl_hours=int(self.config.get("cache_ttl_hours", 24)),
                force_refresh=bool(self.config.get("force_refresh", False)),
            )
            raw_rows = read_spreadsheet(source_result.path)
            headers = list(raw_rows[0].keys()) if raw_rows else []
            schema = validate_standardized_ficha_schema(headers)
            matches = (
                []
                if bool(self.config.get("validate_only", False))
                else lookup_ficha_employees(
                    raw_rows,
                    name_query=str(self.config.get("lookup_name", "")),
                    matricula_query=str(self.config.get("lookup_matricula", "")),
                )
            )
            self.succeeded.emit(
                {
                    "schema": schema,
                    "matches": matches,
                    "source_result": source_result,
                    "match_count": len(matches),
                    "row_count": len(raw_rows),
                    "headers": headers,
                    "schema_order_matches": has_expected_ficha_column_order(headers),
                    "validated": True,
                }
            )
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            if source_result is not None:
                cleanup_source(source_result)


class GenerationWorker(QThread):
    progress = Signal(int, int, str)
    log = Signal(str, str)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, job_type: str, config: dict[str, Any]) -> None:
        super().__init__()
        self.job_type = job_type
        self.config = config

    def run(self) -> None:
        source_result: SpreadsheetSourceResult | None = None
        cleanup_target: SpreadsheetSourceResult | None = None
        started_at = monotonic()
        try:
            def _callback(message: dict[str, Any]) -> None:
                if message.get("type") == "progress":
                    self.progress.emit(
                        int(message["current"]),
                        int(message["total"]),
                        str(message.get("name", "")),
                    )
                elif message.get("type") == "log":
                    self.log.emit(
                        str(message.get("message", "")),
                        str(message.get("level", "info")),
                    )

            if self.job_type == "ficha":
                employee: FichaEmployee = self.config["selected_employee"]
                missing_required = validate_ficha_employee(employee)
                if missing_required:
                    joined = ", ".join(missing_required)
                    raise ValueError(
                        f"O colaborador selecionado nao possui os campos obrigatorios: {joined}."
                    )
                self.log.emit("Colaborador confirmado. Iniciando geracao individual.", "info")
                output_path = generate_ficha_pptx(
                    employee,
                    self.config["output_dir"],
                    callback=_callback,
                )
                files = [output_path]
                source_result = self.config.get("source_result")
            else:
                self.log.emit("Preparando fonte de dados...", "info")
                source_result = resolve_spreadsheet_source(
                    self.config["spreadsheet_source"],
                    cache_enabled=bool(self.config.get("cache_enabled", True)),
                    cache_ttl_hours=int(self.config.get("cache_ttl_hours", 24)),
                    force_refresh=bool(self.config.get("force_refresh", False)),
                )
                cleanup_target = source_result
                self.log.emit(source_result.message, "info")

                raw_rows = read_spreadsheet(source_result.path)
                rows = remap_rows(raw_rows, self.config["column_mapping"])
                self.log.emit(f"{len(rows)} colaboradores encontrados", "success")
                carom_config: CaromConfig = {
                    "colunas": int(self.config.get("colunas", 5)),
                    "agrupamento": self.config.get("agrupamento"),
                    "titulo": str(self.config.get("titulo", "Carometro")),
                    "show_nota": bool(self.config.get("show_nota", True)),
                    "show_potencial": bool(self.config.get("show_potencial", True)),
                    "show_cargo": bool(self.config.get("show_cargo", True)),
                    "cores_automaticas": bool(
                        self.config.get("cores_automaticas", True)
                    ),
                }
                files = generate_carom_pptx(
                    rows,
                    self.config["output_dir"],
                    carom_config,
                    callback=_callback,
                )

            elapsed = max(monotonic() - started_at, 0.0)
            self.finished.emit(
                {
                    "files": files,
                    "output_dir": self.config["output_dir"],
                    "count": len(files),
                    "elapsed": f"{elapsed:0.1f}s",
                    "source_result": source_result,
                }
            )
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            if cleanup_target is not None:
                cleanup_source(cleanup_target)

