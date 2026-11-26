@echo off
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" scripts\reset_practice.py
) else (
  python scripts\reset_practice.py
)
set "result=%errorlevel%"
pause
exit /b %result%
