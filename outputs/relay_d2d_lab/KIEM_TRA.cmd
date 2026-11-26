@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\setup.ps1"
 if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -m pytest tests -q
if errorlevel 1 goto failed
".venv\Scripts\python.exe" scripts\reproduce_final.py
if errorlevel 1 goto failed
echo PASS
pause
exit /b 0
:failed
echo FAIL
pause
exit /b 1
