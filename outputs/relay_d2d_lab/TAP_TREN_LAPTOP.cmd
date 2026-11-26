@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup.ps1"
 if errorlevel 1 exit /b 1
)
set RELAY_LAB_PRACTICE=1
echo Open http://127.0.0.1:8877 - use loopback or replay.
".venv\Scripts\python.exe" -m uvicorn lab.server:app --host 127.0.0.1 --port 8877 --no-access-log
