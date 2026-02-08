# 🏃 Garmin Authentication Tester

A simple toolkit to test Garmin Connect credentials and fetch recent activities. Perfect for verifying your Garmin API access before building integrations.

## 🎯 What This Does

- ✅ Tests authentication with Garmin Connect API
- ✅ Fetches your last 30 days of activities
- ✅ Shows distance, duration, calories, and more
- ✅ Two interfaces: Beautiful Web UI + Command Line
- ⚠️ **Does NOT store credentials** - testing only!

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip
- Valid Garmin Connect account (without 2FA)

### Install UV (if needed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 📋 Option 1: Web UI (Recommended)

**1. Start the server:**
```bash
uv run server.py
```

**2. Open your browser:**
```
http://localhost:8000
```

**3. Test your credentials:**
- Drag & drop your `creds.json` file, OR
- Enter email/password manually
- Click "Test Authentication"

**4. View results:**
- See your recent activities in a beautiful table
- View summary stats (distance, calories, etc.)

## 🖥️ Option 2: Command Line

**Test with JSON file:**
```bash
# Create your credentials file
cp creds.example.json creds.json
# Edit creds.json with your email/password

# Run the test
uv run cli_test.py --credentials creds.json
```

**Test with direct input:**
```bash
uv run cli_test.py --email your@email.com --password yourpass
```

**Fetch more days:**
```bash
uv run cli_test.py --credentials creds.json --days 60
```

## 📄 Credentials File Format

Create a `creds.json` file:
```json
{
  "email": "your-garmin-email@example.com",
  "password": "your-garmin-password"
}
```

## 🎨 Features

### Web UI
- 🖱️ Drag & drop JSON file support
- 📝 Manual credential entry
- 📊 Activity table with details
- 📈 Summary statistics
- 🎨 Beautiful gradient design
- ⚡ Real-time results

### Command Line
- 🎨 Rich formatted output
- 📊 Activity tables with colors
- 📈 Summary statistics
- ⚡ Fast and lightweight
- 🔧 Scriptable for automation

## ⚠️ Important Notes

### Security
- ✅ Credentials are sent **directly to Garmin API**
- ✅ Nothing is stored or logged
- ✅ Run locally on your machine
- ⚠️ Don't share your `creds.json` file!

### Limitations
- ❌ **No 2FA support** - Garmin accounts with 2-factor authentication won't work
- 💡 **Solution:** Create an app-specific password in Garmin settings
- 🔒 Use strong passwords and change them regularly

## 🐛 Troubleshooting

### "Authentication failed"
- Verify your email and password are correct
- Check if your account has 2FA enabled
- Try logging in at https://connect.garmin.com manually
- Consider using an app-specific password

### "No activities found"
- Your account might be new with no activities
- Try increasing the days parameter (--days 60)

### "Module not found" errors
- Make sure you have Python 3.11+: `python --version`
- Install UV: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- The script will auto-install dependencies

## 📦 What's Included

```
proto/authentication/
├── README.md              # This file
├── server.py              # Web UI server (FastAPI)
├── cli_test.py           # Command line tester
├── index.html            # Web interface
├── creds.example.json    # Template for credentials
└── pyproject.toml        # Python dependencies
```

## 🔧 Technical Details

- **Language:** Python 3.11+
- **Web Framework:** FastAPI
- **Garmin Library:** garminconnect 0.2.19
- **CLI Formatting:** Rich
- **Package Manager:** UV (with inline dependencies)

## 🚀 Next Steps

After verifying your credentials work:
1. Build your Garmin integration with confidence
2. Use the `garminconnect` library in your project
3. Store credentials securely (encrypted database recommended)
4. Implement proper authentication in production

## 📚 Resources

- [Garmin Connect](https://connect.garmin.com)
- [garminconnect Library](https://github.com/cyberjunky/python-garminconnect)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [UV Package Manager](https://github.com/astral-sh/uv)

## 📝 License

MIT License - Feel free to use and modify!

## 🤝 Contributing

Found a bug? Have a suggestion? Feel free to share!

---

**Made with ❤️ for the Garmin community**
