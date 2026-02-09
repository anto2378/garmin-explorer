"""
Fetch-and-cache layer.

Handles syncing activities from Garmin API → SQLite cache.
- First sync: backfill 90 days
- Subsequent syncs: last 7 days (incremental)
- Weekly stats: computed from cached activities
"""

import logging
from datetime import datetime, timedelta

from lib.database import (
    get_activity_count,
    get_cached_activities,
    upsert_activities,
    upsert_user,
    upsert_weekly_stats,
)
from lib.garmin import get_activities, get_display_name, resume

logger = logging.getLogger(__name__)

TRAINING_START_DATE = "2026-01-01"


def sync_user(user_name: str, garmin_email: str | None = None) -> dict:
    """
    Sync a user's activities from Garmin API → local cache.
    Always fetches from Jan 1, 2026 to today.
    """
    client = resume(user_name)
    display_name = get_display_name(client)

    # Fetch all activities from training start
    activities = get_activities(client, start_date=TRAINING_START_DATE)

    # Filter out pre-2026 activities (defense in depth)
    activities_2026 = []
    for a in activities:
        start_time = a.get("startTimeLocal") or a.get("startTimeGMT") or ""
        if start_time.startswith("2026"):
            activities_2026.append(a)

    new_count = upsert_activities(user_name, activities_2026)

    # Update last sync timestamp
    upsert_user(
        user_name,
        garmin_email,
        display_name,
        last_synced_at=datetime.now().isoformat()
    )

    result = {
        "user": user_name,
        "display_name": display_name,
        "fetched": len(activities_2026),
        "cached": get_activity_count(user_name),
        "new": new_count,
    }
    logger.info(
        "Synced %s: fetched=%d, new=%d, total_cached=%d",
        user_name,
        len(activities_2026),
        new_count,
        result["cached"],
    )
    return result


def sync_all_users(user_names: list[str]) -> list[dict]:
    """Sync activities for all given users. Returns list of sync results."""
    results = []
    for name in user_names:
        try:
            result = sync_user(name)
            results.append(result)
        except Exception as e:
            logger.error("Failed to sync %s: %s", name, e)
            results.append({"user": name, "error": str(e)})
    return results


def compute_weekly_stats(user_name: str) -> None:
    """
    Compute and store weekly stats from cached activities.
    Groups activities by ISO week (Monday start).
    """
    activities = get_cached_activities(user_name, limit=10_000)

    # Group by week
    weeks: dict[str, dict] = {}
    for a in activities:
        start_time = a.get("start_time")
        if not start_time:
            continue
        try:
            dt = datetime.fromisoformat(start_time)
        except (ValueError, TypeError):
            continue

        # Monday of that week
        monday = dt.date() - timedelta(days=dt.weekday())
        week_key = monday.isoformat()

        if week_key not in weeks:
            weeks[week_key] = {
                "distance_m": 0.0,
                "duration_s": 0.0,
                "activities": 0,
                "calories": 0,
            }
        w = weeks[week_key]
        w["distance_m"] += a.get("distance_m", 0) or 0
        w["duration_s"] += a.get("duration_s", 0) or 0
        w["activities"] += 1
        w["calories"] += a.get("calories", 0) or 0

    # Store each week
    for week_start, stats in weeks.items():
        upsert_weekly_stats(
            user_name=user_name,
            week_start=week_start,
            total_distance_m=stats["distance_m"],
            total_duration_s=stats["duration_s"],
            total_activities=stats["activities"],
            total_calories=stats["calories"],
        )

    logger.info("Computed weekly stats for %s: %d weeks", user_name, len(weeks))
