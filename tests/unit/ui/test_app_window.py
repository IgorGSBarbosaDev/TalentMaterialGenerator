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


def test_app_window_refreshes_home_stats(qtbot) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    window._stats["ficha"] = 3
    window._stats["carom"] = 2
    window._refresh_home()

    assert "3" in window.home_screen.stats_label.text()


def test_app_window_blocks_second_generation_while_worker_is_running(
    qtbot, monkeypatch
) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    messages: list[tuple[str, str]] = []
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, title, message: messages.append((title, message)),
    )
    window.current_worker = SimpleNamespace(isRunning=lambda: True)

    window._start_generation("ficha", {"output_dir": "C:/saida"})

    assert window.stack.currentWidget() is window.progress_screen
    assert messages == [
        (
            "Geracao em andamento",
            "Ja existe uma geracao em andamento. Aguarde a conclusao atual.",
        )
    ]


def test_app_window_start_generation_sets_busy_state(qtbot, monkeypatch) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    created_workers: list[object] = []

    class _FakeSignal:
        def __init__(self) -> None:
            self.connections: list[object] = []

        def connect(self, callback) -> None:
            self.connections.append(callback)

    class _FakeWorker:
        def __init__(self, job_type, payload) -> None:
            self.job_type = job_type
            self.payload = payload
            self.progress = _FakeSignal()
            self.log = _FakeSignal()
            self.finished = _FakeSignal()
            self.error = _FakeSignal()
            self.started = False
            created_workers.append(self)

        def start(self) -> None:
            self.started = True

        def isRunning(self) -> bool:
            return self.started

    monkeypatch.setattr("app.ui.app_window.GenerationWorker", _FakeWorker)

    window._start_generation(
        "ficha",
        {"spreadsheet_source": "https://example.com", "output_dir": "C:/saida"},
    )

    assert created_workers
    assert created_workers[0].started is True
    assert window.current_worker is created_workers[0]
    assert window.ficha_screen.btn_generate.isEnabled() is False
    assert window.carom_screen.btn_generate.isEnabled() is False
    assert window.menu_buttons["ficha"].isEnabled() is False
    assert window.menu_buttons["carom"].isEnabled() is False


def test_app_window_finish_generation_clears_busy_state(qtbot, monkeypatch) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    monkeypatch.setattr(
        settings,
        "update_config",
        lambda updates: {"theme": "dark", "last_generations": updates["last_generations"]},
    )
    window.current_worker = SimpleNamespace(isRunning=lambda: True)
    window._set_generation_busy(True)

    window._handle_worker_finished(
        "ficha",
        {
            "output_dir": "C:/saida",
            "count": 2,
            "elapsed": "1.0s",
            "source_result": SimpleNamespace(downloaded_at="2026-03-25T00:00:00+00:00"),
        },
    )

    assert window.current_worker is None
    assert window.ficha_screen.btn_generate.isEnabled() is True
    assert window.carom_screen.btn_generate.isEnabled() is True
    assert "2" in window.home_screen.stats_label.text()


def test_app_window_error_clears_busy_state(qtbot, monkeypatch) -> None:
    window = AppWindow({"last_generations": [], "theme": "dark"})
    qtbot.addWidget(window)

    captured_errors: list[tuple[str, str]] = []
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, title, message: captured_errors.append((title, message)),
    )
    window.current_worker = SimpleNamespace(isRunning=lambda: True)
    window._set_generation_busy(True)

    window._handle_worker_error("falhou")

    assert window.current_worker is None
    assert window.ficha_screen.btn_generate.isEnabled() is True
    assert window.carom_screen.btn_generate.isEnabled() is True
    assert captured_errors == [("Erro", "falhou")]


def test_app_window_reset_settings_clears_runtime_state(qtbot, monkeypatch) -> None:
    window = AppWindow({"last_generations": ["ficha: 1 arquivo(s)"], "theme": "dark"})
    qtbot.addWidget(window)

    monkeypatch.setattr(
        settings,
        "reset_to_defaults",
        lambda: {"theme": "light", "last_generations": []},
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *_args: None)
    window._stats["ficha"] = 3
    window._stats["carom"] = 1

    window._reset_settings()

    assert window._history == []
    assert window._stats == {"ficha": 0, "carom": 0}
    assert "0" in window.home_screen.stats_label.text()
    assert window.home_screen.history_label.text() == "Histórico vazio."
