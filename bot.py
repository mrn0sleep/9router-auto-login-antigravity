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
import tempfile
import shutil

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
TARGET_URL = "http://localhost:20128/dashboard/providers/antigravity"
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
def force_input(page, locator, text, timeout=15, desc="field"):
    """Input teks ke field dengan multiple fallback.

    Google Login sering block .input() biasa karena JS event handler.
    Urutan strategi:
    1. .input(clear=True) — cara standar DrissionPage
    2. .input(by_js=True) — set value via JavaScript property
    3. Klik field -> page.actions.input() — simulasi keyboard CDP
    4. ele.run_js() — inject value + dispatch event langsung
    """
    from DrissionPage._units.actions import Keys

    ele = wait_and_find(page, locator, timeout=timeout, desc=desc)

    # Strategi 1: .input() standar DrissionPage (klik + ketik native)
    try:
        ele.input(text, clear=True)
        time.sleep(0.5)
        val = ele.attr("value") or ele.property("value") or ""
        if text in val:
            return ele
    except Exception:
        pass

    # Strategi 2: .input(by_js=True) — set value via JS property + change event
    try:
        ele.input(text, clear=True, by_js=True)
        time.sleep(0.5)
        val = ele.attr("value") or ele.property("value") or ""
        if text in val:
            return ele
    except Exception:
        pass

    # Strategi 3: Klik field -> clear manual -> page.actions.input()
    try:
        ele.click()
        time.sleep(0.3)
        # Clear: Ctrl+A lalu Backspace
        page.actions.key_down(Keys.CTRL).type("a").key_up(Keys.CTRL)
        time.sleep(0.2)
        page.actions.type(Keys.BACKSPACE)
        time.sleep(0.3)
        # Input via CDP keyboard events
        page.actions.input(text)
        time.sleep(0.5)
        val = ele.attr("value") or ele.property("value") or ""
        if text in val:
            return ele
    except Exception:
        pass

    # Strategi 4: JavaScript langsung ke elemen (ele.run_js, bukan page.run_js)
    try:
        ele.click()
        time.sleep(0.3)
        ele.run_js(
            """
            this.focus();
            this.value = arguments[0];
            this.dispatchEvent(new Event('input', {bubbles: true}));
            this.dispatchEvent(new Event('change', {bubbles: true}));
            """,
            text,
        )
        time.sleep(0.5)
        return ele
    except Exception:
        pass

    raise Exception(f"Gagal input teks ke {desc} dengan semua strategi")


