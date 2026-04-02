from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

APP_DIR_NAME = "USIGenerator"


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
            config["default_output_dir"] = str(get_default_output_dir())
            return config

        payload = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            config = deepcopy(DEFAULT_CONFIG)
            config["default_output_dir"] = str(get_default_output_dir())
            return config

        merged = deepcopy(DEFAULT_CONFIG)
        merged.update(payload)
        merged.pop("default_output_mode", None)
        merged["default_output_dir"] = str(get_default_output_dir())
        return merged
    except Exception:
        config = deepcopy(DEFAULT_CONFIG)
        config["default_output_dir"] = str(get_default_output_dir())
        return config


def save_config(data: dict[str, Any]) -> None:
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = deepcopy(data)
    payload.pop("default_output_mode", None)
    payload["default_output_dir"] = str(get_default_output_dir())
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
    config["default_output_dir"] = str(get_default_output_dir())
    save_config(config)
    return config
