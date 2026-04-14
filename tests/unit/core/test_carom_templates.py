from __future__ import annotations

from pathlib import Path

import pytest

from app.core import carom_templates, resource_paths


def test_resolve_carom_template_path_finds_source_template(monkeypatch) -> None:
    monkeypatch.delattr(resource_paths.sys, "_MEIPASS", raising=False)

    path = carom_templates.resolve_carom_template_path("Carometro-big.pptx")

    assert path.is_file()
    assert path.name == "Carometro-big.pptx"


def test_resolve_carom_template_path_uses_pyinstaller_runtime_root(
    monkeypatch,
    tmp_path: Path,
) -> None:
    bundled_template = tmp_path / "carometros" / "Carometro-big.pptx"
    bundled_template.parent.mkdir()
    bundled_template.write_bytes(b"pptx")
    monkeypatch.setattr(resource_paths.sys, "_MEIPASS", str(tmp_path), raising=False)

    path = carom_templates.get_carom_preset("big").template_path

    assert path == bundled_template


def test_resolve_carom_template_path_raises_clear_error_when_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(resource_paths.sys, "_MEIPASS", str(tmp_path), raising=False)

    with pytest.raises(FileNotFoundError) as exc_info:
        carom_templates.resolve_carom_template_path("Carometro-big.pptx")

    message = str(exc_info.value)
    assert "Template de carometro" in message
    assert "Carometro-big.pptx" in message
    assert "empacotado" in message