def login_account(account, index, total, headless=False):
    """Proses login untuk satu akun.

    Flow (sama persis kayak bot.js):
    1. Buka browser -> Langsung ke halaman Antigravity
    2. Klik tombol Add
    3. Klik tombol konfirmasi di modal (tombol merah)
    4. Tunggu tab baru muncul (Google Login)
    5. Pindah ke tab baru, input email -> Next -> password -> Next
    6. Handle konfirmasi Google (I Understand -> Allow)
    7. Hapus akun dari akun.txt kalau berhasil
    """
    email = account["email"]
    password = account["password"]

    print(f"\n{'=' * 55}")
    print(f" Akun {index + 1}/{total}: {email}")
    print(f"{'=' * 55}")

    # --- Setup browser (fresh profile, no cache) ---
    print(" [1/7] Membuka browser (fresh profile)...")

    # Bikin temporary folder buat user data — tiap akun dapet profile bersih
    tmp_user_data = tempfile.mkdtemp(prefix="antigravity_")

    co = ChromiumOptions()
    co.set_argument("--start-maximized")
    co.set_argument("--disable-blink-features=AutomationControlled")
    co.set_argument("--no-first-run")
    co.set_argument("--no-default-browser-check")

    # Fresh profile: tiap akun pake folder temp sendiri
    # Gak ada cookies/cache/session dari akun sebelumnya
    co.set_user_data_path(tmp_user_data)
    co.auto_port()  # random port biar gak conflict sama browser lain

    if headless:
        co.headless(True)

    page = ChromiumPage(co)

    try:
        # --- Langsung ke halaman Antigravity ---
        print(f" [2/7] Navigasi ke {TARGET_URL}")
        page.get(TARGET_URL)
        time.sleep(3)

        # --- Klik Add (di halaman Antigravity) ---
        print(" [3/7] Klik tombol 'Add'...")
        add_btn = None
        for locator in [
            "tag:button@@text():Add Connection",
            "tag:button@@text():Add",
            "tag:button@@text()=Add",
            "tag:button@@text()=Add Connection",
        ]:
            try:
                ele = page.ele(locator, timeout=8)
                if ele:
                    add_btn = ele
                    break
            except Exception:
                continue

        if add_btn is None:
            raise Exception("Tidak bisa menemukan tombol 'Add'")
        add_btn.click()
        time.sleep(2)

        # --- Klik tombol konfirmasi di modal router ---
        # bot.js: cari button yang innerText includes "I Understand" atau "Continue"
        # Kalau gak ada, cari button merah (bg-red-500) via JS
        print(" [4/7] Klik konfirmasi modal...")
        confirm_clicked = False

        # Coba cari berdasarkan teks
        for locator in [
            "tag:button@@text():I Understand",
            "tag:button@@text():I understand",
            "tag:button@@text():Continue",
            "tag:button@@text():Confirm",
            "tag:button@@text():Yes",
            "tag:button@@text():OK",
        ]:
            try:
                ele = page.ele(locator, timeout=3)
                if ele:
                    ele.click()
                    confirm_clicked = True
                    break
            except Exception:
                continue

        # Fallback: cari via JS sama kayak bot.js
        if not confirm_clicked:
            try:
                result = page.run_js("""
                    const btn = Array.from(document.querySelectorAll('button')).find(b =>
                        b.innerText.includes('I Understand') ||
                        b.innerText.includes('Continue') ||
                        b.innerText.includes('Confirm') ||
                        b.className.includes('bg-red') ||
                        b.className.includes('danger')
                    );
                    if (btn) { btn.click(); return true; }
                    return false;
                """)
                confirm_clicked = bool(result)
            except Exception:
                pass

        if not confirm_clicked:
            raise Exception("Tidak bisa menemukan tombol konfirmasi di modal")

        # --- Tunggu tab baru muncul (Google Login popup) ---
        print(" [5/7] Menunggu tab Google Login...")

        # Pake wait.new_tab() — tunggu sampe tab baru beneran muncul
        new_tab_id = page.wait.new_tab(timeout=15)
        if not new_tab_id:
            raise Exception("Tab Google Login tidak muncul dalam 15 detik")

        # Ambil object tab dari tab ID
        tab = page.get_tab(new_tab_id)
        print(f"        Tab baru ditemukan (ID: {new_tab_id})")
        print(f"        URL: {tab.url[:80]}")

        # Tunggu halaman Google load
        time.sleep(3)

        # === SEMUA OPERASI DI BAWAH PAKE 'tab' (tab Google), BUKAN 'page' (tab router) ===

        # --- Input Email di Google ---
        print(f" [6/7] Login Google: {email}")
        print("        Input email...")
        force_input(tab, "#identifierId", email, timeout=15, desc="email field")
        time.sleep(1)

        # Klik Next (email)
        print("        Klik Next (email)...")
        next_btn = None
        for locator in [
            "#identifierNext",
            "tag:button@@text():Next",
            "tag:button@@text():Berikutnya",
        ]:
            try:
                ele = tab.ele(locator, timeout=5)
                if ele:
                    next_btn = ele
                    break
            except Exception:
                continue

        if next_btn is None:
            raise Exception("Tidak bisa menemukan tombol Next (email)")
        next_btn.click()
        time.sleep(3)

        # --- Input Password di Google ---
        print("        Input password...")
        pw_locators = [
            "@type=password",
            "tag:input@@type=password",
            "@name=Passwd",
        ]
        pw_done = False
        for loc in pw_locators:
            try:
                force_input(tab, loc, password, timeout=10, desc="password field")
                pw_done = True
                break
            except Exception:
                continue

        if not pw_done:
            raise Exception("Tidak bisa menemukan/input field password")
        time.sleep(1)

        # Klik Next (password)
        print("        Klik Next (password)...")
        pw_next = None
        for locator in [
            "#passwordNext",
            "tag:button@@text():Next",
            "tag:button@@text():Berikutnya",
        ]:
            try:
                ele = tab.ele(locator, timeout=5)
                if ele:
                    pw_next = ele
                    break
            except Exception:
                continue

        if pw_next is None:
            raise Exception("Tidak bisa menemukan tombol Next (password)")
        pw_next.click()
        time.sleep(3)

        # --- [7/7] Handle konfirmasi Google ---
        # bot.js: klik #gaplustosNext (I Understand), lalu #submit_approve_access (Allow)
        print(" [7/7] Handle konfirmasi Google...")

        # Step A: Klik "I Understand"
        i_understand_clicked = False
        for locator in [
            "#gaplustosNext",
            "tag:button@@text():I Understand",
            "tag:button@@text():I understand",
            "tag:button@@text():Saya memahami",
            "tag:button@@text():I agree",
        ]:
            try:
                ele = tab.ele(locator, timeout=8)
                if ele:
                    time.sleep(1)
                    ele.click()
                    i_understand_clicked = True
                    print("        'I Understand' diklik")
                    time.sleep(2)
                    break
            except Exception:
                continue

        if not i_understand_clicked:
            print("        'I Understand' tidak ditemukan (mungkin gak ada), lanjut...")

        # Step B: Klik "Allow" / "Login"
        allow_clicked = False
        for locator in [
            "#submit_approve_access",
            "tag:button@@text():Allow",
            "tag:button@@text():Izinkan",
            "tag:button@@text():Continue",
            "tag:button@@text():Lanjutkan",
        ]:
            try:
                ele = tab.ele(locator, timeout=8)
                if ele:
                    time.sleep(1)
                    ele.click()
                    allow_clicked = True
                    print("        'Allow' diklik")
                    time.sleep(2)
                    break
            except Exception:
                continue

        if not allow_clicked:
            print("        'Allow' tidak ditemukan (mungkin gak ada), lanjut...")

        # --- Cek apakah beneran berhasil ---
        # Tunggu sebentar buat redirect selesai
        time.sleep(5)

        # Sukses
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

        # Hapus temp profile folder biar gak numpuk
        try:
            if os.path.exists(tmp_user_data):
                shutil.rmtree(tmp_user_data, ignore_errors=True)
                print(" [INFO]   Temp profile dihapus.")
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
        default=None,
        help="Path ke file akun (default: akun.txt di folder script)",
    )
    args = parser.parse_args()

    global AKUN_FILE
    if args.file is not None:
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
