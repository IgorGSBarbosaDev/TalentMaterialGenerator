from __future__ import annotations

import subprocess
import sys
import types

from app.core import pdf_exporter


def test_is_libreoffice_available_returns_bool_without_raising() -> None:
    try:
        result = pdf_exporter.is_libreoffice_available()
    except Exception as exc:  # pragma: no cover - defensive assertion only
        raise AssertionError("Function should not raise") from exc

    assert isinstance(result, bool)


def test_is_libreoffice_available_returns_false_when_lookup_raises(monkeypatch) -> None:
    def _raise() -> str | None:
        raise RuntimeError("lookup failed")

    monkeypatch.setattr("app.core.pdf_exporter.find_libreoffice_path", _raise)

    assert pdf_exporter.is_libreoffice_available() is False


def test_find_libreoffice_path_returns_none_when_not_installed(
    monkeypatch,
) -> None:
    monkeypatch.setattr("app.core.pdf_exporter.os.path.exists", lambda _: False)

    result = pdf_exporter.find_libreoffice_path()

    assert result is None


def test_find_libreoffice_path_returns_first_existing_path(monkeypatch) -> None:
    first = pdf_exporter.LIBREOFFICE_PATHS[0]

    monkeypatch.setattr(
        "app.core.pdf_exporter.os.path.exists",
        lambda path: path == first,
    )

    assert pdf_exporter.find_libreoffice_path() == first


def test_export_to_pdf_returns_false_for_nonexistent_pptx_file(tmp_path) -> None:
    result = pdf_exporter.export_to_pdf(
        str(tmp_path / "missing_file.pptx"),
        str(tmp_path),
    )

    assert result is False


def test_try_comtypes_export_returns_false_when_comtypes_is_missing() -> None:
    result = pdf_exporter.try_comtypes_export("any.pptx", "any-output")

    assert result is False


def test_try_comtypes_export_returns_true_on_success(monkeypatch, tmp_path) -> None:
    class _FakePresentation:
        def __init__(self) -> None:
            self.saved: tuple[str, int] | None = None
            self.closed = False

        def SaveAs(self, pdf_path: str, file_type: int) -> None:
            self.saved = (pdf_path, file_type)

        def Close(self) -> None:
            self.closed = True

    class _FakePresentations:
        def __init__(self, presentation: _FakePresentation) -> None:
            self._presentation = presentation

        def Open(self, _pptx_path: str, WithWindow: bool):  # noqa: N803
            assert WithWindow is False
            return self._presentation

    class _FakePowerPoint:
        def __init__(self, presentation: _FakePresentation) -> None:
            self.Presentations = _FakePresentations(presentation)
            self.quit_called = False

        def Quit(self) -> None:
            self.quit_called = True

    fake_presentation = _FakePresentation()
    fake_powerpoint = _FakePowerPoint(fake_presentation)

    fake_client = types.SimpleNamespace(
        CreateObject=lambda _name: fake_powerpoint,
    )
    fake_comtypes = types.ModuleType("comtypes")
    fake_comtypes.client = fake_client

    monkeypatch.setitem(sys.modules, "comtypes", fake_comtypes)
    monkeypatch.setitem(sys.modules, "comtypes.client", fake_client)

    output_dir = tmp_path / "pdfs"
    result = pdf_exporter.try_comtypes_export("input.pptx", str(output_dir))

    assert result is True
    assert fake_presentation.saved == (str(output_dir / "input.pdf"), 32)
    assert fake_presentation.closed is True
    assert fake_powerpoint.quit_called is True


