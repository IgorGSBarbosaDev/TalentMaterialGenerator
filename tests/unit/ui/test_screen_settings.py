from __future__ import annotations

from app.ui.screen_settings import SettingsScreen


def test_settings_screen_emits_save_payload(qtbot) -> None:
    screen = SettingsScreen({})
    qtbot.addWidget(screen)
    received = []
    screen.save_requested.connect(received.append)

    screen.default_output.setText("C:/saida")
    screen._emit_save()

    assert received[0]["default_output_dir"] == "C:/saida"
