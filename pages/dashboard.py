"""
Dashboard page — group fitness overview.

Features:
- Marathon countdown (Geneva, May 10th)
- Cumulative group stats
- Weekly km stats per user (Monday-based weeks)
- Last 5 activities stream
- Calendar month recap
"""

from collections import defaultdict
from datetime import datetime, timedelta

import streamlit as st

from lib.database import get_all_users, get_cached_activities

# --- Config ---
MARATHON_DATE = datetime(2026, 5, 10)

st.title("🏠 Dashboard")
st.markdown("---")

# --- Check if we have data ---
users = get_all_users()
if not users:
    st.info("👋 Welcome! Connect your Garmin account in **Settings** to get started.")
    st.stop()

# --- Marathon Countdown ---
days_to_marathon = (MARATHON_DATE - datetime.now()).days
st.markdown(f"### 🏃‍♂️ Geneva Marathon — {days_to_marathon} days to go!")
st.progress(max(0, min(1, 1 - days_to_marathon / 365)))
st.markdown("---")

# --- Fetch all activities ---
all_activities = get_cached_activities(limit=1000)

if not all_activities:
    st.warning("No activity data yet. Visit **Settings** to sync your Garmin data.")
    st.stop()

# --- Helper functions ---


def get_week_start(date_str: str) -> str:
    """Get Monday of the week for a given date."""
    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    monday = dt - timedelta(days=dt.weekday())
    return monday.strftime("%Y-%m-%d")


def get_month_key(date_str: str) -> str:
    """Get YYYY-MM from date string."""
    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    return dt.strftime("%Y-%m")


