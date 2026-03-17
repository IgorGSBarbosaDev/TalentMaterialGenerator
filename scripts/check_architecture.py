#!/usr/bin/env python3
"""
check_architecture.py — USI Generator Architecture Validator

Validates all architectural rules defined in:
  .github/instructions/copilot-instructions.md
  .github/instructions/core.instructions.md

Run manually : python scripts/check_architecture.py
Run in CI    : python scripts/check_architecture.py
Run threading: python scripts/check_architecture.py --check-threading

Exit codes:
  0 — all checks passed
  1 — one or more violations found
"""

import ast
import re
import sys
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal

# ─── Project root (script lives in scripts/, root is one level up) ────────────
ROOT = Path(__file__).parent.parent
APP  = ROOT / "app"

Severity = Literal["CRITICAL", "HIGH", "WARNING"]


@dataclass
class Violation:
    file: str
    line: int
    severity: Severity
    rule: str
    detail: str

    def __str__(self) -> str:
        badge = {"CRITICAL": "🔴", "HIGH": "🟠", "WARNING": "🟡"}[self.severity]
        return f"  {badge} [{self.severity}] {self.file}:{self.line}\n     Rule: {self.rule}\n     → {self.detail}"


@dataclass
class Report:
    violations: list[Violation] = field(default_factory=list)

    def add(self, file: str, line: int, severity: Severity, rule: str, detail: str) -> None:
        self.violations.append(Violation(file, line, severity, rule, detail))

    @property
    def criticals(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == "CRITICAL"]

    @property
    def highs(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == "HIGH"]

    @property
    def warnings(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == "WARNING"]

    def print_summary(self) -> None:
        if not self.violations:
            print("  ✅ No violations found.")
            return
        for v in self.violations:
            print(v)

    def has_blocking_violations(self) -> bool:
        """Returns True if there are CRITICAL or HIGH violations (CI should fail)."""
        return bool(self.criticals or self.highs)


# ─── RULE IMPLEMENTATIONS ─────────────────────────────────────────────────────

def check_no_ui_imports_in_core(report: Report) -> None:
    """CRITICAL: No app.ui or customtkinter imports inside app/core/ or app/config/."""
    forbidden_modules = ["app.ui", "customtkinter", "tkinter"]

    for py_file in sorted((APP / "core").rglob("*.py")):
        _check_imports_in_file(py_file, forbidden_modules, "CRITICAL",
            "Core must NOT import from UI or Tkinter", report)

    for py_file in sorted((APP / "config").rglob("*.py")):
        _check_imports_in_file(py_file, ["customtkinter"], "CRITICAL",
            "Config must NOT import customtkinter", report)


def _check_imports_in_file(
    py_file: Path,
    forbidden: list[str],
    severity: Severity,
    rule: str,
    report: Report,
) -> None:
    try:
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_file))
    except (SyntaxError, UnicodeDecodeError):
        return

    rel = str(py_file.relative_to(ROOT))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name.startswith(f) for f in forbidden):
                    report.add(rel, node.lineno, severity, rule,
                               f"'import {alias.name}' is forbidden here")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if any(module.startswith(f) for f in forbidden):
                report.add(rel, node.lineno, severity, rule,
                           f"'from {module} import ...' is forbidden here")


def check_slide_width_not_10_inches(report: Report) -> None:
    """CRITICAL: Inches(10) must never appear in generator_ficha.py."""
    target = APP / "core" / "generator_ficha.py"
    if not target.exists():
        return

    rel = str(target.relative_to(ROOT))
    pattern = re.compile(r"Inches\s*\(\s*10\s*\)")
    for i, line in enumerate(target.read_text(encoding="utf-8").splitlines(), start=1):
        if pattern.search(line):
            report.add(rel, i, "CRITICAL",
                "Slide width must be Inches(13.271), never Inches(10)",
                f"Found: {line.strip()!r} — replace with Inches(13.271)")


