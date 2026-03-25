@echo off
pyinstaller ^
  --onedir ^
  --windowed ^
  --collect-all PySide6 ^
  --name="USI Generator" ^
  main.py
