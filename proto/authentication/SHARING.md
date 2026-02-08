# 📦 Sharing Instructions

## For You (Sharing the Package)

### Option 1: Share as ZIP
```bash
cd /Users/anto/work/garmin-explorer
zip -r garmin-auth-tester.zip proto/authentication/
```

Send `garmin-auth-tester.zip` to your friends!

### Option 2: Upload to GitHub
```bash
cd /Users/anto/work/garmin-explorer/proto/authentication
git init
git add .
git commit -m "Initial commit: Garmin Auth Tester"
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

Share the GitHub repository link!

---

## For Your Friends (Using the Package)

### Prerequisites
1. **Python 3.11+** - Check: `python3 --version`
2. **UV package manager** - Install:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Getting Started

**If you received a ZIP:**
```bash
unzip garmin-auth-tester.zip
cd proto/authentication
```

**If from GitHub:**
```bash
git clone YOUR_GITHUB_REPO_URL garmin-auth-tester
cd garmin-auth-tester
```

### Running It

**Quick Start (Interactive):**
```bash
./start.sh
# Choose option 1 for Web UI or 2 for CLI
```

**Option 1: Web Interface**
```bash
uv run server.py
# Open http://localhost:8000 in browser
```

**Option 2: Command Line**
```bash
# Create credentials file
cp creds.example.json creds.json
# Edit creds.json with real credentials

# Run test
uv run cli_test.py --credentials creds.json
```

### What It Does
- ✅ Tests if your Garmin credentials work
- ✅ Fetches your last 30 days of activities
- ✅ Shows stats (distance, calories, duration)
- ⚠️ Does NOT store your credentials anywhere

### Troubleshooting
- **"Module not found"**: The script auto-installs dependencies with `uv run`
- **"Authentication failed"**: Check your email/password
- **"2FA error"**: Garmin accounts with 2FA need app-specific passwords
- **Port 8000 busy**: Change port in `server.py` (line with `port=8000`)

---

## Security Notes for Both
- 🔒 Credentials are NEVER stored
- ✅ Sent directly to Garmin API only
- 🏠 Everything runs locally on your machine
- 📝 Add `creds.json` to `.gitignore` (already done)
- ⚠️ Never commit real credentials to Git

---

## Package Contents
```
proto/authentication/
├── README.md              # Full documentation
├── SHARING.md             # This file
├── server.py              # Web UI server
├── cli_test.py           # Command line tool
├── index.html            # Web interface
├── start.sh              # Quick start script
├── creds.example.json    # Credentials template
├── pyproject.toml        # Dependencies
└── .gitignore           # Git ignore rules
```

---

## Support
Questions? Issues? Feel free to reach out!

**Happy Testing! 🏃‍♂️**
