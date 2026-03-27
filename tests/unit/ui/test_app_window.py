from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtWidgets import QMessageBox

from app.config import settings
from app.ui.app_window import AppWindow


def test_app_window_navigates_between_screens(qtbot) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    window.navigate_to("settings")

    assert window.stack.currentWidget() is window.settings_screen
    assert window.topbar_title.text() == "Configuracoes"
    assert window.menu_buttons["settings"].isChecked() is True


def test_app_window_refreshes_home_stats(qtbot) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    window._stats["ficha"] = 3
    window._stats["carom"] = 2
    window._refresh_home()

    assert "3" in window.home_screen.stats_label.text()
    assert window.home_screen.ficha_metric.value_label.text() == "3"
