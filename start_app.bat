@echo off
REM Starts the Expense Tracker. Double-click this file, or run it from PowerShell.
REM It does NOT install anything and does NOT change your data.
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo The virtual environment ".venv" was not found.
    echo Please follow README.md, steps 3 to 5, first.
    pause
    exit /b 1
)
if not exist ".env" (
    echo The ".env" file was not found.
    echo Copy ".env.example" to ".env" and enter your MySQL details ^(README step 7^).
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
echo Starting server... open http://127.0.0.1:5000 in Chrome. Press Ctrl+C to stop.
python app.py
pause
