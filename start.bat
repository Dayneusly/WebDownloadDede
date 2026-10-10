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

echo Memasang atau memperbarui dependensi...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Instalasi dependensi gagal. Periksa koneksi internet atau pesan pip di atas.
  pause
  exit /b 1
)

echo.
echo Membuka WebDownloadDede Streamlit di http://127.0.0.1:8501
".venv\Scripts\python.exe" -m streamlit run streamlit_app.py --server.address=127.0.0.1 --server.port=8501 --server.headless=true --browser.gatherUsageStats=false
pause


