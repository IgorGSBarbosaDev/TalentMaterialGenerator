@echo off
setlocal

set PYTHONUTF8=1
set PYTHON_EXE=python

if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
)

"%PYTHON_EXE%" scripts\check_architecture.py || exit /b 1
"%PYTHON_EXE%" -m black --check app tests || exit /b 1
"%PYTHON_EXE%" -m flake8 app tests --max-line-length=100 --extend-ignore=E203,W503 --jobs 1 || exit /b 1
"%PYTHON_EXE%" -m mypy app --ignore-missing-imports --python-version=3.11 --no-error-summary || exit /b 1
"%PYTHON_EXE%" -m pytest -q || exit /b 1

echo Delivery check passed.