def format_duration(seconds: float) -> str:
    """Format duration as HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m {secs}s"


def get_current_monday() -> datetime:
    """Get the Monday of the current week."""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def get_last_n_mondays(n: int) -> list[str]:
    """Get list of last N Monday dates (YYYY-MM-DD)."""
    current_monday = get_current_monday()
    mondays = []
    for i in range(n - 1, -1, -1):
        monday = current_monday - timedelta(weeks=i)
        mondays.append(monday.strftime("%Y-%m-%d"))
    return mondays


# --- Cumulative Group Stats ---
st.markdown("### 🎯 Group Stats (All Time)")

total_distance = sum((a["distance_m"] or 0) for a in all_activities) / 1000
total_activities = len(all_activities)
total_duration = sum((a["duration_s"] or 0) for a in all_activities)
total_calories = sum((a["calories"] or 0) for a in all_activities)

# Extract unique activity types
activity_types = defaultdict(int)
for a in all_activities:
    activity_types[a["activity_type"]] += 1

if activity_types:
    most_common_activity = max(activity_types.items(), key=lambda x: x[1])
    most_common_name = most_common_activity[0].replace("_", " ").title()
    most_common_count = most_common_activity[1]
else:
    most_common_name = "N/A"
    most_common_count = 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("🏃 Total Distance", f"{total_distance:.1f} km")
col2.metric("📊 Total Activities", f"{total_activities}")
col3.metric("⏱️ Total Time", f"{format_duration(total_duration)}")
col4.metric("🔥 Total Calories", f"{total_calories:,}")

st.caption(
    f"💪 Most popular activity: **{most_common_name}** ({most_common_count} times)"
)

st.markdown("---")

# --- Weekly Stats (Current Week) ---
st.markdown("### 📊 This Week (Starting Monday)")

current_week_start = get_current_monday().strftime("%Y-%m-%d")
weekly_data = defaultdict(
    lambda: {"distance": 0, "duration": 0, "activities": 0, "calories": 0}
)

for activity in all_activities:
    week = get_week_start(activity["start_time"])
    if week == current_week_start:
        user = activity["user_name"]
        weekly_data[user]["distance"] += (activity["distance_m"] or 0) / 1000
        weekly_data[user]["duration"] += activity["duration_s"] or 0
        weekly_data[user]["activities"] += 1
        weekly_data[user]["calories"] += activity["calories"] or 0

# Display metric cards
cols = st.columns(len(users))
for idx, user_info in enumerate(users):
    user = user_info["name"]
    display_name = user_info["display_name"] or user.capitalize()
    data = weekly_data[user]

    with cols[idx]:
        st.metric(
            label=f"🏃 {display_name}",
            value=f"{data['distance']:.1f} km",
            delta=f"{data['activities']} activities",
        )
        st.caption(f"⏱️ {format_duration(data['duration'])} | 🔥 {data['calories']} cal")

st.markdown("---")

# --- Last 8 Weeks Trend (Monday-based) ---
st.markdown("### 📈 Weekly Distance (Last 8 Weeks - Monday to Sunday)")

# Get last 8 Monday dates
week_labels = get_last_n_mondays(8)

# Compute weekly data
weeks_data = defaultdict(lambda: defaultdict(float))

for activity in all_activities:
    week = get_week_start(activity["start_time"])
    if week in week_labels:
        user = activity["user_name"]
        weeks_data[week][user] += (activity["distance_m"] or 0) / 1000

# Create simple bar chart visualization
for user_info in users:
    user = user_info["name"]
    display_name = user_info["display_name"] or user.capitalize()

    st.markdown(f"**{display_name}**")

    # Get max value for scaling
    user_values = [weeks_data[week][user] for week in week_labels]
    max_value = max(user_values) if user_values else 1

    for week in week_labels:
        value = weeks_data[week][user]
        if max_value > 0:
            bar_width = value / max_value
        else:
            bar_width = 0

        col1, col2, col3 = st.columns([2, 6, 2])
        with col1:
            st.caption(week)
        with col2:
            st.progress(bar_width)
        with col3:
            st.caption(f"{value:.1f} km")

    st.markdown("")

st.markdown("---")

# --- Monthly Recap (Calendar Months - Year to Date) ---
st.markdown("### 📅 Monthly Recap (Calendar Months - 2026 YTD)")

monthly_data = defaultdict(
    lambda: defaultdict(lambda: {"distance": 0, "activities": 0, "duration": 0})
)

# Get all unique months from activities
all_months = set()
for activity in all_activities:
    month = get_month_key(activity["start_time"])
    if month.startswith("2026"):
        all_months.add(month)
        user = activity["user_name"]
        monthly_data[month][user]["distance"] += (activity["distance_m"] or 0) / 1000
        monthly_data[month][user]["activities"] += 1
        monthly_data[month][user]["duration"] += activity["duration_s"] or 0

# Sort months and get month names
sorted_months = sorted(all_months)
month_names_map = {
    "01": "January",
    "02": "February",
    "03": "March",
    "04": "April",
    "05": "May",
    "06": "June",
    "07": "July",
    "08": "August",
    "09": "September",
    "10": "October",
    "11": "November",
    "12": "December",
}

if sorted_months:
    cols = st.columns(len(sorted_months))

    for idx, month_key in enumerate(sorted_months):
        month_num = month_key.split("-")[1]
        month_name = month_names_map[month_num]

        with cols[idx]:
            st.markdown(f"**{month_name}**")
            for user_info in users:
                user = user_info["name"]
                display_name = user_info["display_name"] or user.capitalize()
                data = monthly_data[month_key][user]

                if data["activities"] > 0:
                    st.markdown(
                        f"**{display_name}:** {data['distance']:.1f} km ({data['activities']} act.)"
                    )
                else:
                    st.markdown(f"**{display_name}:** —")
else:
    st.info("No activity data for 2026 yet.")

st.markdown("---")

# --- Last 5 Activities Stream ---
st.markdown("### 🏃 Recent Activities")

recent_activities = get_cached_activities(limit=5)

for activity in recent_activities:
    user_info = next((u for u in users if u["name"] == activity["user_name"]), None)
    display_name = (
        user_info["display_name"] if user_info else activity["user_name"].capitalize()
    )

    # Parse date
    dt = datetime.fromisoformat(activity["start_time"].replace("Z", "+00:00"))
    date_str = dt.strftime("%b %d, %Y %H:%M")

    # Format activity
    distance_km = (activity["distance_m"] or 0) / 1000
    duration = format_duration(activity["duration_s"] or 0)
    activity_type = activity["activity_type"].replace("_", " ").title()

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{display_name}** — {activity_type}")
        st.caption(f"📅 {date_str}")
    with col2:
        st.metric(label="Distance", value=f"{distance_km:.2f} km", delta=duration)

    st.markdown("---")