def test_try_comtypes_export_returns_false_and_handles_cleanup_errors(
    monkeypatch,
    tmp_path,
) -> None:
    class _ExplodingPresentation:
        def SaveAs(self, _pdf_path: str, _file_type: int) -> None:
            raise RuntimeError("save failed")

        def Close(self) -> None:
            raise RuntimeError("close failed")

    class _ExplodingPresentations:
        def Open(self, _pptx_path: str, WithWindow: bool):  # noqa: N803
            assert WithWindow is False
            return _ExplodingPresentation()

    class _ExplodingPowerPoint:
        def __init__(self) -> None:
            self.Presentations = _ExplodingPresentations()

        def Quit(self) -> None:
            raise RuntimeError("quit failed")

    fake_client = types.SimpleNamespace(
        CreateObject=lambda _name: _ExplodingPowerPoint(),
    )
    fake_comtypes = types.ModuleType("comtypes")
    fake_comtypes.client = fake_client

    monkeypatch.setitem(sys.modules, "comtypes", fake_comtypes)
    monkeypatch.setitem(sys.modules, "comtypes.client", fake_client)

    result = pdf_exporter.try_comtypes_export("input.pptx", str(tmp_path / "pdfs"))

    assert result is False


def test_export_to_pdf_calls_subprocess_with_headless_flag(
    monkeypatch,
    tmp_path,
) -> None:
    pptx_path = tmp_path / "input.pptx"
    pptx_path.write_bytes(b"pptx")

    run_mock = []

    def _fake_run(cmd, timeout, check):
        run_mock.append((cmd, timeout, check))
        return None

    monkeypatch.setattr("app.core.pdf_exporter.is_libreoffice_available", lambda: True)
    monkeypatch.setattr(
        "app.core.pdf_exporter.find_libreoffice_path",
        lambda: r"C:\\Program Files\\LibreOffice\\program\\soffice.exe",
    )
    monkeypatch.setattr("app.core.pdf_exporter.subprocess.run", _fake_run)

    result = pdf_exporter.export_to_pdf(str(pptx_path), str(tmp_path))

    assert result is True
    assert run_mock
    assert "--headless" in run_mock[0][0]


def test_export_to_pdf_subprocess_arguments_contain_convert_to_pdf(
    monkeypatch,
    tmp_path,
) -> None:
    pptx_path = tmp_path / "input.pptx"
    pptx_path.write_bytes(b"pptx")

    captured: list[list[str]] = []

    def _fake_run(cmd, timeout, check):
        captured.append(cmd)
        return None

    monkeypatch.setattr("app.core.pdf_exporter.is_libreoffice_available", lambda: True)
    monkeypatch.setattr(
        "app.core.pdf_exporter.find_libreoffice_path",
        lambda: r"C:\\Program Files\\LibreOffice\\program\\soffice.exe",
    )
    monkeypatch.setattr("app.core.pdf_exporter.subprocess.run", _fake_run)

    result = pdf_exporter.export_to_pdf(str(pptx_path), str(tmp_path))

    assert result is True
    assert captured
    assert "--convert-to" in captured[0]
    assert "pdf" in captured[0]


def test_export_to_pdf_returns_true_on_subprocess_success(
    monkeypatch,
    tmp_path,
) -> None:
    pptx_path = tmp_path / "input.pptx"
    pptx_path.write_bytes(b"pptx")

    monkeypatch.setattr("app.core.pdf_exporter.is_libreoffice_available", lambda: True)
    monkeypatch.setattr(
        "app.core.pdf_exporter.find_libreoffice_path",
        lambda: r"C:\\Program Files\\LibreOffice\\program\\soffice.exe",
    )
    monkeypatch.setattr(
        "app.core.pdf_exporter.subprocess.run",
        lambda cmd, timeout, check: None,
    )

    result = pdf_exporter.export_to_pdf(str(pptx_path), str(tmp_path))

    assert result is True


def test_export_to_pdf_returns_false_on_subprocess_error(
    monkeypatch,
    tmp_path,
) -> None:
    pptx_path = tmp_path / "input.pptx"
    pptx_path.write_bytes(b"pptx")

    def _raise_error(cmd, timeout, check):
        raise subprocess.CalledProcessError(returncode=1, cmd=cmd)

    monkeypatch.setattr("app.core.pdf_exporter.is_libreoffice_available", lambda: True)
    monkeypatch.setattr(
        "app.core.pdf_exporter.find_libreoffice_path",
        lambda: r"C:\\Program Files\\LibreOffice\\program\\soffice.exe",
    )
    monkeypatch.setattr("app.core.pdf_exporter.subprocess.run", _raise_error)

    result = pdf_exporter.export_to_pdf(str(pptx_path), str(tmp_path))

    assert result is False


