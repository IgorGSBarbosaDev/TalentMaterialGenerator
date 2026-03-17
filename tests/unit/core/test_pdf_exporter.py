from __future__ import annotations

import subprocess

from app.core import pdf_exporter


def test_is_libreoffice_available_returns_bool_without_raising() -> None:
    try:
        result = pdf_exporter.is_libreoffice_available()
    except Exception as exc:  # pragma: no cover - defensive assertion only
        raise AssertionError("Function should not raise") from exc

    assert isinstance(result, bool)


def test_find_libreoffice_path_returns_none_when_not_installed(
    monkeypatch,
) -> None:
    monkeypatch.setattr("app.core.pdf_exporter.os.path.exists", lambda _: False)

    result = pdf_exporter.find_libreoffice_path()

    assert result is None


def test_export_to_pdf_returns_false_for_nonexistent_pptx_file(tmp_path) -> None:
    result = pdf_exporter.export_to_pdf(
        str(tmp_path / "missing_file.pptx"),
        str(tmp_path),
    )

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
