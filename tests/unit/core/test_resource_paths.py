from __future__ import annotations

from pathlib import Path

from app.core import resource_paths


def test_resolve_existing_icon_path_finds_repo_asset(monkeypatch) -> None:
    monkeypatch.delattr(resource_paths.sys, "_MEIPASS", raising=False)

    path = resource_paths.resolve_existing_icon_path()

    assert path.is_file()
    assert path.name in {"iconeUsiGenerator.png", "iconeUsiGenerator.ico"}


def test_resolve_existing_icon_path_uses_pyinstaller_runtime_root(
    monkeypatch,
    tmp_path: Path,
) -> None:
    bundled_icon = tmp_path / "assets" / "iconeUsiGenerator.png"
    bundled_icon.parent.mkdir(parents=True, exist_ok=True)
    bundled_icon.write_bytes(b"png")
    monkeypatch.setattr(resource_paths.sys, "_MEIPASS", str(tmp_path), raising=False)

    path = resource_paths.resolve_existing_icon_path()

    assert path == bundled_icon
