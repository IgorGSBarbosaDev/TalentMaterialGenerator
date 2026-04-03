from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

APP_DIR_NAME = "USIGenerator"


def get_repo_default_spreadsheet_path() -> Path | None:
    candidate = Path.cwd() / "PlanilhaTeste.xlsx"
    return candidate if candidate.is_file() else None


def _apply_runtime_defaults(config: dict[str, Any]) -> dict[str, Any]:
    config["default_output_dir"] = str(get_default_output_dir())

    repo_default = get_repo_default_spreadsheet_path()
    if repo_default is not None and not str(config.get("default_spreadsheet_path", "")).strip():
        config["default_spreadsheet_path"] = str(repo_default)
        if not str(config.get("default_onedrive_url", "")).strip():
            config["spreadsheet_source"] = "local"
    return config


def get_default_output_dir() -> Path:
    return Path.home() / "Documents" / "Usi Generator"


DEFAULT_CONFIG: dict[str, Any] = {
    "theme": "dark",
    "spreadsheet_source": "onedrive",
    "default_spreadsheet_path": "",
    "default_onedrive_url": "",
    "default_output_dir": str(get_default_output_dir()),
    "default_grouping": "area",
    "default_carom_columns": 5,
    "cache_enabled": True,
    "cache_ttl_hours": 24,
    "refresh_strategy": "auto_with_manual_refresh",
    "last_cache_sync": "",
    "last_generations": [],
}


def get_app_dir() -> Path:
    appdata = Path(os.environ.get("APPDATA", Path.home()))
    return appdata / APP_DIR_NAME


def get_config_path() -> Path:
    return get_app_dir() / "config.json"


def get_cache_dir() -> Path:
    return get_app_dir() / "cache"


def load_config() -> dict[str, Any]:
    try:
        config_path = get_config_path()
        if not config_path.exists():
            config = deepcopy(DEFAULT_CONFIG)
            return _apply_runtime_defaults(config)

        payload = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            config = deepcopy(DEFAULT_CONFIG)
            return _apply_runtime_defaults(config)

        merged = deepcopy(DEFAULT_CONFIG)
        merged.update(payload)
        merged.pop("default_output_mode", None)
        return _apply_runtime_defaults(merged)
    except Exception:
        config = deepcopy(DEFAULT_CONFIG)
        return _apply_runtime_defaults(config)


def save_config(data: dict[str, Any]) -> None:
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = deepcopy(data)
    payload.pop("default_output_mode", None)
    payload = _apply_runtime_defaults(payload)
    config_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def update_config(updates: dict[str, Any]) -> dict[str, Any]:
    config = load_config()
    config.update(updates)
    save_config(config)
    return config


def reset_to_defaults() -> dict[str, Any]:
    config = deepcopy(DEFAULT_CONFIG)
    config = _apply_runtime_defaults(config)
    save_config(config)
    return config
