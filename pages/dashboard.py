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

import plotly.graph_objects as go
import streamlit as st

from lib.database import get_all_users, get_cached_activities


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


# --- Config ---
MARATHON_DATE = datetime(2026, 5, 12)
TRAINING_START_DATE = datetime(2025, 11, 13)  # 180 days before race
RUNNING_TYPES = {"running", "treadmill_running"}

st.title("🏠 Dashboard")

# --- Check if we have data ---
users = get_all_users()
if not users:
    st.info("👋 Welcome! Connect your Garmin account in **Settings** to get started.")
    st.stop()

# --- Layout: Countdown in left, stats in right ---
left_col, main_col = st.columns([1, 2])

with left_col:
    # Marathon Countdown
    days_to_marathon = (MARATHON_DATE - datetime.now()).days
    marathon_date_str = MARATHON_DATE.strftime("%B %d, %Y")

    st.markdown(
        f"""
    <div style="text-align: center; padding: 1.5rem 0;">
        <h3 style="margin-bottom: 0.5rem;">🏃‍♂️ Geneva Marathon</h3>
        <h1 style="font-size: 4rem; margin: 0; color: #ff4b4b;">{days_to_marathon}</h1>
        <h4 style="margin-top: 0.5rem;">days to go</h4>
        <p style="color: #888; font-size: 1rem;">{marathon_date_str}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Training progress
    total_training_days = (MARATHON_DATE - TRAINING_START_DATE).days
    days_trained = (datetime.now() - TRAINING_START_DATE).days
    training_progress = max(0, min(1, days_trained / total_training_days))

    st.caption("Training Progress")
    st.progress(training_progress)
    st.caption(f"Day {days_trained} of {total_training_days}")

    # Last Sync Status
    st.markdown("---")
    st.caption("**Last Sync**")

    for user_info in users:
        display_name = user_info["display_name"] or user_info["name"].capitalize()
        last_synced = user_info.get("last_synced_at")

        if last_synced:
            try:
                dt = datetime.fromisoformat(last_synced)
                time_ago = format_time_ago(dt)
                st.caption(f"🟢 {display_name}: {time_ago}")
            except (ValueError, TypeError):
                st.caption(f"🟡 {display_name}: Never")
        else:
            st.caption(f"🟡 {display_name}: Never")

with main_col:
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


def calculate_effort_distance(distance_m: float, elevation_gain_m: float) -> float:
    """Calculate effort distance: distance + (elevation / 100)."""
    return (distance_m / 1000) + (elevation_gain_m / 100)


def format_elevation(elevation_m: float) -> str:
    """Format elevation as meters with unit."""
    return f"{int(elevation_m)}m" if elevation_m > 0 else "—"


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


with main_col:
    # --- Cumulative Group Stats ---
    st.markdown("### 🎯 Group Stats (All Time)")

    # Custom CSS to make metric values larger
    st.markdown(
        """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 2rem;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1.1rem;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Filter for running activities only
    running_activities = [a for a in all_activities if a["activity_type"] in RUNNING_TYPES]

    total_distance = sum((a["distance_m"] or 0) for a in running_activities) / 1000
    total_activities = len(running_activities)
    total_duration = sum((a["duration_s"] or 0) for a in running_activities)
    total_calories = sum((a["calories"] or 0) for a in running_activities)

    # Extract unique activity types from running activities
    activity_types = defaultdict(int)
    for a in running_activities:
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
        f"🏃 Running activities only • Most popular: **{most_common_name}** ({most_common_count} times)"
    )

    st.markdown("")
    st.markdown("---")

    # --- Per-Person Cumulative Target ---
    st.markdown("### 🎯 Training KM Target")

    TARGET_KM = 700
    user_progress = {}

    for user_info in users:
        user = user_info["name"]
        user_activities = [a for a in running_activities if a["user_name"] == user]

        # Calculate both regular distance and effort distance
        total_distance_km = sum((a.get("distance_m") or 0) / 1000 for a in user_activities)
        total_effort_km = sum(
            calculate_effort_distance(
                a.get("distance_m") or 0,
                a.get("elevation_gain_m") or 0
            )
            for a in user_activities
        )
        total_steps = sum((a.get("steps") or 0) for a in user_activities)

        user_progress[user] = {
            "display_name": user_info["display_name"] or user.capitalize(),
            "distance_km": total_distance_km,
            "effort_km": total_effort_km,
            "steps": total_steps,
        }

    # Display per-user stats without progress bars
    for user, data in sorted(user_progress.items()):
        remaining = max(0, TARGET_KM - data["effort_km"])
        st.markdown(
            f"**{data['display_name']}**: {data['distance_km']:.0f} / 700 km "
            f"({data['effort_km']:.0f} km_effort) — {remaining:.0f} km remaining | "
            f"👣 {data['steps']:,} steps"
        )

    st.markdown("")

    # Group summary with progress bar
    total_group_distance = sum(d["distance_km"] for d in user_progress.values())
    total_group_effort = sum(d["effort_km"] for d in user_progress.values())
    total_group_steps = sum(d["steps"] for d in user_progress.values())
    group_target = TARGET_KM * len(users)
    group_remaining = max(0, group_target - total_group_effort)

    progress_val = min(1.0, total_group_effort / group_target)
    st.progress(progress_val)

    st.caption(
        f"💪 **Group Total**: {total_group_distance:.0f} km "
        f"({total_group_effort:.0f} km_effort) of {group_target:.0f} km target — "
        f"{group_remaining:.0f} km remaining | 👣 {total_group_steps:,} steps"
    )

