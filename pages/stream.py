"""
Activity stream — shows all activities across all connected users.
Useful for debugging and seeing who did what.
"""

from datetime import datetime

import streamlit as st

from lib.cache import sync_all_users
from lib.database import get_cached_activities
from lib.garmin import TOKENS_DIR

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
    st.caption(
        f"**{len(connected)}** connected account(s): {', '.join(u.title() for u in connected)}"
    )
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

st.subheader(f"Recent activities ({len(activities)})")

# Build a clean table
rows = []
for a in activities:
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
)
