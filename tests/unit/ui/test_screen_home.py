from __future__ import annotations

from app.ui.screen_home import HomeScreen


def test_home_screen_updates_history(qtbot) -> None:
    screen = HomeScreen()
    qtbot.addWidget(screen)

    screen.refresh_history(["ficha: 1 arquivo"])

    assert "ficha" in screen.history_label.text()


def test_home_screen_handles_sidebar_collapsed_state(qtbot) -> None:
    screen = HomeScreen()
    qtbot.addWidget(screen)

    screen.set_sidebar_collapsed(True)
    assert screen.hero_eyebrow.isHidden() is True

    screen.set_sidebar_collapsed(False)
    assert screen.hero_eyebrow.isHidden() is False