def check_ficha_title_color_is_not_84BD00(report: Report) -> None:
    """HIGH: Slide title in generator_ficha.py must use #92D050, not #84BD00."""
    target = APP / "core" / "generator_ficha.py"
    if not target.exists():
        return

    rel = str(target.relative_to(ROOT))
    lines = target.read_text(encoding="utf-8").splitlines()
    # Look for #84BD00 in contexts that suggest it's used as title/label color
    bad_pattern = re.compile(r'"#84BD00"', re.IGNORECASE)
    title_context = re.compile(
        r"(title|titulo|label|header|FORMAC|TRAJET|RESUMO|PERFORM|VERDE_TITULO|section)",
        re.IGNORECASE,
    )
    for i, line in enumerate(lines, start=1):
        if bad_pattern.search(line) and title_context.search(line):
            report.add(rel, i, "HIGH",
                "Slide section labels must use #92D050 (VERDE_SLIDE), not #84BD00",
                f"Found: {line.strip()!r}")


def check_no_builtin_hash_in_image_utils(report: Report) -> None:
    """HIGH: image_utils.py must use hashlib, never Python's built-in hash()."""
    target = APP / "core" / "image_utils.py"
    if not target.exists():
        return

    rel = str(target.relative_to(ROOT))
    pattern = re.compile(r"\bhash\s*\(")
    for i, line in enumerate(target.read_text(encoding="utf-8").splitlines(), start=1):
        if pattern.search(line) and "hashlib" not in line:
            report.add(rel, i, "HIGH",
                "Use hashlib.md5() for deterministic hashing, not Python's hash()",
                f"Found: {line.strip()!r}  — hash() is PYTHONHASHSEED-dependent")


def check_no_hardcoded_colors_in_ui(report: Report) -> None:
    """WARNING: UI files should import colors from theme.py, not hardcode hex."""
    ui_dir = APP / "ui"
    if not ui_dir.exists():
        return

    hex_pattern = re.compile(r'"#[0-9A-Fa-f]{6}"')
    # Allow theme.py itself to define them
    for py_file in sorted(ui_dir.rglob("*.py")):
        rel = str(py_file.relative_to(ROOT))
        for i, line in enumerate(py_file.read_text(encoding="utf-8").splitlines(), start=1):
            if hex_pattern.search(line) and "#" not in line.split("#")[0]:  # skip comments
                # Allow fg_color="#transparent" and similar
                match = hex_pattern.search(line)
                if match and "transparent" not in line.lower():
                    report.add(rel, i, "WARNING",
                        "Import colors from app.config.theme instead of hardcoding hex",
                        f"Found: {line.strip()!r}")


def check_no_bare_except(report: Report) -> None:
    """HIGH: No bare `except:` or `except Exception: pass` in the codebase."""
    for py_file in sorted(APP.rglob("*.py")):
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        rel = str(py_file.relative_to(ROOT))
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # Bare except:
                if node.type is None:
                    report.add(rel, node.lineno, "HIGH",
                        "No bare except: — always specify the exception type",
                        "Replace with: except SpecificError as e:")
                # except Exception: pass (silencing)
                elif (
                    isinstance(node.type, ast.Name)
                    and node.type.id == "Exception"
                    and len(node.body) == 1
                    and isinstance(node.body[0], ast.Pass)
                ):
                    report.add(rel, node.lineno, "HIGH",
                        "No silent exception swallowing (except Exception: pass)",
                        "At minimum: log the error with print() or a callback")


