"""
Generate fake users and activities for testing.
"""

import random
from datetime import datetime, timedelta

from lib.database import upsert_activities, upsert_user

# Witty fake names
FAKE_NAMES = [
    "speedy_gonzales",
    "forest_gump",
    "flash_gordon",
    "usain_bolt_wannabe",
    "couch_potato_no_more",
    "marathon_maniac",
    "slowpoke_rodriguez",
    "running_man",
    "gazelle_legs",
    "chariots_of_fire",
    "road_runner",
    "sonic_the_jogger",
    "pavement_pounder",
    "asphalt_assassin",
    "trail_blazer_99",
]

# Activity types distribution (weighted)
ACTIVITY_TYPES = [
    ("running", 0.6),
    ("cycling", 0.2),
    ("walking", 0.1),
    ("swimming", 0.05),
    ("hiking", 0.05),
]


def generate_fake_email(name: str) -> str:
    """Generate a fake Garmin email."""
    return f"{name}@fake-runner.test"


def generate_fake_display_name(name: str) -> str:
    """Generate a display name from username."""
    return name.replace("_", " ").title()


def generate_fake_activity(
    activity_id: int, days_ago: int, activity_type: str = "running"
) -> dict:
    """Generate a single fake activity."""
    # Random time of day (prefer morning/evening)
    hour = random.choice([6, 7, 8, 17, 18, 19, 12])
    minute = random.randint(0, 59)

    start_time = datetime.now() - timedelta(
        days=days_ago, hours=24 - hour, minutes=60 - minute
    )

    # Generate realistic distances based on activity type
    if activity_type == "running":
        distance_km = random.uniform(3.0, 21.0)  # 3-21km
        pace_min_per_km = random.uniform(4.5, 6.5)  # 4:30-6:30 min/km
    elif activity_type == "cycling":
        distance_km = random.uniform(15.0, 80.0)  # 15-80km
        pace_min_per_km = random.uniform(1.5, 2.5)  # faster pace
    elif activity_type == "walking":
        distance_km = random.uniform(2.0, 10.0)
        pace_min_per_km = random.uniform(10.0, 15.0)
    elif activity_type == "swimming":
        distance_km = random.uniform(0.5, 3.0)
        pace_min_per_km = random.uniform(25.0, 35.0)
    else:  # hiking
        distance_km = random.uniform(5.0, 20.0)
        pace_min_per_km = random.uniform(8.0, 12.0)

    distance_m = distance_km * 1000
    duration_s = distance_km * pace_min_per_km * 60
    calories = int(distance_km * random.uniform(60, 80))  # ~60-80 cal/km

    # Generate realistic elevation gain based on activity type
    if activity_type == "running":
        elevation_gain = random.uniform(0, 150)  # 0-150m for runs
    elif activity_type == "cycling":
        elevation_gain = random.uniform(50, 500)  # More elevation for cycling
    elif activity_type == "hiking":
        elevation_gain = random.uniform(100, 800)  # Significant for hiking
    elif activity_type == "walking":
        elevation_gain = random.uniform(0, 100)
    else:  # swimming
        elevation_gain = 0  # No elevation in pool

    return {
        "activityId": activity_id,
        "activityType": {"typeKey": activity_type},
        "distance": distance_m,
        "duration": duration_s,
        "calories": calories,
        "elevationGain": elevation_gain,
        "startTimeLocal": start_time.isoformat(),
        "startTimeGMT": start_time.isoformat(),
    }


def create_fake_user(name: str | None = None, activity_count: int = 30) -> dict:
    """
    Create a fake user with realistic activities.

    Args:
        name: Username (will pick random if None)
        activity_count: Number of activities to generate (default 30)

    Returns:
        dict with user info and activities created
    """
    if name is None:
        # Pick random unused name
        name = random.choice(FAKE_NAMES)

    email = generate_fake_email(name)
    display_name = generate_fake_display_name(name)

    # Register user
    upsert_user(name, garmin_email=email, display_name=display_name)

    # Generate activities spread over last 90 days
    activities = []
    for i in range(activity_count):
        # Pick activity type based on weighted distribution
        activity_type = random.choices(
            [t[0] for t in ACTIVITY_TYPES],
            weights=[t[1] for t in ACTIVITY_TYPES],
        )[0]

        # Spread activities over 90 days, with some clustering
        days_ago = random.randint(0, 90)

        activity = generate_fake_activity(
            activity_id=100000 + random.randint(1000, 99999),
            days_ago=days_ago,
            activity_type=activity_type,
        )
        activities.append(activity)

    # Insert activities into database
    new_count = upsert_activities(name, activities)

    return {
        "name": name,
        "email": email,
        "display_name": display_name,
        "activities_created": new_count,
        "total_activities": activity_count,
    }


def get_available_fake_names() -> list[str]:
    """Get list of fake names that aren't already used."""
    from lib.database import get_all_users

    existing_users = {u["name"] for u in get_all_users()}
    return [name for name in FAKE_NAMES if name not in existing_users]
