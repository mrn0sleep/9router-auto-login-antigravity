# AntiGravity Bot - Auto Add Account

Automated bot for adding Antigravity accounts to a Mikrotik router (9Router).
Built with **Python + DrissionPage** for anti-detection and high stability.

---

## Requirements

- Python 3.8+
- Google Chrome / Chromium
- DrissionPage (auto-install)
- Internet connection
- 9Router running at `http://localhost:20128/` also disable require login 
---

## Features

- **Anti-detection** - DrissionPage doesn't use WebDriver, making it harder to detect
- **Text-based selector** - Finds elements based on text, not long CSS selectors
- **Auto-installer** - Automatically installs DrissionPage if not already present
- **Error handling** - If one account fails, continues to the next account
- **Headless mode** - Can run in the background without showing the browser
- **Cross-platform** - Runs on Windows, Linux, and Mac
- **2 Speed Modes** - `--fast` for fast internet, default (normal) for slow/laggy internet
- **Smart Google Consent Handler** - Automatically handles multiple Google confirmation pages:
  - "Welcome to your new account" (Workspace Terms of Service)
  - "Make sure that you downloaded this app from Google"
  - OAuth consent (Allow/Continue)

---

## Installation

### Quick Method (Automatic)

**Linux / Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
setup.bat
```

### Manual Method

1. **Make sure Python 3.8+ is installed:**
   ```bash
   python3 --version
   ```

2. **Install DrissionPage:**
   ```bash
   pip install DrissionPage
   ```
   > Or just skip this — the script will auto-install it the first time it runs.

3. **Make sure Google Chrome is installed** on your computer.

---

## Usage

### 1. Prepare the Accounts File

Create an `akun.txt` file in the same folder as `bot.py`:

```
user1@gmail.com|password123
user2@gmail.com|password456
user3@gmail.com|password789
```

> Format: `email|password` (separated by a `|`)
> One line = one account

### 2. Run the Bot

**Normal Mode — internet lambat/ngelag (DEFAULT, RECOMMENDED):**
```bash
python3 bot.py
```

**Fast Mode — internet cepat:**
```bash
python3 bot.py --fast
```

**Custom delay between accounts (e.g., 5 seconds):**
```bash
python3 bot.py --delay 5
```

**Custom accounts file:**
```bash
python3 bot.py --file /path/to/other-accounts.txt
```

**Combined:**
```bash
python3 bot.py --fast --delay 5 --file akun2.txt
```

> **Headless Mode (`--headless`):**
> The headless feature (running in the background without the browser showing) is **currently under repair**.
> There's currently a bug where headless Chrome sometimes fails to connect to the WebSocket,
> especially if there's a leftover Chrome process still running.
> **Use normal mode (without `--headless`) for the most stable results.**
> If you want to try headless anyway, make sure to kill all Chrome processes first:
> ```bash
> pkill -f chromium  # Linux
> taskkill /F /IM chrome.exe  # Windows
> ```

### 3. Bot Flow

The bot will automatically:

1. Open the Chrome browser
2. Navigate to `http://localhost:20128/`
3. Click the **Provider** menu
4. Click **Antigravity**
5. Click the **Add** / **Add Connection** button
6. Click **I Understand** / **Continue** (confirmation modal)
7. Wait for a new tab to open (Google Login)
8. Enter the **email** and click **Next**
9. Enter the **password** and click **Next**
10. Handle Google confirmations (loops through all pages automatically):
    - **"Welcome to your new account"** (Workspace TOS) → clicks "I understand"
    - **"Make sure that you downloaded this app from Google"** → clicks Continue
    - **OAuth consent** → clicks Allow
11. If successful, remove the account from `akun.txt`
12. Close the browser, delay, then move to the next account

---

## Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--fast` | `False` | Fast mode — shorter delays for Google pages (use with good internet) |
| `--headless` | `False` | Run the browser in the background **(still buggy, see note above)** |
| `--delay` | `3` | Delay between accounts (seconds) |
| `--file` | `akun.txt` | Path to the accounts file |
| `--help` | - | Show help |

---

## Speed Mode Comparison

Localhost (9Router) timing is the same in both modes — it's always fast since it's local.
The difference is only on Google pages:

| Google Operation | `--fast` | Normal (default) |
|---|---|---|
| Google tab initial load | 1s | 3s |
| After email Next → wait password | 2s | 4s |
| Password field search timeout | 8s | 15s |
| After password Next → wait confirm | 2s | 4s |
| Confirmation loop interval | 1s | 2s |
| Workspace TOS button timeout | 8s | 12s |
| After TOS click | 2s | 4s |
| Consent button search timeout | 3s | 5s |
| Wait when no button found | 2s | 4s |
| After Allow click | 2s | 4s |
| Redirect wait | 3s | 5s |

> **Tip:** Start with normal mode (default). If everything runs smooth with no timeout errors, switch to `--fast`.

---

## Troubleshooting

### 1. "DrissionPage not installed"
The script will auto-install it. If that fails, install it manually:
```bash
pip install DrissionPage
```

### 2. "akun.txt file not found"
Create an `akun.txt` file in the same folder as `bot.py` with the format:
```
email@gmail.com|password
```

### 3. "Cannot find the Provider menu"
- Make sure the 9Router router is running at `http://localhost:20128/`
- Try opening that URL in a regular browser first
- Make sure the page has fully loaded

### 4. "Google Login tab doesn't appear"
- Make sure popups/new tabs aren't blocked
- Try running without `--headless` to see what's happening

### 5. Google asks for a CAPTCHA
- Don't run too many accounts at once
- Increase the delay: `--delay 10`
- Run without headless: the bot is less likely to trigger a CAPTCHA when the UI is visible
- Make sure the accounts don't have 2FA (Two-Factor Authentication) enabled

### 6. Chrome browser not found
- Install Google Chrome
- Or install Chromium:
  - Ubuntu/Debian: `sudo apt install chromium`
  - Mac: `brew install --cask chromium`
  - Windows: Download from [google.com/chrome](https://www.google.com/chrome/)

### 7. Persistent "timeout" errors
- Might be a slow internet connection — make sure you're using normal mode (without `--fast`)
- If still timing out on normal mode, the delays might need to be increased in the `TIMING` dict inside `bot.py`
- The router UI may have changed — check if the menu text is still the same
- Try running it manually to debug:
  ```python
  from DrissionPage import ChromiumPage
  page = ChromiumPage()
  page.get('http://localhost:20128/')
  # Manually inspect the elements present
  ```

### 8. "The connection to the page has been disconnected"
- This usually happens when internet is laggy and the bot tries to interact with a page that hasn't loaded yet
- Switch from `--fast` to normal mode (remove the `--fast` flag)
- If already on normal mode, you may need to increase the timing values in `bot.py`

---

## File Structure

```
project-folder/
  bot.py          # Main script
  akun.txt        # Account list (email|password) -- DO NOT COMMIT
  README.md       # Documentation (this file)
  .gitignore      # Ignore sensitive files
  setup.sh        # Setup script for Linux/Mac
  setup.bat       # Setup script for Windows
```

---

## Security Notes

- **DO NOT** commit `akun.txt` to git (already ignored in `.gitignore`)
- **DO NOT** share the `akun.txt` file with anyone else
- Use a strong password for each account
- Make sure your internet connection is secure while running the bot

---

## Requirements

- Python 3.8+
- Google Chrome / Chromium
- DrissionPage (auto-install)
- Internet connection
- 9Router running at `http://localhost:20128/`

---