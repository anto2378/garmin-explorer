"""
Quick test: authenticate with Garmin and fetch recent activities.

Usage:
    uv run python test_auth.py
"""

import json
import sys
from pathlib import Path

from lib.garmin import get_activities, get_client, get_display_name

CREDS_FILE = Path("creds_anto.json")


def main():
    if not CREDS_FILE.exists():
        print(f"❌ {CREDS_FILE} not found")
        sys.exit(1)

    creds = json.loads(CREDS_FILE.read_text())
    email = creds.get("email")
    password = creds.get("password")

    print(f"🔐 Authenticating as {email}...")
    client = get_client("anto", email, password)

    # Profile
    display_name = get_display_name(client)
    print(f"✅ Logged in as: {display_name}")

    # Activities
    activities = get_activities(client, days=14)
    print(f"📊 Found {len(activities)} activities in last 14 days:\n")

    for act in activities[:10]:
        name = act.get("activityName", "?")
        act_type = act.get("activityType", {}).get("typeKey", "?")
        distance_km = round((act.get("distance", 0) or 0) / 1000, 2)
        duration_min = round((act.get("duration", 0) or 0) / 60, 1)
        start = act.get("startTimeLocal", "?")
        print(
            f"  • {start}  {act_type:<20} {distance_km:>7} km  {duration_min:>6} min  {name}"
        )

    if len(activities) > 10:
        print(f"  ... and {len(activities) - 10} more")

    # Confirm token persistence
    print("\n💾 Tokens saved to data/tokens/anto/")
    print("   Run again — it should work without credentials.")


if __name__ == "__main__":
    main()
