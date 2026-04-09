from __future__ import annotations

from PySide6.QtWidgets import QPushButton

from app.ui.screen_home import HomeScreen


def test_home_screen_updates_history(qtbot) -> None:
    screen = HomeScreen()
    qtbot.addWidget(screen)

    screen.refresh_history(["ficha: Ana_Martins.pptx"])

    assert "Ana_Martins.pptx" in screen.history_label.text()


def test_home_screen_hero_simplified_layout(qtbot) -> None:
    screen = HomeScreen()
    qtbot.addWidget(screen)

    assert screen.hero_card.title_label.text() == "TALENT DEVELOPMENT"
    assert screen.hero_card.subtitle_label.text() == ""

    button_texts = [btn.text() for btn in screen.findChildren(QPushButton)]
    assert "Abrir ficha de curriculo" not in button_texts
    assert "Abrir carometro" not in button_texts
    assert "Preferencias" not in button_texts
    assert "Ir para ficha" in button_texts
    assert "Ir para carometro" in button_texts


def test_home_screen_handles_sidebar_collapsed_state(qtbot) -> None:
    screen = HomeScreen()
    qtbot.addWidget(screen)

    screen.set_sidebar_collapsed(True)
    assert screen.stats_label.isHidden() is True

    screen.set_sidebar_collapsed(False)
    assert screen.stats_label.isHidden() is False


def test_home_screen_history_list_lives_inside_section_card(qtbot) -> None:
    screen = HomeScreen()
    qtbot.addWidget(screen)

    assert screen.history_list.parentWidget().objectName() == "sectionCard"