def test_export_to_pdf_returns_false_on_subprocess_timeout(
    monkeypatch,
    tmp_path,
) -> None:
    pptx_path = tmp_path / "input.pptx"
    pptx_path.write_bytes(b"pptx")

    def _raise_timeout(cmd, timeout, check):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout)

    monkeypatch.setattr("app.core.pdf_exporter.is_libreoffice_available", lambda: True)
    monkeypatch.setattr(
        "app.core.pdf_exporter.find_libreoffice_path",
        lambda: r"C:\\Program Files\\LibreOffice\\program\\soffice.exe",
    )
    monkeypatch.setattr("app.core.pdf_exporter.subprocess.run", _raise_timeout)

    result = pdf_exporter.export_to_pdf(str(pptx_path), str(tmp_path))

    assert result is False


def test_export_to_pdf_returns_false_when_libreoffice_unavailable(
    monkeypatch,
    tmp_path,
) -> None:
    pptx_path = tmp_path / "input.pptx"
    pptx_path.write_bytes(b"pptx")

    monkeypatch.setattr("app.core.pdf_exporter.is_libreoffice_available", lambda: False)
    monkeypatch.setattr("app.core.pdf_exporter.try_comtypes_export", lambda *_: False)

    result = pdf_exporter.export_to_pdf(str(pptx_path), str(tmp_path))

    assert result is False


def test_export_to_pdf_calls_comtypes_fallback_when_libreoffice_missing(
    monkeypatch,
    tmp_path,
) -> None:
    pptx_path = tmp_path / "input.pptx"
    pptx_path.write_bytes(b"pptx")

    called_with: list[tuple[str, str]] = []

    def _fake_fallback(pptx: str, out: str) -> bool:
        called_with.append((pptx, out))
        return False

    monkeypatch.setattr("app.core.pdf_exporter.is_libreoffice_available", lambda: False)
    monkeypatch.setattr("app.core.pdf_exporter.try_comtypes_export", _fake_fallback)

    pdf_exporter.export_to_pdf(str(pptx_path), str(tmp_path))

    assert called_with == [(str(pptx_path), str(tmp_path))]


def test_export_to_pdf_uses_fallback_when_path_lookup_returns_none(
    monkeypatch,
    tmp_path,
) -> None:
    pptx_path = tmp_path / "input.pptx"
    pptx_path.write_bytes(b"pptx")

    fallback_calls: list[tuple[str, str]] = []

    def _fallback(pptx: str, out: str) -> bool:
        fallback_calls.append((pptx, out))
        return True

    monkeypatch.setattr("app.core.pdf_exporter.is_libreoffice_available", lambda: True)
    monkeypatch.setattr("app.core.pdf_exporter.find_libreoffice_path", lambda: None)
    monkeypatch.setattr("app.core.pdf_exporter.try_comtypes_export", _fallback)

    result = pdf_exporter.export_to_pdf(str(pptx_path), str(tmp_path))

    assert result is True
    assert fallback_calls == [(str(pptx_path), str(tmp_path))]


def test_export_to_pdf_never_raises_exception(
    monkeypatch,
    tmp_path,
) -> None:
    pptx_path = tmp_path / "input.pptx"
    pptx_path.write_bytes(b"pptx")

    def _raise_unexpected(cmd, timeout, check):
        raise Exception("unexpected")

    monkeypatch.setattr("app.core.pdf_exporter.is_libreoffice_available", lambda: True)
    monkeypatch.setattr(
        "app.core.pdf_exporter.find_libreoffice_path",
        lambda: r"C:\\Program Files\\LibreOffice\\program\\soffice.exe",
    )
    monkeypatch.setattr("app.core.pdf_exporter.subprocess.run", _raise_unexpected)

    result = pdf_exporter.export_to_pdf(str(pptx_path), str(tmp_path))

    assert result is False
