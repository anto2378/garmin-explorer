# GitHub Copilot Instructions — Garmin Explorer

## Project Overview

Shared Garmin Connect fitness dashboard for a small group of friends.
Built with **Streamlit**, data fetched via **garminconnect** library.
Package management: **UV** (never use pip).
Live at: **https://fake-sporter.nebluda.com/**

## Tech Stack

- **UI:** Streamlit (st.navigation API, wide layout)
- **Data:** garminconnect (OAuth via Garth, tokens valid ~1 year)
- **Charts:** Plotly (planned for Phase 4)
- **Persistence:** SQLite at `data/garmin.db`
- **Deployment:** Ubuntu VPS (web-nebluda), Caddy reverse proxy, systemd service
- **Domain:** Cloudflare → https://fake-sporter.nebluda.com/

## Project Structure

```
garmin-explorer/
├── pyproject.toml
├── app.py                  # Streamlit entry point + router
├── lib/
│   ├── garmin.py           # Garmin API wrapper + token management
│   ├── database.py         # SQLite persistence (users, activities, weekly_stats)
│   └── cache.py            # Fetch + cache logic (90d backfill, 7d incremental)
├── pages/
│   ├── dashboard.py        # Main dashboard (placeholder)
│   ├── stream.py           # Activity feed across all users
│   └── settings.py         # Garmin auth + account management
├── .streamlit/
│   └── config.toml         # Dark theme, red primary color
├── server/
│   ├── setup.sh            # Server provisioning (idempotent)
│   ├── Caddyfile           # Reverse proxy config
│   └── garmin-explorer.service  # systemd unit
├── deploy.sh               # One-command deploy (rsync + restart)
└── data/                   # SQLite DB + token dirs (gitignored)
    ├── garmin.db
    └── tokens/{user}/
```

## Key Patterns

- Use `uv run streamlit run app.py` to start locally
- Use `uv add <pkg>` to add dependencies (never pip)
- Deploy: `./deploy.sh` (rsync to server + restart service)
- Garmin tokens: stored per-user in `data/tokens/{user_name}/`
- SQLite tables:
  - `users (name, garmin_email, display_name, created_at)`
  - `cached_activities (user_name, garmin_id, activity_type, distance_m, duration_s, ...)`
  - `weekly_stats (user_name, week_start, total_distance_m, ...)`
- First connect: backfills 90 days of activities
- Manual sync: fetches last 7 days
- Full width layout with custom CSS in app.py

## Settings Page Features

- Shows connected accounts with Garmin email below name
- Red "Remove" button for each account
- Duplicate email prevention (shows orange warning)
- User-friendly error messages with debug details in expander
- On connect: authenticates → syncs 90 days → stores in DB
