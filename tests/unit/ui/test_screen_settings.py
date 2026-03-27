from __future__ import annotations

from PySide6.QtWidgets import QPushButton

from app.config.settings import get_default_output_dir
from app.ui.screen_settings import SettingsScreen


def test_settings_screen_emits_save_payload(qtbot) -> None:
    screen = SettingsScreen({})
    qtbot.addWidget(screen)
    received = []
    screen.save_requested.connect(received.append)

    screen._emit_save()

    assert "default_output_dir" not in received[0]
    assert screen.default_output.text() == str(get_default_output_dir())
    assert screen.default_output.isReadOnly() is True


def test_settings_screen_has_no_theme_toggle_button(qtbot) -> None:
    screen = SettingsScreen({})
    qtbot.addWidget(screen)

    button_texts = [btn.text().lower() for btn in screen.findChildren(QPushButton)]
    assert all("tema" not in text for text in button_texts)
