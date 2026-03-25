from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.config import settings, theme
from app.ui.app_window import AppWindow


def create_app() -> tuple[QApplication, AppWindow]:
    app = QApplication(sys.argv)
    config = settings.load_config()
    app.setApplicationName("USI Generator")
    app.setStyleSheet(theme.build_stylesheet(config.get("theme", "dark")))

    window = AppWindow(config)
    window.show()
    return app, window


def main() -> int:
    try:
        app, _window = create_app()
        return app.exec()
    except Exception as exc:
        print(f"Failed to initialize application: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
