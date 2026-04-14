from __future__ import annotations

import sys
from pathlib import Path


def get_runtime_root() -> Path:
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return Path(bundle_root)
    return Path(__file__).resolve().parents[2]


def resolve_resource_path(*relative_parts: str | Path) -> Path:
    return get_runtime_root().joinpath(*(str(part) for part in relative_parts))


def resolve_existing_resource_path(
    *relative_parts: str | Path,
    resource_label: str,
) -> Path:
    path = resolve_resource_path(*relative_parts)
    if path.is_file():
        return path

    relative_path = Path(*[str(part) for part in relative_parts])
    raise FileNotFoundError(
        f"{resource_label} nao encontrado: '{relative_path}'. "
        f"Procurei em '{path}'. Verifique se o recurso foi empacotado com a aplicacao."
    )
