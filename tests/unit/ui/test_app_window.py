from __future__ import annotations

from PySide6.QtCore import QAbstractAnimation, QEasingCurve

from app.ui.app_window import AppWindow


def _wait_sidebar_animation_finished(qtbot, window: AppWindow) -> None:
    qtbot.waitUntil(
        lambda: getattr(window, "_sidebar_animation", None) is not None
        and window._sidebar_animation.state() == QAbstractAnimation.State.Stopped,
        timeout=1500,
    )


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


def test_app_window_has_global_theme_button_on_topbar(qtbot) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    assert window.theme_toggle_button.text() == "\u2600"
    assert "claro" in window.theme_toggle_button.toolTip().lower()


def test_app_window_toggle_theme_updates_symbol_and_config(qtbot, monkeypatch) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    def fake_update_config(payload):
        return payload

    monkeypatch.setattr("app.ui.app_window.settings.update_config", fake_update_config)

    window._toggle_theme()

    assert window.config["theme"] == "light"
    assert window.theme_toggle_button.text() == "\u263E"
    assert "escuro" in window.theme_toggle_button.toolTip().lower()


def test_app_window_sidebar_animation_is_configured_for_fluid_motion(qtbot) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    animation = getattr(window, "_sidebar_animation", None)
    assert animation is not None
    assert animation.duration() >= 120
    assert animation.easingCurve().type() == QEasingCurve.Type.OutCubic


def test_app_window_sidebar_toggle_collapses_and_expands(qtbot) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    expanded = window.sidebar.width()
    window.sidebar_toggle_button.click()

    animation = getattr(window, "_sidebar_animation", None)
    assert animation is not None
    assert animation.state() == QAbstractAnimation.State.Running

    qtbot.waitUntil(
        lambda: window.sidebar.width() == window._sidebar_collapsed_width,
        timeout=1500,
    )
    _wait_sidebar_animation_finished(qtbot, window)
    collapsed = window.sidebar.width()

    assert collapsed < expanded
    assert window._sidebar_collapsed is True
    assert window.sidebar_toggle_button.isEnabled() is True

    window.sidebar_toggle_button.click()
    qtbot.waitUntil(lambda: window.sidebar.width() == expanded, timeout=1500)
    _wait_sidebar_animation_finished(qtbot, window)

    assert window.sidebar.width() == expanded
    assert window._sidebar_collapsed is False


def test_app_window_sidebar_state_persists_across_navigation(qtbot) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    window.sidebar_toggle_button.click()
    qtbot.waitUntil(
        lambda: window.sidebar.width() == window._sidebar_collapsed_width,
        timeout=1500,
    )
    _wait_sidebar_animation_finished(qtbot, window)
    collapsed_width = window.sidebar.width()
    window.navigate_to("ficha")
    window.navigate_to("settings")

    assert window.sidebar.width() == collapsed_width
    assert window.menu_buttons["settings"].isChecked() is True


def test_app_window_minimized_sidebar_hides_brand_text_keeps_logo(qtbot) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    window.sidebar_toggle_button.click()
    qtbot.waitUntil(
        lambda: window.sidebar.width() == window._sidebar_collapsed_width,
        timeout=1500,
    )
    _wait_sidebar_animation_finished(qtbot, window)

    assert window.brand_title.isHidden() is True
    assert window.brand_subtitle.isHidden() is True
    assert window.brand_mark.isHidden() is False


def test_app_window_minimized_sidebar_keeps_compact_centered_nav_content(qtbot) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    window.sidebar_toggle_button.click()
    qtbot.waitUntil(
        lambda: window.sidebar.width() == window._sidebar_collapsed_width,
        timeout=1500,
    )
    _wait_sidebar_animation_finished(qtbot, window)
    home_text = window.menu_buttons["home"].text()

    assert "\n" in home_text
    assert "H" in home_text
    assert "Inicio" in home_text


def test_app_window_sidebar_toggle_ignores_clicks_while_animating(qtbot) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    window.sidebar_toggle_button.click()

    animation = getattr(window, "_sidebar_animation", None)
    assert animation is not None
    assert animation.state() == QAbstractAnimation.State.Running
    assert window.sidebar_toggle_button.isEnabled() is False

    window.sidebar_toggle_button.click()

    qtbot.waitUntil(
        lambda: window.sidebar.width() == window._sidebar_collapsed_width,
        timeout=1500,
    )
    _wait_sidebar_animation_finished(qtbot, window)

    assert window._sidebar_collapsed is True
    assert window.sidebar_toggle_button.isEnabled() is True


def test_app_window_topbar_has_no_right_badge_widget(qtbot) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    assert hasattr(window, "topbar_badge") is False
