@echo off
REM ============================================================
REM Setup Script - Bot AntiGravity (Windows)
REM Otomatis bikin virtual environment
REM ============================================================

echo ==============================================
echo   Bot AntiGravity - Setup
echo ==============================================
echo.

REM --- Cek Python ---
python --version >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python tidak ditemukan!
        echo         Download dan install Python 3.8+ dari:
        echo         https://www.python.org/downloads/
        echo.
        echo         PENTING: Centang "Add Python to PATH" saat install!
        pause
        exit /b 1
    )
    set PYTHON=python3
) else (
    set PYTHON=python
)

echo [OK] Python ditemukan
%PYTHON% --version
echo.

REM --- Bikin virtual environments ---
if exist ".venv\Scripts\python.exe" (
    echo [OK] Virtual environment sudah ada di .venv\
) else (
    echo [INFO] Membuat virtual environment di .venv\ ...
    %PYTHON% -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Gagal membuat venv!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment berhasil dibuat!
)
echo.

REM --- Install DrissionPage di venv ---
echo [INFO] Menginstall DrissionPage di venv...
.venv\Scripts\pip install --upgrade pip 2>nul
.venv\Scripts\pip install DrissionPage
echo.
echo [OK] DrissionPage berhasil diinstall!
echo.

REM --- Cek akun.txt ---
if exist "akun.txt" (
    echo [OK] File akun.txt ditemukan
) else (
    echo [INFO] File akun.txt belum ada.
    echo        Buat file akun.txt dengan format:
    echo        email@gmail.com^|password123
    echo.
    set /p BUAT="       Mau buat file contoh? (y/n): "
    if /i "%BUAT%"=="y" (
        echo contoh@gmail.com^|passwordcontoh> akun.txt
        echo        [OK] File akun.txt contoh telah dibuat.
        echo        Edit file tersebut dengan akun asli kamu.
    )
)

echo.
echo ==============================================
echo   Setup selesai!
echo.
echo   Cara jalankan (pilih salah satu):
echo.
echo   1. Langsung (auto-detect venv):
echo      python bot.py
echo.
echo   2. Pakai venv eksplisit:
echo      .venv\Scripts\python bot.py
echo.
echo   Dengan headless mode:
echo      python bot.py --headless
echo ==============================================
echo.
pause
