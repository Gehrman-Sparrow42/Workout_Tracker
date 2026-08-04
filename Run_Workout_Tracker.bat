@echo off
cd /d "%~dp0"
python -c "import flet" 2>nul
if %errorlevel% neq 0 (
    echo Installing required packages (flet)...
    pip install flet
)
start "" pythonw main.py
