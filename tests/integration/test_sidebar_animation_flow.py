from __future__ import annotations

from PySide6.QtCore import QAbstractAnimation

from app.ui.app_window import AppWindow


def _wait_sidebar_animation_finished(qtbot, window: AppWindow) -> None:
    qtbot.waitUntil(
        lambda: getattr(window, "_sidebar_animation", None) is not None
        and window._sidebar_animation.state() == QAbstractAnimation.State.Stopped,
        timeout=1500,
    )


def test_sidebar_animation_flow_persists_collapsed_state_across_navigation(qtbot) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    window.navigate_to("ficha")
    window.sidebar_toggle_button.click()
    qtbot.waitUntil(
        lambda: window.sidebar.width() == window._sidebar_collapsed_width,
        timeout=1500,
    )
    _wait_sidebar_animation_finished(qtbot, window)

    window.navigate_to("settings")

    assert window.stack.currentWidget() is window.settings_screen
    assert window.sidebar.width() == window._sidebar_collapsed_width
    assert window.brand_title.isHidden() is True
    assert window.menu_buttons["settings"].isChecked() is True


def test_sidebar_animation_flow_recovers_to_expanded_state_on_current_screen(qtbot) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    window.navigate_to("progress")

    window.sidebar_toggle_button.click()
    qtbot.waitUntil(
        lambda: window.sidebar.width() == window._sidebar_collapsed_width,
        timeout=1500,
    )
    _wait_sidebar_animation_finished(qtbot, window)

    window.sidebar_toggle_button.click()
    qtbot.waitUntil(
        lambda: window.sidebar.width() == window._sidebar_expanded_width,
        timeout=1500,
    )
    _wait_sidebar_animation_finished(qtbot, window)

    assert window.stack.currentWidget() is window.progress_screen
    assert window.sidebar.width() == window._sidebar_expanded_width
    assert window._sidebar_collapsed is False
    assert window.menu_buttons["progress"].isChecked() is True
