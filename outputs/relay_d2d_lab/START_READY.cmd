@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup.ps1"
  if errorlevel 1 (
    echo Setup failed. Check Python and Internet connection.
    pause
    exit /b 1
  )
)
start "Relay Lab Guide" "%~dp0Huong_dan_Relay_Lab_2_5_va_demo.pdf"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_lab.ps1"
pause
