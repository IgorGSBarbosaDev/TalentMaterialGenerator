from __future__ import annotations

import sys
from typing import Any

import customtkinter as ctk

from app.config import settings
from app.ui.screen_ficha import FichaScreen


def _resolve_appearance_mode(config: dict[str, Any]) -> str:
	theme_value = str(config.get("theme", "dark")).strip().lower()
	return "Light" if theme_value == "light" else "Dark"


def _populate_default_paths(screen: FichaScreen, config: dict[str, Any]) -> None:
	spreadsheet = str(config.get("default_spreadsheet_path", "")).strip()
	photos_dir = str(config.get("default_photos_dir", "")).strip()
	output_dir = str(config.get("default_output_dir", "")).strip()

	if spreadsheet:
		screen.entry_spreadsheet.insert(0, spreadsheet)
	if photos_dir:
		screen.entry_photos_dir.insert(0, photos_dir)
	if output_dir:
		screen.entry_output_dir.insert(0, output_dir)


def create_app() -> ctk.CTk:
	config = settings.load_config()

	ctk.set_appearance_mode(_resolve_appearance_mode(config))
	ctk.set_default_color_theme("green")

	app = ctk.CTk()
	app.title("USI Generator")
	app.geometry("900x600")
	app.minsize(900, 600)

	ficha_screen = FichaScreen(app)
	ficha_screen.pack(fill="both", expand=True)
	_populate_default_paths(ficha_screen, config)

	return app


def main() -> int:
	try:
		app = create_app()
		app.mainloop()
		return 0
	except Exception as exc:
		print(f"Failed to initialize application: {exc}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	raise SystemExit(main())
