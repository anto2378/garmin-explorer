"""
Activity stream — shows all activities across all connected users.
Useful for debugging and seeing who did what.
"""

from datetime import datetime, timedelta

import streamlit as st

from lib.cache import sync_all_users
from lib.database import get_all_users, get_cached_activities
from lib.garmin import TOKENS_DIR


def format_time_ago(dt: datetime) -> str:
    """Format datetime as 'X hours ago' or 'X days ago'."""
    now = datetime.now()
    # Handle timezone-aware datetimes
    if dt.tzinfo is not None:
        from datetime import timezone
        now = now.replace(tzinfo=timezone.utc)

    delta = now - dt
    seconds = delta.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        mins = int(seconds / 60)
        return f"{mins}m ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}h ago"
    else:
        days = int(seconds / 86400)
        return f"{days}d ago"

st.title("📡 Stream")
st.markdown("---")

# --- Sync controls ---
connected = []
if TOKENS_DIR.exists():
    connected = [
        d.name for d in sorted(TOKENS_DIR.iterdir()) if d.is_dir() and any(d.iterdir())
    ]

if not connected:
    st.warning(
        "No accounts connected yet. Go to **Settings** to connect a Garmin account."
    )
    st.stop()

col1, col2 = st.columns([3, 1])
with col1:
    # Build status with last sync times
    db_users = {u["name"]: u for u in get_all_users()}
    status_parts = []
    for u in connected:
        user_info = db_users.get(u)
        if user_info and user_info.get("last_synced_at"):
            try:
                dt = datetime.fromisoformat(user_info["last_synced_at"])
                time_ago = format_time_ago(dt)
                status_parts.append(f"{u.title()} ({time_ago})")
            except:
                status_parts.append(u.title())
        else:
            status_parts.append(f"{u.title()} (never)")

    st.caption(f"**{len(connected)}** connected: {', '.join(status_parts)}")
with col2:
    if st.button("🔄 Sync now", use_container_width=True):
        with st.spinner("Fetching activities from Garmin..."):
            results = sync_all_users(connected)
        for r in results:
            if "error" in r:
                st.error(f"❌ {r['user'].title()}: {r['error']}")
            else:
                st.success(
                    f"✅ {r['display_name']}: {r['fetched']} fetched, "
                    f"{r['new']} new — {r['cached']} total cached"
                )
        st.rerun()

st.markdown("---")

# --- Activity feed ---
activities = get_cached_activities(limit=200)

if not activities:
    st.info("No cached activities yet. Hit **Sync now** to fetch from Garmin.")
    st.stop()

# --- Quick filters ---
st.subheader(f"Recent activities ({len(activities)})")

filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1, 1, 1, 3])

with filter_col1:
    filter_week = st.button("This week", use_container_width=True)
with filter_col2:
    filter_month = st.button("This month", use_container_width=True)
with filter_col3:
    filter_year = st.button("2026 year", use_container_width=True)

# Apply filters
now = datetime.now()
filtered_activities = activities

if filter_week:
    # Get Monday of current week
    monday = now - timedelta(days=now.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    filtered_activities = [
        a
        for a in activities
        if a.get("start_time")
        and datetime.fromisoformat(a["start_time"].replace("Z", "+00:00")) >= monday
    ]
elif filter_month:
    # Get first day of current month
    first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    filtered_activities = [
        a
        for a in activities
        if a.get("start_time")
        and datetime.fromisoformat(a["start_time"].replace("Z", "+00:00")) >= first_day
    ]
elif filter_year:
    # Get all 2026 activities
    filtered_activities = [
        a
        for a in activities
        if a.get("start_time") and a["start_time"].startswith("2026")
    ]

# Show filter info if active
if filter_week or filter_month or filter_year:
    st.caption(f"Showing {len(filtered_activities)} of {len(activities)} activities")
else:
    st.caption("Showing all activities")

st.markdown("")

# Build a clean table
rows = []
for a in filtered_activities:
    # Parse start time for display
    start = a.get("start_time", "")
    try:
        dt = datetime.fromisoformat(start)
        date_str = dt.strftime("%a %d %b %H:%M")
    except (ValueError, TypeError):
        date_str = start or "—"

    # Distance in km
    dist_m = a.get("distance_m", 0) or 0
    dist_km = dist_m / 1000

    # Duration in minutes
    dur_s = a.get("duration_s", 0) or 0
    dur_min = dur_s / 60

    # Pace (min/km) for running activities
    pace = ""
    if dist_km > 0 and dur_min > 0:
        pace_val = dur_min / dist_km
        pace_mins = int(pace_val)
        pace_secs = int((pace_val - pace_mins) * 60)
        pace = f"{pace_mins}:{pace_secs:02d} /km"

    rows.append(
        {
            "When": date_str,
            "Who": a.get("user_name", "?").title(),
            "Type": (a.get("activity_type") or "unknown").replace("_", " ").title(),
            "Distance": f"{dist_km:.1f} km" if dist_km > 0 else "—",
            "Duration": f"{dur_min:.0f} min" if dur_min > 0 else "—",
            "Pace": pace or "—",
            "Calories": a.get("calories", 0) or "—",
        }
    )

st.dataframe(
    rows,
    use_container_width=True,
    hide_index=True,
    height=600,
)
