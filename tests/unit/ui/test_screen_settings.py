from __future__ import annotations

from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton

from app.config.settings import get_default_output_dir
from app.ui.screen_settings import SettingsScreen


def test_settings_screen_emits_save_payload(qtbot) -> None:
    screen = SettingsScreen({})
    qtbot.addWidget(screen)
    received = []
    screen.save_requested.connect(received.append)

    screen._emit_save()

    assert "default_output_dir" not in received[0]
    assert "default_onedrive_url" not in received[0]
    assert screen.default_output.text() == str(get_default_output_dir())
    assert screen.default_output.isReadOnly() is True


def test_settings_screen_has_no_theme_toggle_button(qtbot) -> None:
    screen = SettingsScreen({})
    qtbot.addWidget(screen)

    button_texts = [btn.text().lower() for btn in screen.findChildren(QPushButton)]
    assert all("tema" not in text for text in button_texts)


def test_settings_screen_does_not_render_duplicate_page_title(qtbot) -> None:
    screen = SettingsScreen({})
    qtbot.addWidget(screen)

    title_labels = [
        label
        for label in screen.findChildren(QLabel)
        if label.objectName() == "title" and label.text() == "Configuracoes"
    ]

    assert title_labels == []


def test_settings_screen_has_no_onedrive_controls(qtbot) -> None:
    screen = SettingsScreen({"default_onedrive_url": "https://example.com/base.xlsx"})
    qtbot.addWidget(screen)

    label_texts = [label.text().lower() for label in screen.findChildren(QLabel)]
    button_texts = [
        button.text().lower() for button in screen.findChildren(QPushButton)
    ]
    line_values = [line.text().lower() for line in screen.findChildren(QLineEdit)]

    assert all("onedrive" not in text for text in label_texts)
    assert all("onedrive" not in text for text in button_texts)
    assert all("https://example.com/base.xlsx" not in text for text in line_values)


def test_settings_screen_has_single_cache_refresh_button_and_browse_button(
    qtbot,
) -> None:
    screen = SettingsScreen({})
    qtbot.addWidget(screen)

    buttons = screen.findChildren(QPushButton)
    refresh_buttons = [
        button for button in buttons if button.text() == "Atualizar base agora"
    ]
    browse_buttons = [
        button for button in buttons if button.text() == "Procurar arquivo"
    ]

    assert len(refresh_buttons) == 1
    assert len(browse_buttons) == 1
    assert refresh_buttons[0].parentWidget().objectName() == "sectionCard"
    assert browse_buttons[0].parentWidget().objectName() == "sectionCard"


def test_settings_screen_shows_default_base_metadata(qtbot) -> None:
    screen = SettingsScreen(
        {
            "default_spreadsheet_name": "base.xlsx",
            "default_spreadsheet_path": r"C:\dados\base.xlsx",
            "default_base_row_count": 12,
            "default_spreadsheet_mtime": 100.0,
            "default_spreadsheet_size": 200,
        }
    )
    qtbot.addWidget(screen)

    assert screen.base_name_label.text() == "base.xlsx"
    assert screen.base_path_label.text() == r"C:\dados\base.xlsx"
    assert "12" in screen.base_status_label.text()


def test_settings_screen_handles_sidebar_collapsed_state(qtbot) -> None:
    screen = SettingsScreen({})
    qtbot.addWidget(screen)

    screen.set_sidebar_collapsed(True)
    assert screen.intro_card.subtitle_label.isHidden() is True

    screen.set_sidebar_collapsed(False)
    assert screen.intro_card.subtitle_label.isHidden() is False


def test_settings_inputs_live_inside_section_card_container(qtbot) -> None:
    screen = SettingsScreen({})
    qtbot.addWidget(screen)

    assert screen.default_spreadsheet.parentWidget().objectName() == "sectionCard"
