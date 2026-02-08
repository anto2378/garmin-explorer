# Garmin Explorer — Implementation Plan

**Last updated:** 2026-02-08 (v4 — Phase 4 done: comprehensive dashboard with marathon countdown)
**Domain:** https://fake-sporter.nebluda.com/
**Server:** 89.167.10.158 (Ubuntu 24.04, `ssh web-nebluda`)
**Stack:** Streamlit + garminconnect + SQLite + Plotly
**Package manager:** UV (never pip)

---

## Architecture

```
┌──────────────┐     ┌────────────────┐     ┌──────────────────┐
│  Cloudflare  │────▶│  Ubuntu VPS    │────▶│  Streamlit app   │
│  HTTPS proxy │     │  Caddy reverse │     │  :8501            │
│              │     │  proxy :80/443 │     │                  │
└──────────────┘     └────────────────┘     └──────────────────┘
                                                    │
                                            ┌───────┴────────┐
                                            │  data/          │
                                            │  ├── garmin.db  │  SQLite
                                            │  └── tokens/    │  Garth OAuth
                                            └────────────────┘
```

**Cloudflare** handles HTTPS termination + caching.
**Caddy** listens on :80, auto-redirects, reverse proxies to Streamlit.
**Streamlit** runs as a systemd service on :8501 (localhost only).

---

## Deployment

One-command deploy from local machine:

```bash
./deploy.sh
```

This does: rsync project → server, restart systemd service.

---

## Phases

### Phase 1: Garmin Auth ✅ _(done)_

**Goal:** Confirm we can login, store tokens, and fetch activities.

Files:

- `lib/__init__.py`
- `lib/garmin.py` — wrapper around garminconnect: login, token persist, fetch activities
- `test_auth.py` — quick script to validate auth works

---

### Phase 2: Server + Deploy + Minimal App ✅ _(done)_

**Goal:** Get a live website at https://fake-sporter.nebluda.com/ where friends
can connect their Garmin account. Deploy in one command.

Server provisioning (`server/setup.sh` — idempotent, re-runnable):

- Install uv, Caddy
- Create `garmin` system user
- Install systemd service
- Caddy reverse proxy :80 → Streamlit :8501

Minimal Streamlit app:

- `app.py` — entry point, navigation (dashboard, stream, settings), wide layout
- `pages/dashboard.py` — "coming soon" placeholder
- `pages/stream.py` — live activity feed across all users
- `pages/settings.py` — Garmin login form + connected users list with:
  - Email display below each user name
  - Red "Remove" button for each account
  - Duplicate email prevention (orange warning)
  - User-friendly error messages with debug details in expander
- `.streamlit/config.toml` — theme config (dark, red primary)

Deploy:

- `deploy.sh` — rsync code to server, restart service
- `server/garmin-explorer.service` — systemd unit
- `server/Caddyfile` — reverse proxy config

Test:

```bash
# Local
uv run streamlit run app.py  # → login works at localhost:8501

# Deploy
./deploy.sh                  # → rsync + restart
curl https://fake-sporter.nebluda.com/  # → Streamlit loads
# → Connect Garmin on live site → tokens stored on server
```

---

### Phase 3: Persistence + Caching ✅ _(done)_

**Goal:** SQLite for user registry + cached activity data. Activity stream page.

Files:

- `lib/database.py` — SQLite setup, user + activity + weekly_stats tables
  - Added `garmin_email` field (UNIQUE) to prevent duplicate accounts
  - Functions: `upsert_user()`, `get_user_by_email()`, `delete_user()`
- `lib/cache.py` — fetch-and-cache logic: backfill 90 days on first sync, 7 days after
- `pages/stream.py` — activity feed: shows all activities across all users (with sync button)

Tables:

- `users (id, name, garmin_email, display_name, created_at)` — now includes garmin_email
- `cached_activities (id, user_name, garmin_id, activity_type, distance_m, duration_s, calories, start_time, activity_json, fetched_at)`
- `weekly_stats (id, user_name, week_start, total_distance_m, total_duration_s, total_activities, total_calories, computed_at)`

Strategy:

- On first connect → backfill last 90 days + register user in SQLite
- After that → manual sync via "Sync now" button on stream page (fetches last 7 days)
- Weekly stats computed from cached activities (not yet used in UI)

Test:

```bash
# Connect a user via Settings page → auto-backfills 90 days
# Visit Stream page → see all activities across users
# Hit "Sync now" → fetches last 7 days for all connected users
```

---

### Phase 4: Dashboard ✅ _(done)_

**Goal:** Visualize group fitness data.

Files:

- `pages/dashboard.py` — full implementation with comprehensive stats

Dashboard components:

- **Marathon countdown** — days until Geneva Marathon (May 10, 2026)
- **This Week cards** — metric cards per person (km, activities, duration, calories)
- **8-week trend** — Plotly grouped bar chart: weekly km per person
- **Monthly recap** — Jan/Feb/Mar 2026 summary per person
- **Recent activities** — last 5 activities stream with details

Features:

- Auto-expandable for new users (all charts update dynamically)
- Dark theme with Plotly integration
- Progress bar for marathon countdown
- Formatted durations and distances

Test:

```bash
uv run streamlit run app.py
# → Dashboard loads with real data, all charts responsive
```

---

### Phase 5: Polish & Extras

- Auto-refresh data on a schedule
- Weekly challenges / streaks
- Token expiry warnings
- Mobile-friendly layout tweaks

---

## Questions Resolved

- **Token storage:** On-disk via Garth (garminconnect's default), per-user dirs
- **Caching:** SQLite for stats, Streamlit's `@st.cache_data` for in-memory
- **Deploy:** rsync + systemd (no Docker needed, simple VPS)
- **HTTPS:** Cloudflare handles SSL termination
- **Domain:** fake-sporter.nebluda.com → Cloudflare → 89.167.10.158:80 → Caddy → :8501
