@echo off
REM ══════════════════════════════════════════════════════════════════════════
REM  delivery_check.bat — USI Generator · Local CI Gate
REM
REM  Run this script at the END of every Codex delivery before committing.
REM  It mirrors exactly what GitHub Actions CI will run.
REM  If this script fails, do NOT push to main.
REM
REM  Usage:
REM    scripts\delivery_check.bat
REM    scripts\delivery_check.bat --fast   (skip integration tests)
REM ══════════════════════════════════════════════════════════════════════════

setlocal EnableDelayedExpansion

REM ── Configuration ──────────────────────────────────────────────────────────
set FAST_MODE=0
set COVERAGE_GLOBAL_MIN=80
set COVERAGE_CORE_MIN=100
set MAX_LINE_LENGTH=100
set PYTHONHASHSEED=0
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYTHON_EXE=python

if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
)

if "%1"=="--fast" set FAST_MODE=1

REM ── Tracking ───────────────────────────────────────────────────────────────
set PASS_COUNT=0
set FAIL_COUNT=0
set START_TIME=%TIME%

echo.
echo ══════════════════════════════════════════════════════════
echo   USI Generator — Delivery Check (Local CI Gate)
echo ══════════════════════════════════════════════════════════
echo   PYTHONHASHSEED=%PYTHONHASHSEED%
if %FAST_MODE%==1 echo   Mode: FAST (integration tests skipped)
echo.

REM ── Check if venv is active ────────────────────────────────────────────────
"%PYTHON_EXE%" -c "import sys; assert hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix), 'Not in venv'" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo   [WARN] Virtual environment not detected.
    echo          Run: .venv\Scripts\activate
    echo          Continuing anyway...
    echo.
)

REM ══════════════════════════════════════════════════════════════════════════
REM  STEP 1 — Architecture Rules
REM ══════════════════════════════════════════════════════════════════════════
echo ── Step 1/6: Architecture Rules ──────────────────────────────────────────
"%PYTHON_EXE%" scripts\check_architecture.py
if %ERRORLEVEL% NEQ 0 (
    echo   [FAIL] Architecture violations found. Fix before pushing.
    set /A FAIL_COUNT+=1
) else (
    echo   [PASS] Architecture rules OK
    set /A PASS_COUNT+=1
)
echo.

REM ══════════════════════════════════════════════════════════════════════════
REM  STEP 2 — Code Formatting (black)
REM ══════════════════════════════════════════════════════════════════════════
echo ── Step 2/6: Code Formatting (black) ─────────────────────────────────────
"%PYTHON_EXE%" -m black --check --diff app/ tests/ --quiet
if %ERRORLEVEL% NEQ 0 (
    echo   [FAIL] Formatting issues found.
    echo          Auto-fix with: black app/ tests/
    set /A FAIL_COUNT+=1
) else (
    echo   [PASS] black formatting OK
    set /A PASS_COUNT+=1
)
echo.

REM ══════════════════════════════════════════════════════════════════════════
REM  STEP 3 — Linting (flake8)
REM ══════════════════════════════════════════════════════════════════════════
echo ── Step 3/6: Linting (flake8) ────────────────────────────────────────────
"%PYTHON_EXE%" -m flake8 app/ tests/ --max-line-length=%MAX_LINE_LENGTH% --extend-ignore=E203,W503 --statistics
if %ERRORLEVEL% NEQ 0 (
    echo   [FAIL] Lint violations found.
    set /A FAIL_COUNT+=1
) else (
    echo   [PASS] flake8 lint OK
    set /A PASS_COUNT+=1
)
echo.

REM ══════════════════════════════════════════════════════════════════════════
REM  STEP 4 — Type Checking (mypy)
REM ══════════════════════════════════════════════════════════════════════════
echo ── Step 4/6: Type Checking (mypy) ────────────────────────────────────────
"%PYTHON_EXE%" -m mypy app\ --ignore-missing-imports --python-version=3.11 --no-error-summary
if %ERRORLEVEL% NEQ 0 (
    echo   [FAIL] Type errors found.
    set /A FAIL_COUNT+=1
) else (
    echo   [PASS] mypy type check OK
    set /A PASS_COUNT+=1
)
echo.

REM ══════════════════════════════════════════════════════════════════════════
REM  STEP 5 — Unit Tests + Coverage
REM ══════════════════════════════════════════════════════════════════════════
echo ── Step 5/6: Unit Tests ^& Coverage ──────────────────────────────────────
"%PYTHON_EXE%" -m pytest tests\unit\ ^
    --tb=short ^
    --cov=app ^
    --cov-report=term-missing ^
    --cov-fail-under=%COVERAGE_GLOBAL_MIN% ^
    -q
if %ERRORLEVEL% NEQ 0 (
    echo   [FAIL] Unit tests or coverage gate failed.
    echo          Coverage must be >= %COVERAGE_GLOBAL_MIN%%
    set /A FAIL_COUNT+=1
) else (
    echo   [PASS] Unit tests OK, coverage >= %COVERAGE_GLOBAL_MIN%%
    set /A PASS_COUNT+=1
)
echo.

REM ── Core coverage must be 100% ─────────────────────────────────────────────
"%PYTHON_EXE%" -m coverage report --include="app/core/*" --fail-under=%COVERAGE_CORE_MIN% -m
if %ERRORLEVEL% NEQ 0 (
    echo   [FAIL] app/core/ coverage below %COVERAGE_CORE_MIN%%
    echo          All public functions in core must be 100%% covered.
    set /A FAIL_COUNT+=1
)

REM ══════════════════════════════════════════════════════════════════════════
REM  STEP 6 — Integration Tests (skipped in --fast mode)
REM ══════════════════════════════════════════════════════════════════════════
echo ── Step 6/6: Integration Tests ───────────────────────────────────────────
if %FAST_MODE%==1 (
    echo   [SKIP] Integration tests skipped (--fast mode)
    echo          Run full check before merging to main.
    set /A PASS_COUNT+=1
    goto :summary
)

"%PYTHON_EXE%" -m pytest tests\integration\ --tb=short -q
if %ERRORLEVEL% NEQ 0 (
    echo   [FAIL] Integration tests failed.
    set /A FAIL_COUNT+=1
) else (
    echo   [PASS] Integration tests OK
    set /A PASS_COUNT+=1
)
echo.

REM ══════════════════════════════════════════════════════════════════════════
REM  SUMMARY
REM ══════════════════════════════════════════════════════════════════════════
:summary
echo.
echo ══════════════════════════════════════════════════════════
echo   DELIVERY CHECK SUMMARY
echo ══════════════════════════════════════════════════════════
echo   Passed : %PASS_COUNT% / 6
echo   Failed : %FAIL_COUNT% / 6
echo.

if %FAIL_COUNT% GTR 0 (
    echo   [BLOCKED] DELIVERY BLOCKED
    echo      %FAIL_COUNT% check(s) failed. Do NOT push to main.
    echo      Fix all failures and re-run: scripts\delivery_check.bat
    echo.
    exit /b 1
) else (
    echo   [APPROVED] DELIVERY APPROVED
    echo      All checks passed. Safe to commit and push to main.
    echo.
    echo   Next steps:
    echo     git add -A
    echo     git commit -m "feat: {short description of what was implemented}"
    echo     git push origin main
    echo.
    exit /b 0
)