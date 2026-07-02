# Bot AntiGravity - Auto Add Account

Bot otomatis untuk menambahkan akun Antigravity ke router Mikrotik (9Router).  
Dibangun dengan **Python + DrissionPage** untuk anti-detection dan stabilitas tinggi.

---

## Fitur

- **Anti-detection** - DrissionPage tidak pakai WebDriver, jadi lebih susah dideteksi
- **Text-based selector** - Cari elemen berdasarkan teks, bukan CSS selector panjang
- **Auto-installer** - Otomatis install DrissionPage kalau belum ada
- **Error handling** - Kalau 1 akun gagal, lanjut ke akun berikutnya
- **Headless mode** - Bisa jalan di background tanpa muncul browser
- **Cross-platform** - Jalan di Windows, Linux, dan Mac

---

## Instalasi

### Cara Cepat (Otomatis)

**Linux / Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
setup.bat
```

### Cara Manual

1. **Pastikan Python 3.8+ sudah terinstall:**
   ```bash
   python3 --version
   ```

2. **Install DrissionPage:**
   ```bash
   pip install DrissionPage
   ```
   > Atau biarkan saja, script akan otomatis install saat pertama kali dijalankan.

3. **Pastikan Google Chrome sudah terinstall** di komputer kamu.

---

## Cara Pakai

### 1. Siapkan File Akun

Buat file `akun.txt` di folder yang sama dengan `bot.py`:

```
user1@gmail.com|password123
user2@gmail.com|password456
user3@gmail.com|password789
```

> Format: `email|password` (pisahkan dengan tanda `|`)  
> Satu baris = satu akun

### 2. Jalankan Bot

**Mode Normal (dengan browser — RECOMMENDED):**
```bash
python3 bot.py
```

**Custom delay antar akun (contoh: 5 detik):**
```bash
python3 bot.py --delay 5
```

**Custom file akun:**
```bash
python3 bot.py --file /path/to/akun-lain.txt
```

**Kombinasi:**
```bash
python3 bot.py --delay 5 --file akun2.txt
```

> **Headless Mode (`--headless`):**  
> Fitur headless (jalan di background tanpa browser muncul) **sedang dalam perbaikan**.  
> Saat ini ada bug di mana Chrome headless kadang gagal connect ke WebSocket,  
> terutama kalau ada proses Chrome lama yang masih nyangkut.  
> **Gunakan mode normal (tanpa `--headless`) untuk hasil paling stabil.**  
> Kalau mau coba headless, pastikan kill semua proses Chrome dulu:
> ```bash
> pkill -f chromium  # Linux
> taskkill /F /IM chrome.exe  # Windows
> ```

### 3. Flow Bot

Bot akan secara otomatis:

1. Buka browser Chrome
2. Navigasi ke `http://localhost:20128/`
3. Klik menu **Provider**
4. Klik **Antigravity**
5. Klik tombol **Add** / **Add Connection**
6. Klik **I Understand** / **Continue** (modal konfirmasi)
7. Tunggu tab baru terbuka (Google Login)
8. Input **email** dan klik **Next**
9. Input **password** dan klik **Next**
10. Handle konfirmasi Google (I Understand, Allow, dll)
11. Kalau berhasil, hapus akun dari `akun.txt`
12. Close browser, delay, lanjut akun berikutnya

---

## Opsi Command Line

| Opsi | Default | Keterangan |
|------|---------|------------|
| `--headless` | `False` | Jalankan browser di background **(masih bug, lihat catatan di atas)** |
| `--delay` | `3` | Delay antar akun (detik) |
| `--file` | `akun.txt` | Path ke file akun |
| `--help` | - | Tampilkan bantuan |

---

## Troubleshooting

### 1. "DrissionPage belum terinstall"
Script akan otomatis install. Kalau gagal, install manual:
```bash
pip install DrissionPage
```

### 2. "File akun.txt tidak ditemukan"
Buat file `akun.txt` di folder yang sama dengan `bot.py` dengan format:
```
email@gmail.com|password
```

### 3. "Tidak bisa menemukan menu Provider"
- Pastikan router 9Router sudah jalan di `http://localhost:20128/`
- Coba buka URL tersebut di browser biasa dulu
- Pastikan halaman sudah full-loaded

### 4. "Tab Google Login tidak muncul"
- Pastikan popup/tab baru tidak diblokir
- Coba jalankan tanpa `--headless` untuk lihat apa yang terjadi

### 5. Google minta CAPTCHA
- Jangan jalankan terlalu banyak akun sekaligus
- Tambah delay: `--delay 10`
- Jalankan tanpa headless: bot lebih susah kena CAPTCHA kalau ada tampilan
- Pastikan akun tidak menyalakan 2FA (Two-Factor Authentication)

### 6. Browser Chrome tidak ditemukan
- Install Google Chrome
- Atau install Chromium:
  - Ubuntu/Debian: `sudo apt install chromium`
  - Mac: `brew install --cask chromium`
  - Windows: Download dari [google.com/chrome](https://www.google.com/chrome/)

### 7. Error "timeout" terus-menerus
- Kemungkinan koneksi internet lambat, coba tambah delay
- UI router mungkin berubah, cek apakah teks menu masih sama
- Coba jalankan manual untuk debug:
  ```python
  from DrissionPage import ChromiumPage
  page = ChromiumPage()
  page.get('http://localhost:20128/')
  # Cek manual elemen-elemen yang ada
  ```

---

## Struktur File

```
project-folder/
  bot.py          # Script utama
  akun.txt        # Daftar akun (email|password) -- JANGAN COMMIT
  README.md       # Dokumentasi (file ini)
  .gitignore      # Ignore file sensitif
  setup.sh        # Setup script untuk Linux/Mac
  setup.bat       # Setup script untuk Windows
```

---

## Catatan Keamanan

- **JANGAN** commit `akun.txt` ke git (sudah di-ignore di `.gitignore`)
- **JANGAN** share file `akun.txt` ke orang lain
- Gunakan password yang kuat untuk setiap akun
- Pastikan koneksi internet aman saat menjalankan bot

---

## Requirements

- Python 3.8+
- Google Chrome / Chromium
- DrissionPage (auto-install)
- Koneksi internet
- 9Router berjalan di `http://localhost:20128/`

---
