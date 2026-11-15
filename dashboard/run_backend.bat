@echo off
cd /d "%~dp0.."
if not defined BETALENS_FACTOR_ROOT (
  echo Set BETALENS_FACTOR_ROOT to your research checkout.
  exit /b 1
)
".venv\Scripts\python.exe" -m dashboard.backend.cli serve --reload
