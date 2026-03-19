from __future__ import annotations

import queue
import threading
from pathlib import Path
from typing import Any

import customtkinter as ctk

from app.core import reader
from app.core.generator_ficha import generate_ficha_pptx


class FichaScreen(ctk.CTkFrame):
    """Configuration screen for ficha generation."""

    def __init__(self, master: Any, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.column_mapping: dict[str, str | None] = {}
        self._queue: queue.Queue[dict[str, Any]] | None = None
        self._thread: threading.Thread | None = None

        self.entry_spreadsheet = ctk.CTkEntry(self, placeholder_text="Planilha .xlsx")
        self.entry_spreadsheet.pack(fill="x", padx=20, pady=(20, 8))

        self.entry_photos_dir = ctk.CTkEntry(self, placeholder_text="Pasta de fotos")
        self.entry_photos_dir.pack(fill="x", padx=20, pady=8)

        self.entry_output_dir = ctk.CTkEntry(self, placeholder_text="Pasta de saida")
        self.entry_output_dir.pack(fill="x", padx=20, pady=8)

        self.var_include_photo = ctk.BooleanVar(value=True)
        self.chk_include_photo = ctk.CTkCheckBox(
            self,
            text="Incluir foto",
            variable=self.var_include_photo,
        )
        self.chk_include_photo.pack(anchor="w", padx=20, pady=(8, 4))

        self.var_gerar_pdf = ctk.BooleanVar(value=False)
        self.chk_gerar_pdf = ctk.CTkCheckBox(
            self,
            text="Gerar PDF",
            variable=self.var_gerar_pdf,
        )
        self.chk_gerar_pdf.pack(anchor="w", padx=20, pady=(4, 12))

        self.btn_gerar = ctk.CTkButton(
            self,
            text="GERAR FICHAS",
            command=self._start_generation,
        )
        self.btn_gerar.pack(fill="x", padx=20, pady=(8, 20))

    def _entry_value(self, attr_name: str) -> str:
        entry = getattr(self, attr_name, None)
        if entry is None:
            return ""

        getter = getattr(entry, "get", None)
        if not callable(getter):
            return ""

        value = getter()
        if value is None:
            return ""

        return str(value).strip()

    def _bool_var_value(self, attr_name: str, default: bool = False) -> bool:
        variable = getattr(self, attr_name, None)
        if variable is None:
            return default

        getter = getattr(variable, "get", None)
        if callable(getter):
            return bool(getter())

        return bool(variable)

    def _validate_inputs(self) -> bool:
        spreadsheet_path = self._entry_value("entry_spreadsheet")
        photos_dir = self._entry_value("entry_photos_dir")

        if spreadsheet_path == "" or photos_dir == "":
            return False

        if not Path(spreadsheet_path).is_file():
            return False

        if not Path(photos_dir).is_dir():
            return False

        return True

    def _get_config(self) -> dict[str, Any]:
        return {
            "spreadsheet_path": self._entry_value("entry_spreadsheet"),
            "photos_dir": self._entry_value("entry_photos_dir"),
            "output_dir": self._entry_value("entry_output_dir"),
            "column_mapping": dict(getattr(self, "column_mapping", {})),
            "include_photo": self._bool_var_value("var_include_photo", default=True),
            "gerar_pdf": self._bool_var_value("var_gerar_pdf", default=False),
        }

    def _auto_detect_columns(self) -> None:
        spreadsheet_path = self._entry_value("entry_spreadsheet")
        if spreadsheet_path == "" or not Path(spreadsheet_path).is_file():
            return

        rows = reader.read_spreadsheet(spreadsheet_path)
        headers = list(rows[0].keys()) if rows else []
        self.column_mapping = reader.detect_columns(headers)

    def _start_generation(self) -> None:
        if not self._validate_inputs():
            return

        self.btn_gerar.configure(state="disabled")
        self._queue = queue.Queue()

        config = self._get_config()
        self._thread = threading.Thread(
            target=self._run_worker,
            args=(config, self._queue),
            daemon=True,
        )
        self._thread.start()
        self.after(100, self._check_queue)

    def _run_worker(
        self, config: dict[str, Any], q: queue.Queue[dict[str, Any]]
    ) -> None:
        try:
            employees = reader.read_spreadsheet(config["spreadsheet_path"])
            generate_ficha_pptx(
                employees=employees,
                photos_dir=config["photos_dir"],
                output_dir=config["output_dir"],
                callback=lambda msg: q.put(msg),
            )
            q.put({"type": "complete"})
        except Exception as exc:  # pragma: no cover - defensive thread boundary
            q.put({"type": "error", "message": str(exc)})

    def _check_queue(self) -> None:
        if self._queue is None:
            return

        try:
            while True:
                message = self._queue.get_nowait()
                self._handle_message(message)
        except queue.Empty:
            pass

        if self._thread is not None and self._thread.is_alive():
            self.after(100, self._check_queue)
        else:
            self.btn_gerar.configure(state="normal")

    def _handle_message(self, msg: dict[str, Any]) -> None:
        self._last_message = msg
