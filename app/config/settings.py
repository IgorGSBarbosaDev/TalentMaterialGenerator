from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "theme": "dark",
    "default_spreadsheet_path": "",
    "default_photos_dir": "",
    "default_output_dir": "",
    "default_format": "pptx",
    "default_carom_columns": 5,
    "last_generations": [],
}


def get_config_path() -> Path:
    appdata_path = Path(os.environ["APPDATA"])
    return appdata_path / "USIGenerator" / "config.json"


def load_config() -> dict[str, Any]:
    try:
        config_path = get_config_path()
        if not config_path.exists():
            return DEFAULT_CONFIG.copy()

        loaded_data = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(loaded_data, dict):
            return DEFAULT_CONFIG.copy()

        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(loaded_data)
        return merged_config
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(data: dict[str, Any]) -> None:
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def reset_to_defaults() -> None:
    save_config(DEFAULT_CONFIG.copy())
