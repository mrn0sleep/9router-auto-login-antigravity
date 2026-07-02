#!/usr/bin/env python3
"""
Bot AntiGravity - Auto Add Account ke Router Mikrotik (9Router)
Refactored dari Node.js + Puppeteer ke Python + DrissionPage

Fitur:
  - Anti-detection (DrissionPage, bukan WebDriver/Selenium)
  - Text-based selector (gak pakai CSS selector panjang)
  - Auto-installer (otomatis install DrissionPage + bikin venv kalau perlu)
  - Error handling per-akun (1 gagal, lanjut ke berikutnya)
  - Cross-platform (Windows, Linux, Mac)
  - Headless mode (opsi jalan di background)
"""

# ============================================================
# AUTO-INSTALLER - Install DrissionPage otomatis kalau belum ada
# Kalau kena "externally-managed-environment" (Debian 12+/Ubuntu 23.04+),
# otomatis bikin virtual environment dan re-exec dari sana.
# ============================================================
import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(SCRIPT_DIR, ".venv")


def _ensure_drissionpage():
    """Pastikan DrissionPage terinstall. Bikin venv kalau perlu."""
    try:
        import DrissionPage  # noqa: F401
        return  # udah ada, lanjut
    except ImportError:
        pass

    print("=" * 50)
    print(" DrissionPage belum terinstall!")
    print(" Menginstall otomatis...")
    print("=" * 50)

    # Coba install langsung dulu (works di Mac, Windows, Linux tanpa PEP 668)
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "DrissionPage"],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        print("\n DrissionPage berhasil diinstall!\n")
        return
    except subprocess.CalledProcessError:
        pass

    # Gagal — kemungkinan besar kena externally-managed-environment
    # Bikin virtual environment otomatis
    print("\n [INFO] pip langsung gagal (kemungkinan externally-managed-environment)")
    print(" [INFO] Membuat virtual environment di .venv/ ...")

    # Pastikan python3-venv tersedia
    try:
        subprocess.check_call(
            [sys.executable, "-m", "venv", VENV_DIR],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
    except subprocess.CalledProcessError:
        print("\n [ERROR] Gagal membuat venv!")
        print("          Coba install dulu: sudo apt install python3-venv")
        sys.exit(1)

    # Tentukan path python di dalam venv
    if sys.platform == "win32":
        venv_python = os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        venv_python = os.path.join(VENV_DIR, "bin", "python3")

    # Install DrissionPage di dalam venv
    print(" [INFO] Menginstall DrissionPage di venv...")
    subprocess.check_call(
        [venv_python, "-m", "pip", "install", "--upgrade", "pip"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.check_call(
        [venv_python, "-m", "pip", "install", "DrissionPage"],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    print("\n DrissionPage berhasil diinstall di venv!")
    print(" [INFO] Menjalankan ulang bot dari venv...\n")

    # Re-exec script ini pakai python dari venv
    os.execv(venv_python, [venv_python] + sys.argv)
    # execv gak return — proses ini langsung diganti


_ensure_drissionpage()

from DrissionPage import ChromiumPage, ChromiumOptions  # noqa: E402

import time      # noqa: E402
import argparse  # noqa: E402

# ============================================================
# KONFIGURASI
# ============================================================
TARGET_URL = "http://localhost:20128/"
AKUN_FILE = os.path.join(SCRIPT_DIR, "akun.txt")
DELAY_ANTAR_AKUN = 3  # detik


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def print_banner():
    """Tampilkan banner aplikasi."""
    banner = r"""
    ___          __  _ ______                 _ __
   /   |  ____  / /_(_) ____/________ __   __(_) /___  __
  / /| | / __ \/ __/ / / __/ ___/ __ `/ | / / / __/ / / /
 / ___ |/ / / / /_/ / /_/ / /  / /_/ /| |/ / / /_/ /_/ /
/_/  |_/_/ /_/\__/_/\____/_/   \__,_/ |___/_/\__/\__, /
                                                 /____/
    Bot Auto Add Account - Python + DrissionPage
    """
    print(banner)
    print("=" * 55)


def read_accounts():
    """Baca daftar akun dari akun.txt.

    Format: email|password (1 baris = 1 akun)
    Baris kosong atau tanpa '|' akan di-skip.
    """
    if not os.path.exists(AKUN_FILE):
        print(f" [ERROR] File '{AKUN_FILE}' tidak ditemukan!")
        print("          Buat file akun.txt dengan format: email|password")
        return []

    with open(AKUN_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    accounts = []
    for line in lines:
        if "|" not in line:
            print(f" [SKIP] Format salah (kurang '|'): {line}")
            continue
        parts = line.split("|", 1)
        email = parts[0].strip()
        password = parts[1].strip()
        if email and password:
            accounts.append({"email": email, "password": password, "raw": line})
        else:
            print(f" [SKIP] Email/password kosong: {line}")

    return accounts


def remove_account(raw_line):
    """Hapus akun yang sudah berhasil login dari akun.txt."""
    if not os.path.exists(AKUN_FILE):
        return

    with open(AKUN_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    remaining = [line for line in lines if line.strip() != raw_line]

    with open(AKUN_FILE, "w", encoding="utf-8") as f:
        f.writelines(remaining)


def wait_and_find(page, locator, timeout=15, desc="element"):
    """Cari elemen dengan retry dan timeout.

    Kalau elemen gak ketemu dalam waktu timeout, raise exception.
    """
    ele = page.ele(locator, timeout=timeout)
    if ele is None:
        raise TimeoutError(f"Tidak bisa menemukan {desc} dengan locator: {locator}")
    return ele


def safe_click(page, locator, timeout=10, desc="button"):
    """Klik elemen dengan safety check."""
    ele = wait_and_find(page, locator, timeout=timeout, desc=desc)
    ele.click()
    return ele


# ============================================================
# FUNGSI UTAMA: LOGIN SATU AKUN
# ============================================================
def login_account(account, index, total, headless=False):
    """Proses login untuk satu akun.

    Flow:
    1. Buka browser -> Navigasi ke router
    2. Klik Provider -> Antigravity -> Add -> Confirm
    3. Handle tab baru (Google Login)
    4. Input email & password
    5. Handle konfirmasi Google
    6. Hapus akun dari akun.txt kalau berhasil
    """
    email = account["email"]
    password = account["password"]

    print(f"\n{'=' * 55}")
    print(f" Akun {index + 1}/{total}: {email}")
    print(f"{'=' * 55}")

    # --- Setup browser ---
    print(" [1/8] Membuka browser...")
    co = ChromiumOptions()
    co.set_argument("--start-maximized")
    co.set_argument("--disable-blink-features=AutomationControlled")
    co.set_argument("--no-first-run")
    co.set_argument("--no-default-browser-check")

    if headless:
        co.headless(True)

    page = ChromiumPage(co)

    try:
        # --- Navigasi ke router ---
        print(f" [2/8] Navigasi ke {TARGET_URL}")
        page.get(TARGET_URL)
        time.sleep(2)

        # --- Klik Provider ---
        print(" [3/8] Klik menu 'Provider'...")
        # Cari berdasarkan TEKS, bukan CSS selector
        provider_btn = None
        # Coba beberapa cara cari Provider
        for locator in [
            "@text()=Provider",
            "@text():Provider",
            "tag:a@@text():Provider",
            "tag:a@@text()=Provider",
        ]:
            try:
                ele = page.ele(locator, timeout=5)
                if ele:
                    provider_btn = ele
                    break
            except Exception:
                continue

        if provider_btn is None:
            raise Exception("Tidak bisa menemukan menu 'Provider'")
        provider_btn.click()
        time.sleep(2)

        # --- Klik Antigravity ---
        print(" [4/8] Klik 'Antigravity'...")
        antigravity_btn = None
        for locator in [
            "@text()=Antigravity",
            "@text():Antigravity",
            "tag:a@@text():Antigravity",
            "tag:h3@@text():Antigravity",
        ]:
            try:
                ele = page.ele(locator, timeout=5)
                if ele:
                    antigravity_btn = ele
                    break
            except Exception:
                continue

        if antigravity_btn is None:
            raise Exception("Tidak bisa menemukan 'Antigravity'")
        antigravity_btn.click()
        time.sleep(2)

        # --- Klik Add ---
        print(" [5/8] Klik tombol 'Add'...")
        add_btn = None
        for locator in [
            "tag:button@@text():Add Connection",
            "tag:button@@text():Add",
            "tag:button@@text()=Add",
            "tag:button@@text()=Add Connection",
        ]:
            try:
                ele = page.ele(locator, timeout=5)
                if ele:
                    add_btn = ele
                    break
            except Exception:
                continue

        if add_btn is None:
            raise Exception("Tidak bisa menemukan tombol 'Add'")
        add_btn.click()
        time.sleep(1)

        # --- Klik Confirm (I Understand / Continue) ---
        print(" [6/8] Klik konfirmasi (I Understand / Continue)...")
        confirm_btn = None
        for locator in [
            "tag:button@@text():I Understand",
            "tag:button@@text():Continue",
            "tag:button@@text():Confirm",
            "tag:button@@text():I understand",
        ]:
            try:
                ele = page.ele(locator, timeout=5)
                if ele:
                    confirm_btn = ele
                    break
            except Exception:
                continue

        if confirm_btn is None:
            raise Exception("Tidak bisa menemukan tombol konfirmasi")
        confirm_btn.click()

        # --- Tunggu tab baru (Google Login) ---
        print(" [7/8] Menunggu tab Google Login...")
        time.sleep(5)

        # Cari tab Google
        google_tab = None
        all_tabs = page.get_tabs()
        for tab in all_tabs:
            try:
                tab_url = tab.url if hasattr(tab, "url") else str(tab)
                if "google" in tab_url.lower() or "accounts.google" in tab_url.lower():
                    google_tab = tab
                    break
            except Exception:
                continue

        if google_tab is None:
            # Kalau gak ketemu via URL, coba ambil tab terakhir
            if len(all_tabs) > 1:
                google_tab = all_tabs[-1]
            else:
                raise Exception("Tab Google Login tidak muncul")

        # Pindah ke tab Google
        page.get_tab(google_tab)
        time.sleep(2)

        # --- Input Email ---
        print(f" [8/8] Login Google: {email}")
        print("        Input email...")
        email_field = wait_and_find(page, "#identifierId", timeout=15, desc="email field")
        email_field.clear()
        email_field.input(email)
        time.sleep(1)

        # Klik Next (email)
        print("        Klik Next...")
        next_btn = None
        for locator in [
            "#identifierNext",
            "tag:button@@text():Next",
            "tag:button@@text():Berikutnya",
        ]:
            try:
                ele = page.ele(locator, timeout=5)
                if ele:
                    next_btn = ele
                    break
            except Exception:
                continue

        if next_btn is None:
            raise Exception("Tidak bisa menemukan tombol Next (email)")
        next_btn.click()
        time.sleep(3)

        # --- Input Password ---
        print("        Input password...")
        pw_field = None
        for locator in [
            "@type=password",
            "#password input",
            "tag:input@@type=password",
            "@name=Passwd",
        ]:
            try:
                ele = page.ele(locator, timeout=10)
                if ele:
                    pw_field = ele
                    break
            except Exception:
                continue

        if pw_field is None:
            raise Exception("Tidak bisa menemukan field password")
        pw_field.clear()
        pw_field.input(password)
        time.sleep(1)

        # Klik Next (password)
        print("        Klik Next...")
        pw_next = None
        for locator in [
            "#passwordNext",
            "tag:button@@text():Next",
            "tag:button@@text():Berikutnya",
        ]:
            try:
                ele = page.ele(locator, timeout=5)
                if ele:
                    pw_next = ele
                    break
            except Exception:
                continue

        if pw_next is None:
            raise Exception("Tidak bisa menemukan tombol Next (password)")
        pw_next.click()
        time.sleep(3)

        # --- Handle konfirmasi Google ---
        print("        Handle konfirmasi Google...")

        # Klik "I Understand" / "I agree" di Google
        for locator in [
            "#gaplustosNext",
            "tag:button@@text():I Understand",
            "tag:button@@text():I understand",
            "tag:button@@text():Saya memahami",
            "tag:button@@text():I agree",
        ]:
            try:
                ele = page.ele(locator, timeout=5)
                if ele:
                    ele.click()
                    time.sleep(2)
                    break
            except Exception:
                continue

        # Klik "Allow" / "Login" / "Continue"
        for locator in [
            "#submit_approve_access",
            "tag:button@@text():Allow",
            "tag:button@@text():Izinkan",
            "tag:button@@text():Continue",
            "tag:button@@text():Lanjutkan",
        ]:
            try:
                ele = page.ele(locator, timeout=5)
                if ele:
                    ele.click()
                    time.sleep(2)
                    break
            except Exception:
                continue

        # --- SUKSES ---
        print(f"\n [SUKSES] Akun {index + 1}/{total} berhasil login: {email}")
        remove_account(account["raw"])
        print(f" [INFO]   Akun dihapus dari akun.txt")

        time.sleep(3)

    except Exception as e:
        print(f"\n [GAGAL] Akun {index + 1}/{total} gagal: {email}")
        print(f"          Error: {str(e)}")

    finally:
        # Pastikan browser ditutup
        try:
            page.quit()
            print(" [INFO]   Browser ditutup.")
        except Exception:
            pass


# ============================================================
# MAIN
# ============================================================
def main():
    """Entry point utama."""
    parser = argparse.ArgumentParser(
        description="Bot AntiGravity - Auto Add Account ke Router"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Jalankan browser di background (tanpa tampilan)",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=DELAY_ANTAR_AKUN,
        help=f"Delay antar akun dalam detik (default: {DELAY_ANTAR_AKUN})",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=AKUN_FILE,
        help=f"Path ke file akun (default: {AKUN_FILE})",
    )
    args = parser.parse_args()

    global AKUN_FILE
    AKUN_FILE = args.file

    print_banner()

    # Baca akun
    accounts = read_accounts()
    if not accounts:
        print("\n [INFO] Tidak ada akun yang bisa diproses.")
        print("        Pastikan file akun.txt ada dan berisi: email|password")
        sys.exit(1)

    print(f"\n Total akun: {len(accounts)}")
    print(f" Headless mode: {'YA' if args.headless else 'TIDAK'}")
    print(f" Delay antar akun: {args.delay} detik")
    print(f" File akun: {AKUN_FILE}")
    print()

    # Proses setiap akun
    sukses = 0
    gagal = 0

    for i, account in enumerate(accounts):
        login_account(account, i, len(accounts), headless=args.headless)

        # Re-read file buat cek apakah akun sudah dihapus (artinya sukses)
        remaining = read_accounts()
        if account["raw"] not in [a["raw"] for a in remaining]:
            sukses += 1
        else:
            gagal += 1

        # Delay antar akun (kecuali yang terakhir)
        if i < len(accounts) - 1:
            print(f"\n [DELAY] Menunggu {args.delay} detik sebelum akun berikutnya...")
            time.sleep(args.delay)

    # Summary
    print(f"\n{'=' * 55}")
    print(f" SELESAI!")
    print(f" Total  : {len(accounts)} akun")
    print(f" Sukses : {sukses} akun")
    print(f" Gagal  : {gagal} akun")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
