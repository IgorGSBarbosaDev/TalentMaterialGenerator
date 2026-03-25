#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"


def _read_tree(path: Path):
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def check_no_legacy_imports() -> list[str]:
    violations: list[str] = []
    forbidden = ("customtkinter", "PIL", "app.core.image_utils")
    for py_file in APP.rglob("*.py"):
        tree = _read_tree(py_file)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(forbidden):
                        violations.append(f"{py_file}:{node.lineno}: legacy import {alias.name}")
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith(forbidden):
                    violations.append(f"{py_file}:{node.lineno}: legacy import {module}")
    return violations


def check_core_no_ui_imports() -> list[str]:
    violations: list[str] = []
    for py_file in (APP / "core").rglob("*.py"):
        tree = _read_tree(py_file)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith("app.ui"):
                    violations.append(f"{py_file}:{node.lineno}: core imports ui")
    return violations


def check_pyside_threading_contract() -> list[str]:
    worker_path = APP / "core" / "worker.py"
    source = worker_path.read_text(encoding="utf-8") if worker_path.exists() else ""
    violations: list[str] = []
    if "QThread" not in source or "Signal" not in source:
        violations.append("app/core/worker.py: missing QThread/Signal contract")
    return violations


def main() -> int:
    violations = []
    violations.extend(check_no_legacy_imports())
    violations.extend(check_core_no_ui_imports())
    violations.extend(check_pyside_threading_contract())

    if violations:
        for violation in violations:
            print(violation)
        return 1

    print("Architecture check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