st.markdown("---")

# --- Cumulative Distance Over Time ---
st.markdown("### 📈 Cumulative Running Distance")

# Build per-user cumulative series from running activities
user_colors = ["#ff4b4b", "#4b9eff", "#4bff91", "#ffcc4b", "#cc4bff"]
cumulative_fig = go.Figure()

sorted_users = sorted(users, key=lambda u: u["name"])

for idx, user_info in enumerate(sorted_users):
    user = user_info["name"]
    display_name = user_info["display_name"] or user.capitalize()
    color = user_colors[idx % len(user_colors)]

    user_running = [
        a for a in running_activities
        if a["user_name"] == user and a.get("start_time")
    ]
    # Sort ascending by date
    user_running.sort(key=lambda a: a["start_time"])

    if not user_running:
        continue

    dates = []
    cumulative_km = []
    running_total = 0.0
    for a in user_running:
        running_total += (a.get("distance_m") or 0) / 1000
        dates.append(a["start_time"][:10])  # YYYY-MM-DD
        cumulative_km.append(running_total)

    cumulative_fig.add_trace(
        go.Scatter(
            x=dates,
            y=cumulative_km,
            mode="lines+markers",
            name=display_name,
            line=dict(color=color, width=2),
            marker=dict(size=4),
            hovertemplate="%{x}<br><b>%{y:.1f} km</b><extra>" + display_name + "</extra>",
        )
    )

cumulative_fig.update_layout(
    template="plotly_dark",
    height=380,
    margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    xaxis_title=None,
    yaxis_title="Cumulative km",
    hovermode="x unified",
)
st.plotly_chart(cumulative_fig, use_container_width=True)

st.markdown("---")

# --- Weekly Stats (Current Week) ---
st.markdown("### 📊 This Week (Starting Monday)")

current_week_start = get_current_monday().strftime("%Y-%m-%d")
weekly_data = defaultdict(
    lambda: {"distance": 0, "effort_distance": 0, "duration": 0, "activities": 0, "active_calories": 0}
)

for activity in all_activities:
    if activity["activity_type"] not in RUNNING_TYPES:
        continue
    week = get_week_start(activity["start_time"])
    if week == current_week_start:
        user = activity["user_name"]
        distance_km = (activity["distance_m"] or 0) / 1000
        effort_km = calculate_effort_distance(
            activity.get("distance_m") or 0,
            activity.get("elevation_gain_m") or 0
        )
        weekly_data[user]["distance"] += distance_km
        weekly_data[user]["effort_distance"] += effort_km
        weekly_data[user]["duration"] += activity["duration_s"] or 0
        weekly_data[user]["activities"] += 1
        weekly_data[user]["active_calories"] += activity.get("active_calories") or 0

# Display metric cards
cols = st.columns(len(users))
for idx, user_info in enumerate(users):
    user = user_info["name"]
    display_name = user_info["display_name"] or user.capitalize()
    data = weekly_data[user]

    with cols[idx]:
        st.metric(
            label=f"🏃 {display_name}",
            value=f"{data['distance']:.1f} km ({data['effort_distance']:.1f} km_effort)",
            delta=f"{data['activities']} activities",
        )
        st.caption(f"⏱️ {format_duration(data['duration'])} | 🔥 {data['active_calories']} cal")

st.markdown("---")

# --- Last 8 Weeks Trend (Monday-based) ---
st.markdown("### 📈 Weekly Distance (Last 8 Weeks - Monday to Sunday)")

# Get last 8 Monday dates
week_labels = get_last_n_mondays(8)

# Compute weekly data
weeks_data = defaultdict(lambda: defaultdict(float))

for activity in all_activities:
    if activity["activity_type"] not in RUNNING_TYPES:
        continue
    week = get_week_start(activity["start_time"])
    if week in week_labels:
        user = activity["user_name"]
        weeks_data[week][user] += (activity["distance_m"] or 0) / 1000

# Create DataFrame for st.bar_chart (wide format)
import pandas as pd

chart_data = {}

# Convert week dates to week numbers (ISO 8601 format: YYYY-Wxx)
week_numbers = []
for week_date in week_labels:
    dt = datetime.strptime(week_date, "%Y-%m-%d")
    iso_year, iso_week, _ = dt.isocalendar()
    week_numbers.append(f"{iso_year}-W{iso_week:02d}")

