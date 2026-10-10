@echo off
setlocal
cd /d "%~dp0"
where pythonw.exe >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw.exe "%~dp0desktop_app.py"
) else (
    start "" python.exe "%~dp0desktop_app.py"
)
