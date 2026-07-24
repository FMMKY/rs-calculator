@echo off
cd /d %~dp0

where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher не найден.
  echo Установите Python 3.11 или новее с https://www.python.org/downloads/
  pause
  exit /b 1
)

if not exist .venv (
  py -3 -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run.py
pause
