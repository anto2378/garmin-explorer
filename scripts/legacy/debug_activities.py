#!/usr/bin/env python3
"""
Debug script to check what activities are available in your Garmin data
"""

import os
from collections import Counter

from garminconnect import Garmin


def debug_activities():
    """Debug function to see what activities are available."""
    print("🔍 DEBUGGING GARMIN ACTIVITIES (Last 60 days)")
    print("=" * 50)

    # Load credentials from .env file
    if not os.path.exists(".env"):
        print("❌ .env file not found. Run setup first.")
        return

    # Simple way to load .env
    env_vars = {}
    with open(".env", "r") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                env_vars[key] = value

    email = env_vars.get("GARMIN_EMAIL")
    password = env_vars.get("GARMIN_PASSWORD")

    if not email or not password:
        print("❌ Credentials not found in .env file.")
        return

    try:
        print("🔐 Authenticating...")
        client = Garmin(email, password)
        client.login()
        print("✅ Authentication successful!")

        print("\n📊 Fetching activities from last 60 days...")
        activities = client.get_activities(
            0, 120
        )  # Get more activities to ensure we have 60 days

        print(f"✅ Found {len(activities)} total activities")

        if not activities:
            print("❌ No activities found at all!")
            return

        # Debug: Check the structure of activities
        print("\n🔍 DEBUGGING ACTIVITY STRUCTURE:")
        print(f"Type of activities: {type(activities)}")
        print(
            f"Length of activities: {len(activities) if hasattr(activities, '__len__') else 'No length'}"
        )

        if activities and len(activities) > 0:
            first_activity = activities[0] if isinstance(activities, list) else None
            if first_activity:
                print(f"Type of first activity: {type(first_activity)}")
                if isinstance(first_activity, dict):
                    print(f"First activity keys: {list(first_activity.keys())}")
                else:
                    print(f"First activity content: {first_activity}")

        # Convert activities to a list if it's not already
        if not isinstance(activities, list):
            print(f"Converting activities from {type(activities)} to list...")
            try:
                activities = list(activities)
            except:
                print("Failed to convert to list")
                return

        # Show first few activities
        print("\n📋 FIRST 5 ACTIVITIES:")
        print("-" * 40)
        for i in range(min(5, len(activities))):
            activity = activities[i]
            if isinstance(activity, dict):
                date = activity.get("startTimeLocal", "Unknown")
                if date != "Unknown" and len(str(date)) >= 10:
                    date = str(date)[:10]
                activity_type = activity.get("activityType", "Unknown")
                name = activity.get("activityName", "Unnamed")
                distance = activity.get("distance", 0)
                if distance and distance > 0:
                    distance_km = float(distance) / 1000
                    print(
                        f"{i + 1}. {date} - {activity_type} - {name} - {distance_km:.2f}km"
                    )
                else:
                    print(f"{i + 1}. {date} - {activity_type} - {name} - No distance")
            else:
                print(
                    f"{i + 1}. Unexpected activity type: {type(activity)} - {activity}"
                )

        # Activity type breakdown - handle potential nested structure
        print("\n🏃‍♂️ ACTIVITY TYPE BREAKDOWN (Last 60 days):")
        print("-" * 40)

        activity_types = []
        for act in activities:
            if isinstance(act, dict):
                activity_types.append(str(act.get("activityType", "Unknown")))
            else:
                activity_types.append("Unknown")

        activity_counts = Counter(activity_types)

        for activity_type, count in activity_counts.most_common():
            print(f"  {activity_type}: {count} activities")

        # Check for any running-related activities specifically
        running_keywords = [
            "running",
            "run",
            "jog",
            "marathon",
            "trail",
            "track",
            "road",
            "treadmill",
        ]
        running_activities = []

        for activity in activities:
            activity_type = activity.get("activityType", "").lower()
            if any(keyword in activity_type for keyword in running_keywords):
                running_activities.append(activity)

        print(f"\n🏃 RUNNING-RELATED ACTIVITIES FOUND: {len(running_activities)}")
        if running_activities:
            for activity in running_activities:
                date = activity.get("startTimeLocal", "Unknown")[:10]
                activity_type = activity.get("activityType", "Unknown")
                distance = activity.get("distance", 0)
                if distance > 0:
                    distance_km = distance / 1000
                    print(f"  {date} - {activity_type} - {distance_km:.2f} km")
                else:
                    print(f"  {date} - {activity_type}")
        else:
            print("No activities found in the last 60 days.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_activities()
