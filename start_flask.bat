@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Membuat lingkungan Python...
  py -3 -m venv .venv
  if errorlevel 1 (
    echo Gagal membuat virtual environment. Pastikan Python terpasang.
    pause
    exit /b 1
  )
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Instalasi dependensi gagal.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" app.py
pause
