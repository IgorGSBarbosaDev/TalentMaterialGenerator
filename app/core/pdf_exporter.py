from __future__ import annotations

import os
import subprocess
from pathlib import Path

LIBREOFFICE_PATHS: list[str] = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]


def find_libreoffice_path() -> str | None:
    """Return the first known LibreOffice executable path found on the system."""
    for path in LIBREOFFICE_PATHS:
        if os.path.exists(path):
            return path
    return None


def is_libreoffice_available() -> bool:
    """Return True when a known LibreOffice executable path exists."""
    try:
        return find_libreoffice_path() is not None
    except Exception:
        return False


def try_comtypes_export(pptx_path: str, output_dir: str) -> bool:
    """Try PPTX to PDF conversion via Windows COM automation (PowerPoint)."""
    try:
        import comtypes.client  # type: ignore[import-not-found]
    except ImportError:
        return False

    powerpoint = None
    presentation = None

    try:
        os.makedirs(output_dir, exist_ok=True)
        pdf_path = os.path.join(output_dir, f"{Path(pptx_path).stem}.pdf")

        powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
        presentation = powerpoint.Presentations.Open(pptx_path, WithWindow=False)
        presentation.SaveAs(pdf_path, 32)

        return True
    except Exception:
        return False
    finally:
        try:
            if presentation is not None:
                presentation.Close()
        except Exception:
            presentation = None
        try:
            if powerpoint is not None:
                powerpoint.Quit()
        except Exception:
            powerpoint = None


def export_to_pdf(pptx_path: str, output_dir: str) -> bool:
    """Convert a PPTX file to PDF using LibreOffice first and COM as fallback."""
    try:
        if not os.path.exists(pptx_path):
            return False

        os.makedirs(output_dir, exist_ok=True)

        if not is_libreoffice_available():
            print("Warning: LibreOffice not found. Trying COM fallback.")
            return try_comtypes_export(pptx_path, output_dir)

        libreoffice_path = find_libreoffice_path()
        if libreoffice_path is None:
            print("Warning: LibreOffice not found. Trying COM fallback.")
            return try_comtypes_export(pptx_path, output_dir)

        cmd = [
            libreoffice_path,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            output_dir,
            pptx_path,
        ]
        subprocess.run(cmd, timeout=120, check=True)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    except Exception:
        return False
