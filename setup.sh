#!/bin/bash
# ============================================================
# Setup Script - Bot AntiGravity (Linux / Mac)
# Otomatis bikin virtual environment biar gak kena
# "externally-managed-environment" error di Debian 12+ / Ubuntu 23.04+
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "=============================================="
echo "  Bot AntiGravity - Setup"
echo "=============================================="
echo ""

# --- Cek Python ---
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "[ERROR] Python tidak ditemukan!"
    echo "        Install Python 3.8+ terlebih dahulu:"
    echo "        - Ubuntu/Debian: sudo apt install python3 python3-venv"
    echo "        - Mac: brew install python3"
    echo "        - Atau download dari https://python.org"
    exit 1
fi

echo "[OK] Python ditemukan: $($PYTHON --version)"

# --- Bikin virtual environment ---
echo ""
if [ -d "$VENV_DIR" ]; then
    echo "[OK] Virtual environment sudah ada di .venv/"
else
    echo "[INFO] Membuat virtual environment di .venv/ ..."
    $PYTHON -m venv "$VENV_DIR" 2>/dev/null || {
        echo ""
        echo "[ERROR] Gagal membuat venv!"
        echo "        Coba install dulu:"
        echo "        sudo apt install python3-venv"
        exit 1
    }
    echo "[OK] Virtual environment berhasil dibuat!"
fi

# --- Aktifkan venv & install ---
echo ""
echo "[INFO] Menginstall DrissionPage di venv..."
"$VENV_DIR/bin/pip" install --upgrade pip 2>/dev/null || true
"$VENV_DIR/bin/pip" install DrissionPage

echo ""
echo "[OK] DrissionPage berhasil diinstall!"

# --- Cek Google Chromes ---
echo ""
if command -v google-chrome &> /dev/null || command -v chromium-browser &> /dev/null || command -v chromium &> /dev/null; then
    echo "[OK] Chrome/Chromium ditemukan!"
else
    echo "[WARNING] Google Chrome tidak ditemukan di PATH."
    echo "          Install Chrome terlebih dahulu:"
    echo "          - Ubuntu: sudo apt install chromium-browser"
    echo "          - Mac: brew install --cask google-chrome"
    echo "          - Download: https://www.google.com/chrome/"
fi

# --- Cek akun.txt ---
echo ""
if [ -f "$SCRIPT_DIR/akun.txt" ]; then
    JUMLAH=$(grep -c '|' "$SCRIPT_DIR/akun.txt" 2>/dev/null || echo "0")
    echo "[OK] File akun.txt ditemukan ($JUMLAH akun)"
else
    echo "[INFO] File akun.txt belum ada."
    echo "       Buat file akun.txt dengan format:"
    echo "       email@gmail.com|password123"
    echo ""
    read -p "       Mau buat file contoh? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "contoh@gmail.com|passwordcontoh" > "$SCRIPT_DIR/akun.txt"
        echo "       [OK] File akun.txt contoh telah dibuat."
        echo "       Edit file tersebut dengan akun asli kamu."
    fi
fi

echo ""
echo "=============================================="
echo "  Setup selesai!"
echo ""
echo "  Cara jalankan (pilih salah satu):"
echo ""
echo "  1. Langsung (auto-detect venv):"
echo "     python3 bot.py"
echo ""
echo "  2. Pakai venv eksplisit:"
echo "     .venv/bin/python3 bot.py"
echo ""
echo "  Dengan headless mode:"
echo "     python3 bot.py --headless"
echo "=============================================="
