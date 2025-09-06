# Garmin Explorer 🏃‍♂️📊

A comprehensive Python tool for analyzing and visualizing your Garmin Connect data. Extract insights from your running activities, sleep patterns, daily steps, and more with beautiful charts and detailed statistics.

## Features

### 🏃‍♂️ Activity Analysis
- **Running Statistics**: Total distance, average pace, longest runs
- **Monthly Trends**: Track your monthly running volume and patterns
- **Activity Breakdown**: Analyze different types of activities

### 😴 Sleep Analysis
- **Sleep Duration Patterns**: Track your sleep consistency
- **Sleep Stages**: Deep sleep, light sleep, and REM analysis
- **Sleep Quality**: Efficiency scores and recommendations
- **Interactive Dashboards**: Beautiful visualizations with Plotly

### 👣 Daily Activity
- **Steps Analysis**: Daily step counts and trends
- **Activity Goals**: Track progress toward 10,000+ step goals

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management.

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- A Garmin Connect account with activity data

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/garmin-explorer.git
   cd garmin-explorer
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Set up your credentials**:
   ```bash
   cp .env.example .env
   # Edit .env with your Garmin Connect credentials
   ```

## Usage

### Basic Activity Analysis

Run the main analysis script to get comprehensive insights into your Garmin data:

```bash
uv run python example.py
```

This will:
- Connect to your Garmin account
- Fetch activity data from the last year
- Analyze running statistics and trends
- Generate monthly trend charts
- Analyze daily steps patterns
- Create visualizations saved as PNG files

### Sleep Analysis

For detailed sleep analysis with interactive charts:

```bash
uv run python sleep_analysis.py
```

This will:
- Fetch sleep data from the last 90 days
- Analyze sleep duration, stages, and efficiency
- Create an interactive HTML dashboard
- Generate detailed sleep pattern visualizations

### Sample Output

**Running Statistics:**
```
🏃‍♂️ RUNNING STATISTICS
==================================================
📈 Total kilometers run: 845.2 km
🏃 Total number of runs: 156
📏 Average distance per run: 5.4 km
⏱️  Total running time: 78.3 hours
⚡ Average pace: 5.56 min/km
🏆 Longest run: 21.1 km on 2024-10-15
```

**Monthly Trends:**
```
📅 MONTHLY RUNNING TRENDS
==================================================
Monthly Summary:
  2024-01: 67.3 km, 14 runs, 6.2h
  2024-02: 89.1 km, 18 runs, 8.1h
  2024-03: 92.4 km, 16 runs, 8.8h
```

## Configuration

### Environment Variables

Create a `.env` file (copied from `.env.example`) with your settings:

```bash
# Garmin Connect Credentials
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_password

# Analysis Settings
DEFAULT_ANALYSIS_DAYS=365
DEFAULT_SLEEP_ANALYSIS_DAYS=90
```

### Security Note

⚠️ **Never commit your `.env` file to version control!** Your Garmin credentials should be kept private.

## Generated Files

The analysis scripts create several output files:

### Activity Analysis
- `monthly_running_trends.png` - Monthly distance and run count charts
- `daily_steps.png` - Daily step count trends

### Sleep Analysis
- `sleep_analysis_dashboard.html` - Interactive sleep dashboard (open in browser)
- `detailed_sleep_analysis.png` - Detailed sleep pattern charts

## Dependencies

This project uses several key libraries:

- **garminconnect** - Python library for Garmin Connect API
- **pandas** - Data analysis and manipulation
- **matplotlib** - Static plotting and visualization
- **seaborn** - Statistical data visualization
- **plotly** - Interactive charts and dashboards
- **python-dateutil** - Date/time utilities

## Project Structure

```
garmin-explorer/
├── README.md              # This file
├── pyproject.toml         # Project configuration and dependencies
├── .env.example           # Example environment configuration
├── example.py             # Main activity analysis script
├── sleep_analysis.py      # Dedicated sleep analysis script
└── .venv/                 # Virtual environment (created by uv)
```

## Troubleshooting

### Authentication Issues

If you encounter authentication problems:

1. **Two-Factor Authentication**: Garmin Connect 2FA may cause issues. Try using an app-specific password if available.
2. **Rate Limiting**: If you get rate-limited, wait a few minutes before retrying.
3. **Account Locked**: Too many failed attempts may temporarily lock your account.

### Data Issues

If no data is returned:
1. Check that you have activities in your Garmin Connect account
2. Verify the date range (default is last 365 days)
3. Ensure your activities are synced to Garmin Connect

### Common Errors

**`ModuleNotFoundError`**: Make sure you're using the virtual environment:
```bash
uv run python example.py  # Use uv run
```

**`Permission Denied`**: Make sure scripts are executable:
```bash
chmod +x example.py sleep_analysis.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. Some areas for improvement:

- Add more activity types (cycling, swimming, etc.)
- Implement heart rate analysis
- Add nutrition and hydration tracking
- Create weekly/yearly summary reports
- Add data export functionality

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [python-garminconnect](https://github.com/cyberjunky/python-garminconnect) - Excellent library for Garmin Connect API access
- Garmin for providing the Connect platform and API access
- The Python data science community for the amazing visualization libraries

## Disclaimer

This project is not affiliated with Garmin. Use at your own risk and respect Garmin's terms of service.
