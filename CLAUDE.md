# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Garmin Explorer is a shared fitness dashboard for a Geneva Marathon (May 12, 2026) training group. Built with Streamlit + Python 3.12, using SQLite for caching and the garminconnect library for OAuth-based Garmin API access.

Never coauthor commits.

## Essential Commands

**Package Manager**: Always use `uv` (never `pip`)

```bash
# Development
uv sync                          # Install dependencies
uv run streamlit run app.py      # Run locally (http://localhost:8501)

# Deployment
./deploy.sh                      # Deploy to production server
./deploy.sh --setup              # First-time server provisioning
ssh web-nebluda                  # SSH to production
systemctl status garmin-explorer # Check service status on server
```

**Database Operations**:

```bash
sqlite3 data/garmin.db                    # Open database
sqlite3 data/garmin.db "SELECT ..."       # Run query
cp data/garmin.db data/garmin.db.backup   # Backup before migrations
```

## Architecture

### Three-Tier Structure

1. **Data Layer** (`lib/database.py`)
   - SQLite with 3 tables: `users`, `cached_activities`, `weekly_stats`
   - Auto-migrations on import (see `init_db()` and `migrate_*` functions)
   - Activities stored with full Garmin API response in `activity_json` blob

2. **Business Logic** (`lib/`)
   - `garmin.py`: OAuth wrapper, token persistence in `data/tokens/{user}/`
   - `cache.py`: Sync orchestration (always fetches from Jan 1, 2026 onwards)
   - `fake_data.py`: Test data generator with witty names

3. **Presentation** (`pages/`)
   - Streamlit multi-page navigation (Dashboard, Stream, Settings)
   - Entry point: `app.py` (configures page, runs navigation)

### Activity Data Flow

```
Garmin API → lib/garmin.py → lib/cache.py → lib/database.py → pages/*.py
                ↓                   ↓                ↓
         OAuth tokens       2026 filter      SQLite cache
```

## Critical Implementation Patterns

### Database Migrations

Add migrations as functions in `lib/database.py`:

```python
def migrate_add_new_column() -> None:
    """Add new_column to table_name."""
    with get_db() as db:
        cursor = db.execute("PRAGMA table_info(table_name)")
        columns = {row[1] for row in cursor.fetchall()}
        if "new_column" not in columns:
            db.execute("ALTER TABLE table_name ADD COLUMN new_column TYPE DEFAULT value")
            logger.info("Added new_column to table_name")
            # Backfill logic here if needed

def init_db() -> None:
    # ...
    migrate_add_new_column()  # Call new migration
```

Migrations run automatically on app start via `init_db()` (called at module import).

### Activity Filtering Rules

**Sync Logic** (`lib/cache.py`):

- Always fetches from `TRAINING_START_DATE = "2026-01-01"` to today
- Defensive filter: Only stores activities with `startTimeLocal.startswith("2026")`

**Dashboard Metrics** (`pages/dashboard.py`):

- Define: `RUNNING_TYPES = {"running", "treadmill_running"}`
- Filter for metrics: `running_activities = [a for a in all_activities if a["activity_type"] in RUNNING_TYPES]`
- Keep unfiltered for activity lists (show all types)

### Equivalent Distance Calculation

Formula: `equivalent_distance = distance + (elevation_gain / 100)`

- 100m elevation = 1km distance
- Elevation stored in `cached_activities.elevation_gain_m` (extracted from `activity_json`)
- Helper functions in both `pages/dashboard.py` and `pages/stream.py`:
  ```python
  def calculate_equivalent_distance(distance_m: float, elevation_gain_m: float) -> float:
      return (distance_m / 1000) + (elevation_gain_m / 100)
  ```

### OAuth Token Persistence

Tokens stored per-user in `data/tokens/{user_name}/`:

- garmin_session.json
- oauth1_token.json
- oauth2_token.json

Use `resume(user_name)` to restore session (handles token refresh automatically).

## Deployment Architecture

- **Server**: Ubuntu 24.04 at web-nebluda (fake-sporter.nebluda.com)
- **Reverse Proxy**: Caddy with automatic HTTPS
- **Service**: systemd unit `garmin-explorer.service`
- **User**: Runs as `garmin` (not root)
- **Deployment**: rsync excludes `.git/`, `.venv/`, `data/`, `creds*.json`

The `./deploy.sh` script:

1. Syncs code via rsync
2. Installs dependencies with `uv sync --no-dev`
3. Restarts systemd service
4. Verifies service is active

## Data Directory Structure

```
data/
├── garmin.db              # SQLite database
├── garmin.db.backup       # Manual backups (not tracked)
└── tokens/                # OAuth tokens (gitignored)
    ├── anto/
    ├── arnaud/
    └── jeff_lp/
```

## Streamlit Multi-Page Navigation

- Entry: `app.py` configures page + runs navigation
- Pages auto-discovered from `pages/` directory
- Navigation defined explicitly: `st.navigation([dashboard, stream, settings])`
- Default page: `dashboard.py` (with `default=True`)

## Key Conventions

- **Activity types**: snake_case from Garmin API (e.g., `treadmill_running`, `backcountry_skiing`)
- **Display formatting**: Replace underscores with spaces, title case (e.g., `"Treadmill Running"`)
- **Date handling**: ISO-8601 strings in database, parse with `datetime.fromisoformat()`
- **Null handling**: Use `a.get("field") or 0` pattern for nullable numeric fields
- **Equivalent distance display**: Format as `"8.4km + 38m = 8.8km eq"`

## Adding New Features

### Adding a New Dashboard Metric

1. Extract data from `running_activities` list (already filtered)
2. Calculate metric (sum/count/average)
3. Display with `st.metric()` or custom layout
4. Add to relevant sections: Group Stats, Weekly Stats, 8-Week Trend, or Monthly Recap

### Adding a New Activity Field

1. Update schema in `lib/database.py`:
   - Add column to `_SCHEMA`
   - Create migration function
   - Call migration in `init_db()`
2. Update `upsert_activities()` to extract field from Garmin API response
3. Update display in `pages/dashboard.py` and/or `pages/stream.py`
4. Update `lib/fake_data.py` to generate test data for new field

### Adding a New Page

1. Create `pages/new_page.py` with Streamlit UI
2. Update `app.py` navigation:
   ```python
   new_page = st.Page("pages/new_page.py", title="New Page", icon="🎯")
   pg = st.navigation([dashboard, stream, settings, new_page])
   ```

## Testing with Fake Data

Generate fake users/activities for local testing:

```python
from lib.fake_data import create_fake_user

# Via Settings page "Create Fake User" button, or:
create_fake_user(name="test_user", activity_count=30)
```

Fake data includes:

- Realistic distances based on activity type
- Varied paces/speeds
- Elevation gain (0-150m for running, 0-800m for hiking)
- Spread over last 90 days
