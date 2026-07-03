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
  - Fresh browser profile tiap akun (gak ada cache nyangkut)
  - 2 speed mode: --fast (internet cepat) dan default normal (internet lambat)
"""

# ============================================================
# AUTO-INSTALLER
# ============================================================
import os
import sys
import subprocess
import tempfile
import shutil
import random
import signal

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(SCRIPT_DIR, ".venv")


def _ensure_drissionpage():
    """Pastikan DrissionPage terinstall. Bikin venv kalau perlu."""
    try:
        import DrissionPage  # noqa: F401
        return
    except ImportError:
        pass

    print("=" * 50)
    print(" DrissionPage belum terinstall!")
    print(" Menginstall otomatis...")
    print("=" * 50)

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "DrissionPage"],
            stdout=sys.stdout, stderr=sys.stderr,
        )
        print("\n DrissionPage berhasil diinstall!\n")
        return
    except subprocess.CalledProcessError:
        pass

    print("\n [INFO] pip langsung gagal (externally-managed-environment)")
    print(" [INFO] Membuat virtual environment di .venv/ ...")

    try:
        subprocess.check_call(
            [sys.executable, "-m", "venv", VENV_DIR],
            stdout=sys.stdout, stderr=sys.stderr,
        )
    except subprocess.CalledProcessError:
        print("\n [ERROR] Gagal membuat venv!")
        print("          Coba: sudo apt install python3-venv")
        sys.exit(1)

    if sys.platform == "win32":
        venv_python = os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        venv_python = os.path.join(VENV_DIR, "bin", "python3")

    print(" [INFO] Menginstall DrissionPage di venv...")
    subprocess.check_call(
        [venv_python, "-m", "pip", "install", "--upgrade", "pip"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    subprocess.check_call(
        [venv_python, "-m", "pip", "install", "DrissionPage"],
        stdout=sys.stdout, stderr=sys.stderr,
    )

    print("\n DrissionPage berhasil diinstall di venv!")
    print(" [INFO] Menjalankan ulang bot dari venv...\n")
    os.execv(venv_python, [venv_python] + sys.argv)


_ensure_drissionpage()

from DrissionPage import ChromiumPage, ChromiumOptions  # noqa: E402
from DrissionPage._units.actions import Keys             # noqa: E402

import time      # noqa: E402
import argparse  # noqa: E402

# ============================================================
# KONFIGURASI
# ============================================================
TARGET_URL = "http://localhost:20128/dashboard/providers/antigravity"
AKUN_FILE = os.path.join(SCRIPT_DIR, "akun.txt")
DELAY_ANTAR_AKUN = 3

# ============================================================
# TIMING PROFILES
# ============================================================
# Localhost (9Router) selalu cepat di kedua mode.
# Perbedaan cuma di Google — normal lebih sabar nunggu loading.
#
# Cara pakai:
#   python bot.py              → mode NORMAL (default, internet lambat)
#   python bot.py --fast       → mode FAST (internet cepat)

TIMING = {
    "fast": {
        # --- Localhost (9Router) — selalu cepat ---
        "page_load":          1,     # tunggu halaman router load
        "after_add_click":    1,     # setelah klik Add
        "after_confirm":      0.5,   # setelah klik konfirmasi modal
        "wait_new_tab":       10,    # timeout tunggu tab Google muncul
        # --- Google — cepat ---
        "google_initial":     1,     # tunggu tab Google pertama load
        "after_email_input":  0.5,   # setelah input email
        "after_email_next":   2,     # setelah klik Next (email) → tunggu password
        "password_timeout":   8,     # timeout cari field password
        "after_pw_input":     0.5,   # setelah input password
        "after_pw_next":      2,     # setelah klik Next (password) → tunggu konfirmasi
        "step_loop_wait":     1,     # jeda antar step di loop konfirmasi
        "tos_button_timeout": 3,     # timeout cari tombol di Workspace TOS
        "after_tos_click":    1,     # setelah klik I understand (TOS)
        "btn_find_timeout":   2,     # timeout cari tombol (Continue/Allow/dll)
        "after_consent_btn":  1,     # setelah klik tombol consent
        "after_allow":        1,     # setelah klik Allow
        "no_btn_wait":        2,     # tunggu kalau gak ada tombol ketemu
        "redirect_wait":      2,     # tunggu redirect selesai
        "after_success":      1,     # setelah sukses, sebelum tutup browser
    },
    "normal": {
        # --- Localhost (9Router) — tetap cepat ---
        "page_load":          1,     # tunggu halaman router load
        "after_add_click":    1,     # setelah klik Add
        "after_confirm":      0.5,   # setelah klik konfirmasi modal
        "wait_new_tab":       15,    # timeout tunggu tab Google muncul
        # --- Google — lebih sabar ---
        "google_initial":     3,     # tunggu tab Google pertama load
        "after_email_input":  1,     # setelah input email
        "after_email_next":   4,     # setelah klik Next (email) → tunggu password
        "password_timeout":   15,    # timeout cari field password
        "after_pw_input":     1,     # setelah input password
        "after_pw_next":      4,     # setelah klik Next (password) → tunggu konfirmasi
        "step_loop_wait":     2,     # jeda antar step di loop konfirmasi
        "tos_button_timeout": 5,     # timeout cari tombol di Workspace TOS
        "after_tos_click":    2,     # setelah klik I understand (TOS)
        "btn_find_timeout":   3,     # timeout cari tombol (Continue/Allow/dll)
        "after_consent_btn":  2,     # setelah klik tombol consent
        "after_allow":        3,     # setelah klik Allow
        "no_btn_wait":        3,     # tunggu kalau gak ada tombol ketemu
        "redirect_wait":      3,     # tunggu redirect selesai
        "after_success":      2,     # setelah sukses, sebelum tutup browser
    },
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def print_banner():
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
    if not os.path.exists(AKUN_FILE):
        print(f" [ERROR] File '{AKUN_FILE}' tidak ditemukan!")
        return []

    with open(AKUN_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    accounts = []
    for line in lines:
        if "|" not in line:
            continue
        parts = line.split("|", 1)
        email, password = parts[0].strip(), parts[1].strip()
        if email and password:
            accounts.append({"email": email, "password": password, "raw": line})
    return accounts


def remove_account(raw_line):
    if not os.path.exists(AKUN_FILE):
        return
    with open(AKUN_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    remaining = [line for line in lines if line.strip() != raw_line]
    with open(AKUN_FILE, "w", encoding="utf-8") as f:
        f.writelines(remaining)


def find_and_click(page_or_tab, locators, timeout=5, desc="element"):
    """Cari elemen dari list locator, klik yang pertama ketemu.
    Return True kalau berhasil klik, False kalau gak ketemu semua.
    """
    for locator in locators:
        try:
            ele = page_or_tab.ele(locator, timeout=timeout)
            if ele:
                ele.click()
                return True
        except Exception:
            continue
    return False


def force_input(page_or_tab, locator, text, timeout=15, desc="field"):
    """Input teks ke field dengan multiple fallback."""
    ele = page_or_tab.ele(locator, timeout=timeout)
    if ele is None:
        raise Exception(f"Elemen {desc} tidak ditemukan: {locator}")

    # Strategi 1: .input() standar
    try:
        ele.input(text, clear=True)
        time.sleep(0.5)
        val = ele.attr("value") or ele.property("value") or ""
        if text in val:
            return ele
    except Exception:
        pass

    # Strategi 2: .input(by_js=True)
    try:
        ele.input(text, clear=True, by_js=True)
        time.sleep(0.5)
        val = ele.attr("value") or ele.property("value") or ""
        if text in val:
            return ele
    except Exception:
        pass

    # Strategi 3: page.actions.input() via CDP keyboard
    try:
        ele.click()
        time.sleep(0.3)
        page_or_tab.actions.key_down(Keys.CTRL).type("a").key_up(Keys.CTRL)
        time.sleep(0.2)
        page_or_tab.actions.type(Keys.BACKSPACE)
        time.sleep(0.3)
        page_or_tab.actions.input(text)
        time.sleep(0.5)
        val = ele.attr("value") or ele.property("value") or ""
        if text in val:
            return ele
    except Exception:
        pass

    # Strategi 4: JavaScript langsung
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


# ============================================================
# FUNGSI UTAMA: LOGIN SATU AKUN
# ============================================================
def login_account(account, index, total, headless=False, t=None):
    """Proses login untuk satu akun. t = timing dict."""
    if t is None:
        t = TIMING["normal"]

    email = account["email"]
    password = account["password"]

    print(f"\n{'=' * 55}")
    print(f" Akun {index + 1}/{total}: {email}")
    print(f"{'=' * 55}")

    # --- [1/7] Setup browser (fresh profile) ---
    print(" [1/7] Membuka browser (fresh profile)...")
    tmp_user_data = tempfile.mkdtemp(prefix="antigravity_")

    co = ChromiumOptions()
    co.set_argument("--start-maximized")
    co.set_argument("--disable-blink-features=AutomationControlled")
    co.set_argument("--no-first-run")
    co.set_argument("--no-default-browser-check")
    co.set_user_data_path(tmp_user_data)
    co.set_local_port(random.randint(19200, 29200))

    if headless:
        co.headless(True)

    page = ChromiumPage(co)

    try:
        # --- [2/7] Navigasi ke halaman Antigravity ---
        print(f" [2/7] Navigasi ke {TARGET_URL}")
        page.get(TARGET_URL)
        time.sleep(t["page_load"])

        # --- [3/7] Klik Add ---
        print(" [3/7] Klik tombol 'Add'...")
        clicked = find_and_click(page, [
            "tag:button@@text():Add Connection",
            "tag:button@@text():Add",
            "tag:button@@text()=Add",
        ], timeout=1.5, desc="Add button")

        if not clicked:
            clicked = page.run_js("""
                const btn = Array.from(document.querySelectorAll('button'))
                    .find(b => b.textContent.trim().includes('Add'));
                if (btn) { btn.click(); return true; }
                return false;
            """)
        if not clicked:
            raise Exception("Tidak bisa menemukan tombol 'Add'")
        time.sleep(t["after_add_click"])

        # --- [4/7] Klik konfirmasi modal ---
        print(" [4/7] Klik konfirmasi modal...")

        # PENTING: catat tab yang ada SEBELUM klik konfirmasi,
        # karena tab Google bisa langsung kebuka setelah klik
        tabs_before = set(page.tab_ids)

        confirm_clicked = find_and_click(page, [
            "tag:button@@text():I Understand",
            "tag:button@@text():I understand",
            "tag:button@@text():Continue",
            "tag:button@@text():Confirm",
        ], timeout=1, desc="confirm button")

        if not confirm_clicked:
            confirm_clicked = page.run_js("""
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
        if not confirm_clicked:
            raise Exception("Tidak bisa menemukan tombol konfirmasi di modal")

        # --- [5/7] Tunggu tab baru (Google Login) ---
        # Tab Google bisa kebuka LANGSUNG setelah klik konfirmasi,
        # jadi kita cek dulu apakah udah ada tab baru sebelum pake wait.new_tab()
        print(" [5/7] Menunggu tab Google Login...")

        new_tab_id = None
        wait_timeout = t["wait_new_tab"]

        # Cara 1: Cek apakah tab baru udah ada (kebuka saat klik / sleep)
        for _ in range(3):
            time.sleep(0.5)
            tabs_now = set(page.tab_ids)
            new_tabs = tabs_now - tabs_before
            if new_tabs:
                new_tab_id = new_tabs.pop()
                break

        # Cara 2: Fallback ke wait.new_tab() kalau belum ada
        if not new_tab_id:
            new_tab_id = page.wait.new_tab(timeout=wait_timeout)

        # Cara 3: Last resort — cek semua tab, cari yang URL-nya Google
        if not new_tab_id:
            for tid in page.tab_ids:
                try:
                    t_tab = page.get_tab(tid)
                    if "accounts.google.com" in (t_tab.url or ""):
                        new_tab_id = tid
                        break
                except Exception:
                    continue

        if not new_tab_id:
            raise Exception(f"Tab Google Login tidak muncul dalam {wait_timeout} detik")

        tab = page.get_tab(new_tab_id)
        print(f"        Tab ditemukan: {tab.url[:70]}")
        time.sleep(t["google_initial"])

        # === Semua operasi Google pake 'tab', bukan 'page' ===

        # --- [6/7] Login Google ---
        print(f" [6/7] Login Google: {email}")

        # Input email
        print("        Input email...")
        force_input(tab, "#identifierId", email, timeout=15, desc="email field")
        time.sleep(t["after_email_input"])

        # Klik Next (email)
        print("        Klik Next (email)...")
        if not find_and_click(tab, [
            "#identifierNext",
            "tag:button@@text():Next",
            "tag:button@@text():Berikutnya",
        ], timeout=5, desc="Next button"):
            raise Exception("Tombol Next (email) tidak ditemukan")
        time.sleep(t["after_email_next"])

        # Input password
        print("        Input password...")
        pw_done = False
        for loc in ["@type=password", "tag:input@@type=password", "@name=Passwd"]:
            try:
                force_input(tab, loc, password, timeout=t["password_timeout"], desc="password field")
                pw_done = True
                break
            except Exception:
                continue
        if not pw_done:
            raise Exception("Field password tidak ditemukan")
        time.sleep(t["after_pw_input"])

        # Klik Next (password)
        print("        Klik Next (password)...")
        if not find_and_click(tab, [
            "#passwordNext",
            "tag:button@@text():Next",
            "tag:button@@text():Berikutnya",
        ], timeout=5, desc="Next button"):
            raise Exception("Tombol Next (password) tidak ditemukan")
        time.sleep(t["after_pw_next"])

        # --- [7/7] Handle konfirmasi Google ---
        # Setelah masukin password + Next, Google bisa menampilkan
        # beberapa halaman secara BERURUTAN:
        #
        #   Halaman 1 (akun pertama kali login):
        #     "Welcome to your new account" (Workspace Terms of Service)
        #     URL: accounts.google.com/v3/signin/speedbump/workspacetermsofservice
        #     → harus klik "I understand"
        #
        #   Halaman 2 (selalu muncul):
        #     "Make sure that you downloaded this app from Google"
        #     → harus klik/konfirmasi (Continue / Allow / dll)
        #
        #   Setelah itu langsung redirect balik ke 9Router = SUKSES
        #
        # Strategi: loop cek halaman satu-satu, handle sesuai URL/konten,
        # sampai redirect balik ke router atau timeout.
        print(" [7/7] Handle konfirmasi Google...")

        MAX_STEPS = 10
        step_count = 0

        while step_count < MAX_STEPS:
            step_count += 1
            time.sleep(t["step_loop_wait"])

            # Cek apakah tab masih ada
            try:
                current_url = tab.url
            except Exception:
                # Tab udah nutup = redirect sukses
                print("        Tab Google udah nutup (redirect sukses)")
                break

            # Cek apakah udah balik ke router (bukan google lagi)
            if "accounts.google.com" not in current_url and "google.com" not in current_url:
                print(f"        Redirect ke non-Google: {current_url[:70]}")
                break

            print(f"        [Step {step_count}] URL: {current_url[:80]}")

            # ── Halaman: Workspace Terms of Service ──
            # "Welcome to your new account" → klik "I understand"
            if "workspacetermsofservice" in current_url or "speedbump" in current_url:
                print("        >> Halaman 'Welcome to your new account' terdeteksi")
                handled = find_and_click(tab, [
                    "tag:button@@text():I understand",
                    "tag:button@@text():I Understand",
                    "tag:button@@text():Accept",
                    "tag:button@@text():Saya memahami",
                    "tag:input@@type=submit",
                ], timeout=t["tos_button_timeout"], desc="I understand (Workspace TOS)")

                if not handled:
                    handled = tab.run_js("""
                        window.scrollTo(0, document.body.scrollHeight);
                        const btn = Array.from(document.querySelectorAll('button, input[type="submit"]'))
                            .find(el => {
                                const t = (el.innerText || el.value || '').toLowerCase();
                                return t.includes('i understand') || t.includes('accept')
                                    || t.includes('saya memahami');
                            });
                        if (btn) { btn.click(); return true; }
                        return false;
                    """)

                if handled:
                    print("        >> 'I understand' (Workspace TOS) diklik!")
                    time.sleep(t["after_tos_click"])
                    continue
                else:
                    print("        >> [WARN] Tombol di Workspace TOS gak ketemu, coba lanjut...")
                    continue

            # ── Halaman: OAuth consent / "Make sure..." / Allow ──
            if "oauthchooseaccount" in current_url or "consent" in current_url \
               or "signin/oauth" in current_url or "approval" in current_url:
                print("        >> Halaman OAuth consent terdeteksi")

            # Coba cari dan klik tombol-tombol yang mungkin muncul, satu per satu

            # Coba 1: "Continue" / "Make sure..." confirmation
            clicked = find_and_click(tab, [
                "tag:button@@text():Continue",
                "tag:button@@text():Lanjutkan",
            ], timeout=t["btn_find_timeout"], desc="Continue")
            if clicked:
                print("        >> 'Continue' diklik!")
                time.sleep(t["after_consent_btn"])
                continue

            # Coba 2: "I Understand" / "I understand" (generic)
            clicked = find_and_click(tab, [
                "#gaplustosNext",
                "tag:button@@text():I Understand",
                "tag:button@@text():I understand",
                "tag:button@@text():Saya memahami",
                "tag:button@@text():I agree",
                "tag:button@@text():Saya setuju",
                "tag:a@@text():I Understand",
                "tag:a@@text():I understand",
            ], timeout=t["btn_find_timeout"], desc="I Understand")
            if clicked:
                print("        >> 'I Understand' diklik!")
                time.sleep(t["after_consent_btn"])
                continue

            # Coba 3: "Allow" / "Izinkan"
            clicked = find_and_click(tab, [
                "#submit_approve_access",
                "tag:button@@text():Allow",
                "tag:button@@text():Izinkan",
            ], timeout=t["btn_find_timeout"], desc="Allow")
            if clicked:
                print("        >> 'Allow' diklik!")
                time.sleep(t["after_allow"])
                continue

            # Coba 4: Checkbox yang perlu dicentang
            try:
                tab.run_js("""
                    document.querySelectorAll('input[type="checkbox"]:not(:checked)')
                        .forEach(cb => cb.click());
                """)
            except Exception:
                pass

            # Coba 5: Fallback JS — cari APAPUN yang bisa diklik
            try:
                clicked = tab.run_js("""
                    const keywords = [
                        'i understand', 'saya memahami',
                        'continue', 'lanjutkan',
                        'allow', 'izinkan',
                        'accept', 'terima',
                        'i agree', 'saya setuju',
                        'confirm', 'konfirmasi',
                        'next', 'berikutnya',
                    ];
                    const btn = Array.from(document.querySelectorAll('button, a, input[type="submit"]'))
                        .find(el => {
                            const text = (el.innerText || el.value || el.textContent || '').toLowerCase().trim();
                            return keywords.some(kw => text.includes(kw));
                        });
                    if (btn) { btn.click(); return true; }
                    return false;
                """)
            except Exception:
                clicked = False
            if clicked:
                print("        >> Tombol diklik (via JS fallback)!")
                time.sleep(t["after_consent_btn"])
                continue

            # Gak ada yang bisa diklik di iterasi ini
            print(f"        >> [WAIT] Gak ada tombol, tunggu...")
            time.sleep(t["no_btn_wait"])

        if step_count >= MAX_STEPS:
            raise Exception(
                f"Terlalu banyak step konfirmasi Google ({MAX_STEPS}x) — "
                "kemungkinan stuck di halaman yang gak dikenal"
            )

        # --- Verifikasi: tunggu redirect dan cek tab Google nutup ---
        print("        Menunggu redirect selesai...")
        time.sleep(t["redirect_wait"])

        # Cek apakah tab Google udah nutup (redirect balik ke router = sukses)
        try:
            current_tabs = page.tab_ids
            google_still_open = new_tab_id in current_tabs
            if google_still_open:
                try:
                    current_url = tab.url
                    if "accounts.google.com" in current_url:
                        raise Exception(
                            f"Masih di halaman Google ({current_url[:60]}) — "
                            "kemungkinan login gagal atau ada step tambahan"
                        )
                except Exception as e:
                    if "login gagal" in str(e) or "Masih di halaman" in str(e):
                        raise
                    # Tab mungkin udah nutup tapi masih kedetect
        except Exception as e:
            if "login gagal" in str(e) or "Masih di halaman" in str(e):
                raise
            pass  # Error lain = tab udah nutup = kemungkinan sukses

        # --- SUKSES ---
        print(f"\n [SUKSES] Akun {index + 1}/{total}: {email}")
        remove_account(account["raw"])
        print(f" [INFO]   Akun dihapus dari akun.txt")
        time.sleep(t["after_success"])

    except Exception as e:
        print(f"\n [GAGAL] Akun {index + 1}/{total}: {email}")
        print(f"          Error: {str(e)}")

    finally:
        try:
            page.quit()
            print(" [INFO]   Browser ditutup.")
        except Exception:
            pass
        try:
            if os.path.exists(tmp_user_data):
                shutil.rmtree(tmp_user_data, ignore_errors=True)
        except Exception:
            pass


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Bot AntiGravity - Auto Add Account ke Router"
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Jalankan browser di background (tanpa tampilan)",
    )
    parser.add_argument(
        "--fast", action="store_true",
        help="Mode cepat (internet bagus, delay minimal di Google)",
    )
    parser.add_argument(
        "--delay", type=int, default=DELAY_ANTAR_AKUN,
        help=f"Delay antar akun dalam detik (default: {DELAY_ANTAR_AKUN})",
    )
    parser.add_argument(
        "--file", type=str, default=None,
        help="Path ke file akun (default: akun.txt di folder script)",
    )
    args = parser.parse_args()

    global AKUN_FILE
    if args.file is not None:
        AKUN_FILE = args.file

    speed_mode = "fast" if args.fast else "normal"
    t = TIMING[speed_mode]

    print_banner()

    # Kill zombie Chrome dari run sebelumnya yang masih nyangkut
    try:
        if sys.platform != "win32":
            os.system("pkill -f 'chromium.*antigravity_' 2>/dev/null")
            os.system("pkill -f 'chrome.*antigravity_' 2>/dev/null")
        import glob
        for old_tmp in glob.glob(os.path.join(tempfile.gettempdir(), "antigravity_*")):
            try:
                shutil.rmtree(old_tmp, ignore_errors=True)
            except Exception:
                pass
    except Exception:
        pass

    accounts = read_accounts()
    if not accounts:
        print("\n [INFO] Tidak ada akun yang bisa diproses.")
        print("        Pastikan file akun.txt ada dan berisi: email|password")
        sys.exit(1)

    print(f"\n Total akun: {len(accounts)}")
    print(f" Speed mode: {speed_mode.upper()}")
    print(f" Headless mode: {'YA' if args.headless else 'TIDAK'}")
    print(f" Delay antar akun: {args.delay} detik")
    print(f" File akun: {AKUN_FILE}")
    print()

    sukses = 0
    gagal = 0

    for i, account in enumerate(accounts):
        login_account(account, i, len(accounts), headless=args.headless, t=t)

        remaining = read_accounts()
        if account["raw"] not in [a["raw"] for a in remaining]:
            sukses += 1
        else:
            gagal += 1

        if i < len(accounts) - 1:
            print(f"\n [DELAY] Menunggu {args.delay} detik...")
            time.sleep(args.delay)

    print(f"\n{'=' * 55}")
    print(f" SELESAI!")
    print(f" Total  : {len(accounts)} akun")
    print(f" Sukses : {sukses} akun")
    print(f" Gagal  : {gagal} akun")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
