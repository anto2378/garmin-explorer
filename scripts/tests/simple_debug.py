#!/usr/bin/env python3
"""
Simple debug script to check what activities are available in your Garmin data
"""

import os

from garminconnect import Garmin


def simple_debug():
    """Simple debug function to see what activities are available."""
    print("🔍 SIMPLE GARMIN ACTIVITIES DEBUG")
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

        print("\n📊 Fetching activities...")
        activities = client.get_activities(0, 60)  # Get last 60 activities

        print(f"✅ Raw activities type: {type(activities)}")
        print(
            f"✅ Activities length: {len(activities) if hasattr(activities, '__len__') else 'Unknown'}"
        )

        if not activities:
            print("❌ No activities found!")
            return

        # Try to safely iterate through activities
        print("\n📋 EXAMINING ACTIVITIES:")
        print("-" * 40)

        activity_count = 0
        activity_types_found = set()

        try:
            # Try to iterate through activities however they're structured
            for i, activity in enumerate(activities):
                if i >= 10:  # Only show first 10
                    break

                activity_count += 1
                print(f"\nActivity {i + 1}:")
                print(f"  Type: {type(activity)}")

                # Try to extract information if it's a dict
                if isinstance(activity, dict):
                    # Print all keys to see what's available
                    print(f"  Keys: {list(activity.keys())}")

                    # Try to get common fields
                    activity_type = activity.get("activityType", "Unknown")
                    activity_types_found.add(str(activity_type))

                    date = activity.get("startTimeLocal", "Unknown")
                    name = activity.get("activityName", "Unnamed")
                    distance = activity.get("distance", 0)

                    print(f"  Activity Type: {activity_type}")
                    print(f"  Date: {str(date)[:19] if date != 'Unknown' else date}")
                    print(f"  Name: {name}")
                    if distance and isinstance(distance, (int, float)) and distance > 0:
                        print(f"  Distance: {distance / 1000:.2f} km")
                    else:
                        print("  Distance: Not available or 0")
                else:
                    print(f"  Content: {str(activity)[:100]}...")

        except Exception as e:
            print(f"Error iterating through activities: {e}")

        print(f"\n✅ Successfully processed {activity_count} activities")

        if activity_types_found:
            print("\n🏃‍♂️ ACTIVITY TYPES FOUND:")
            for activity_type in sorted(activity_types_found):
                print(f"  - {activity_type}")

            # Check for running activities
            running_types = [
                t
                for t in activity_types_found
                if any(
                    keyword in t.lower()
                    for keyword in ["run", "jog", "marathon", "trail"]
                )
            ]
            if running_types:
                print("\n🏃 RUNNING-RELATED TYPES:")
                for running_type in running_types:
                    print(f"  - {running_type}")
            else:
                print("\n🏃 No obvious running-related activity types found")
                print("Maybe running activities use a different name?")
        else:
            print("\n❌ No activity types could be extracted")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    simple_debug()
