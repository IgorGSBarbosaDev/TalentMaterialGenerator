from __future__ import annotations

from time import monotonic
from typing import Any

from PySide6.QtCore import QThread, Signal

from app.core.generator_carom import CaromConfig, generate_carom_pptx
from app.core.generator_ficha import generate_ficha_pptx
from app.core.reader import (
    SpreadsheetSourceResult,
    cleanup_source,
    read_spreadsheet,
    remap_rows,
    resolve_spreadsheet_source,
)


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
        started_at = monotonic()
        try:
            self.log.emit("Preparando fonte de dados...", "info")
            source_result = resolve_spreadsheet_source(
                self.config["spreadsheet_source"],
                cache_enabled=bool(self.config.get("cache_enabled", True)),
                cache_ttl_hours=int(self.config.get("cache_ttl_hours", 24)),
                force_refresh=bool(self.config.get("force_refresh", False)),
            )
            self.log.emit(source_result.message, "info")

            raw_rows = read_spreadsheet(source_result.path)
            rows = remap_rows(raw_rows, self.config["column_mapping"])
            self.log.emit(f"{len(rows)} colaboradores encontrados", "success")

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
                files = generate_ficha_pptx(
                    rows,
                    self.config["output_dir"],
                    output_mode=str(
                        self.config.get("output_mode", "one_file_per_employee")
                    ),
                    callback=_callback,
                )
            else:
                carom_config: CaromConfig = {
                    "colunas": int(self.config.get("colunas", 5)),
                    "agrupamento": self.config.get("agrupamento"),
                    "titulo": str(self.config.get("titulo", "Carômetro")),
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
            if source_result is not None:
                cleanup_source(source_result)