def check_threading_safety(report: Report) -> None:
    """HIGH: Workers (Thread targets) must not update Tkinter widgets directly."""
    ui_dir = APP / "ui"
    if not ui_dir.exists():
        return

    widget_update_pattern = re.compile(
        r"\.(configure|set|insert|delete|append)\s*\("
    )
    after_pattern = re.compile(r"self\.after\s*\(")

    for py_file in sorted(ui_dir.rglob("*.py")):
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        rel = str(py_file.relative_to(ROOT))
        lines = source.splitlines()

        # Find all functions that are used as Thread targets
        thread_targets: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                dump = ast.dump(node)
                if "Thread" in dump and "target" in dump:
                    for kw in node.keywords:
                        if kw.arg == "target":
                            if isinstance(kw.value, ast.Attribute):
                                thread_targets.add(kw.value.attr)
                            elif isinstance(kw.value, ast.Name):
                                thread_targets.add(kw.value.id)

        if not thread_targets:
            continue

        # Check those functions for widget updates
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in thread_targets:
                    for child in ast.walk(node):
                        if isinstance(child, ast.Expr):
                            child_src = lines[child.lineno - 1] if child.lineno <= len(lines) else ""
                            if widget_update_pattern.search(child_src):
                                if not after_pattern.search(child_src):
                                    report.add(rel, child.lineno, "HIGH",
                                        "Thread worker must NOT update widgets directly",
                                        f"Found in '{node.name}': {child_src.strip()!r}\n"
                                        "     → Use queue.Queue + after(100, _check_queue)")


def check_public_functions_have_type_hints(report: Report) -> None:
    """WARNING: All public functions in app/core/ must have type annotations."""
    for py_file in sorted((APP / "core").rglob("*.py")):
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        rel = str(py_file.relative_to(ROOT))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                # Check return annotation
                if node.returns is None:
                    report.add(rel, node.lineno, "WARNING",
                        "Public functions must have return type annotation",
                        f"def {node.name}(...) — missing return type")
                # Check argument annotations (skip self/cls)
                for arg in node.args.args:
                    if arg.arg in ("self", "cls"):
                        continue
                    if arg.annotation is None:
                        report.add(rel, node.lineno, "WARNING",
                            "Public functions must have parameter type annotations",
                            f"def {node.name}('{arg.arg}': ?) — missing type hint")


# ─── RUNNER ───────────────────────────────────────────────────────────────────

def run_all_checks(threading_only: bool = False) -> Report:
    report = Report()

    if threading_only:
        print("\n─── Threading Safety Check ───")
        check_threading_safety(report)
        return report

    checks = [
        ("No UI imports in core/config",       check_no_ui_imports_in_core),
        ("Slide width (must be 13.271\")",      check_slide_width_not_10_inches),
        ("Ficha title color (#92D050 only)",    check_ficha_title_color_is_not_84BD00),
        ("No builtin hash() in image_utils",   check_no_builtin_hash_in_image_utils),
        ("No hardcoded hex colors in UI",       check_no_hardcoded_colors_in_ui),
        ("No bare except clauses",              check_no_bare_except),
        ("Threading safety in UI workers",      check_threading_safety),
        ("Type hints on public core functions", check_public_functions_have_type_hints),
    ]

    for label, check_fn in checks:
        print(f"\n  ▸ Checking: {label}")
        check_fn(report)

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="USI Generator — Architecture Validator")
    parser.add_argument("--check-threading", action="store_true",
                        help="Run only the threading safety check (for CI step)")
    args = parser.parse_args()

    print("\n══════════════════════════════════════════════")
    print("  USI Generator — Architecture Validation")
    print("══════════════════════════════════════════════")

    if not APP.exists():
        print(f"\n  ⚠ app/ directory not found at {APP}")
        print("  Run this script from the project root.")
        return 1

    report = run_all_checks(threading_only=args.check_threading)

    print("\n──────────────────────────────────────────────")
    print("  RESULTS")
    print("──────────────────────────────────────────────")
    report.print_summary()

    total = len(report.violations)
    print(f"\n  Total: {total} violation(s)")
    print(f"    🔴 CRITICAL : {len(report.criticals)}")
    print(f"    🟠 HIGH     : {len(report.highs)}")
    print(f"    🟡 WARNING  : {len(report.warnings)}")

    if report.has_blocking_violations():
        print("\n  ❌ Architecture check FAILED — fix CRITICAL/HIGH violations before merging.")
        return 1
    elif report.warnings:
        print("\n  ⚠  Architecture check PASSED with warnings.")
        return 0
    else:
        print("\n  ✅ Architecture check PASSED — no violations.")
        return 0


if __name__ == "__main__":
    sys.exit(main())