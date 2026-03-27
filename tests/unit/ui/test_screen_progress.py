from __future__ import annotations

from app.ui.screen_progress import ProgressScreen


def test_progress_screen_updates_progress_and_log(qtbot) -> None:
    screen = ProgressScreen()
    qtbot.addWidget(screen)

    screen.update_progress(2, 4, "Ana")
    screen.append_log("Gerando ficha", "success")

    assert screen.progress_bar.value() == 50
    assert "Ana" in screen.counter_label.text()
    assert "Gerando ficha" in screen.log_box.toPlainText()
    assert screen.percent_metric.value_label.text() == "50%"


def test_progress_screen_enables_output_after_completion(qtbot) -> None:
    screen = ProgressScreen()
    qtbot.addWidget(screen)

    screen.on_complete("C:/saida", 3, "1.2s")

    assert screen.btn_open.isEnabled() is True
    assert screen.page_badge == "Concluido"