chart_data["Week"] = week_numbers

# Add each user as a column
colors = ["#FF4B4B", "#0068C9", "#83C9FF", "#FF9B00", "#29B09D", "#7D3AC1", "#DB4CB2"]
user_colors = []

for idx, user_info in enumerate(users):
    user = user_info["name"]
    display_name = user_info["display_name"] or user.capitalize()
    chart_data[display_name] = [weeks_data[week][user] for week in week_labels]
    user_colors.append(colors[idx % len(colors)])

df = pd.DataFrame(chart_data)

# Create grouped bar chart with Altair for better y-axis control
import altair as alt

# Prepare data in long format for Altair
chart_rows = []
for week_idx, week in enumerate(week_labels):
    for user_info in users:
        user = user_info["name"]
        display_name = user_info["display_name"] or user.capitalize()
        chart_rows.append(
            {
                "Week": week_numbers[week_idx],
                "Runner": display_name,
                "Distance (km)": weeks_data[week][user],
            }
        )

chart_df = pd.DataFrame(chart_rows)

# Create Altair chart with y-axis starting at 0
chart = (
    alt.Chart(chart_df)
    .mark_bar()
    .encode(
        x=alt.X("Week:N", title="Week"),
        y=alt.Y(
            "Distance (km):Q",
            scale=alt.Scale(domain=[0, chart_df["Distance (km)"].max() * 1.1]),
        ),
        color=alt.Color("Runner:N", scale=alt.Scale(range=colors[: len(users)])),
        xOffset="Runner:N",
    )
    .properties(height=400)
)

st.altair_chart(chart, use_container_width=True)

st.markdown("---")

# --- Monthly Recap (Calendar Months - Jan to May 2026) ---
st.markdown("### 📅 Monthly Recap (Jan - May 2026)")

monthly_data = defaultdict(
    lambda: defaultdict(lambda: {"distance": 0, "effort_distance": 0, "activities": 0, "duration": 0})
)

# Compute monthly data
for activity in all_activities:
    if activity["activity_type"] not in RUNNING_TYPES:
        continue
    month = get_month_key(activity["start_time"])
    if month.startswith("2026"):
        user = activity["user_name"]
        distance_km = (activity["distance_m"] or 0) / 1000
        effort_km = calculate_effort_distance(
            activity.get("distance_m") or 0,
            activity.get("elevation_gain_m") or 0
        )
        monthly_data[month][user]["distance"] += distance_km
        monthly_data[month][user]["effort_distance"] += effort_km
        monthly_data[month][user]["activities"] += 1
        monthly_data[month][user]["duration"] += activity["duration_s"] or 0

# Fixed months: Jan-May
months_to_show = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05"]
month_names = ["January", "February", "March", "April", "May"]

import pandas as pd

# Build single consolidated table
table_data = []
for user_info in users:
    user = user_info["name"]
    display_name = user_info["display_name"] or user.capitalize()

    row = {"Runner": display_name}

    # Add km (with effort) and activity count for each month
    for month_key, month_name in zip(months_to_show, month_names):
        data = monthly_data[month_key][user]
        if data["activities"] > 0:
            row[f"{month_name} km"] = f"{data['distance']:.1f} ({data['effort_distance']:.1f} effort)"
            row[f"{month_name} #"] = data["activities"]
        else:
            row[f"{month_name} km"] = "—"
            row[f"{month_name} #"] = "—"

    table_data.append(row)

if table_data:
    df = pd.DataFrame(table_data)
    st.dataframe(df, hide_index=True, use_container_width=True)

st.markdown("---")

# --- Recent Activities Stream (Table Format) ---
st.markdown("### 🏃 Recent Activities")

recent_activities = get_cached_activities(limit=20)

# Build table data
activity_rows = []
for activity in recent_activities:
    user_info = next((u for u in users if u["name"] == activity["user_name"]), None)
    display_name = (
        user_info["display_name"]
        if user_info
        else activity["user_name"].capitalize()
    )

    # Parse date
    dt = datetime.fromisoformat(activity["start_time"].replace("Z", "+00:00"))
    date_str = dt.strftime("%b %d, %H:%M")

    # Calculate metrics
    distance_km = (activity["distance_m"] or 0) / 1000
    elevation_gain = activity.get("elevation_gain_m") or 0
    effort_km = distance_km + (elevation_gain / 100)
    duration = format_duration(activity["duration_s"] or 0)
    activity_type = activity["activity_type"].replace("_", " ").title()

    activity_rows.append({
        "Date": date_str,
        "Who": display_name,
        "Type": activity_type,
        "Distance": f"{distance_km:.1f} km",
        "Elevation": format_elevation(elevation_gain),
        "Effort Dist": f"{effort_km:.1f} km",
        "Duration": duration,
    })

if activity_rows:
    df = pd.DataFrame(activity_rows)
    st.dataframe(df, hide_index=True, use_container_width=True, height=500)
