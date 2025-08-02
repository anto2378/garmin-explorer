#!/usr/bin/env python3
"""
Garmin Connect Data Analysis Example

This script connects to your Garmin Connect account and analyzes your activity data,
providing insights into your running performance, monthly trends, and daily steps.

Usage:
    python example.py

Make sure to set your Garmin Connect credentials as environment variables:
    GARMIN_EMAIL=your_email@example.com
    GARMIN_PASSWORD=your_password

Or you will be prompted to enter them when running the script.
"""

import os
import sys
import warnings
from datetime import datetime, timedelta
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from garminconnect import Garmin

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Set up plotting style
plt.style.use("seaborn-v0_8")
sns.set_palette("husl")


class GarminAnalyzer:
    """Main class for analyzing Garmin Connect data."""

    def __init__(self):
        """Initialize the Garmin analyzer."""
        self.client = None
        self.activities = []
        self.user_stats = {}

    def authenticate(self) -> bool:
        """
        Authenticate with Garmin Connect.

        Returns:
            bool: True if authentication successful, False otherwise.
        """
        print("🔐 Authenticating with Garmin Connect...")

        # Try to get credentials from environment variables
        email = os.getenv("GARMIN_EMAIL")
        password = os.getenv("GARMIN_PASSWORD")

        # If not in env vars, prompt user
        if not email:
            email = input("Enter your Garmin Connect email: ")
        if not password:
            import getpass

            password = getpass.getpass("Enter your Garmin Connect password: ")

        try:
            self.client = Garmin(email, password)
            self.client.login()
            print("✅ Successfully authenticated with Garmin Connect!")
            return True
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False

    def fetch_activities(self, days_back: int = 365) -> List[Dict[Any, Any]]:
        """
        Fetch activities from the last specified number of days.

        Args:
            days_back (int): Number of days to look back for activities.

        Returns:
            List[Dict]: List of activity dictionaries.
        """
        print(f"📊 Fetching activities from the last {days_back} days...")

        try:
            # Get activities for the specified period
            activities = self.client.get_activities(
                0, days_back * 2
            )  # Get more than needed, then filter

            # Filter to only include activities from the last 'days_back' days
            cutoff_date = datetime.now() - timedelta(days=days_back)

            filtered_activities = []
            for activity in activities:
                activity_date = datetime.strptime(
                    activity["startTimeLocal"][:10], "%Y-%m-%d"
                )
                if activity_date >= cutoff_date:
                    filtered_activities.append(activity)

            self.activities = filtered_activities
            print(
                f"✅ Found {len(self.activities)} activities in the last {days_back} days"
            )
            return self.activities

        except Exception as e:
            print(f"❌ Error fetching activities: {e}")
            return []

    def fetch_user_stats(self) -> Dict[str, Any]:
        """
        Fetch user statistics and profile information.

        Returns:
            Dict: User statistics and profile data.
        """
        print("👤 Fetching user profile and statistics...")

        try:
            # Get user stats
            stats = self.client.get_user_summary(datetime.now().strftime("%Y-%m-%d"))
            profile = self.client.get_full_name()

            self.user_stats = {"profile": profile, "daily_stats": stats}

            print("✅ Successfully fetched user statistics")
            return self.user_stats

        except Exception as e:
            print(f"❌ Error fetching user stats: {e}")
            return {}

    def analyze_running_stats(self) -> None:
        """Analyze and display running statistics."""
        print("\n🏃‍♂️ RUNNING STATISTICS")
        print("=" * 50)

        if not self.activities:
            print("No activities found.")
            return

        # Convert activities to DataFrame for easier analysis
        df = pd.DataFrame(self.activities)

        # Extract the actual activity type from the nested structure
        def get_activity_type(activity_type_obj):
            if isinstance(activity_type_obj, dict):
                return activity_type_obj.get("typeKey", "unknown")
            return str(activity_type_obj).lower()

        df["activityTypeKey"] = df["activityType"].apply(get_activity_type)

        # Filter for running activities (more flexible matching)
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
        running_pattern = "|".join(running_keywords)
        running_activities = df[
            df["activityTypeKey"].str.contains(running_pattern, case=False, na=False)
        ]

        if running_activities.empty:
            print("No running activities found.")
            print("Available activity types:")
            unique_types = df["activityTypeKey"].unique()
            for activity_type in unique_types:
                print(f"  - {activity_type}")
            return

        # Convert distance from meters to kilometers
        running_activities = running_activities.copy()
        running_activities["distanceKm"] = running_activities["distance"] / 1000
        running_activities["durationHours"] = running_activities["duration"] / 3600

        # Calculate total statistics
        total_km = running_activities["distanceKm"].sum()
        total_runs = len(running_activities)
        avg_distance = running_activities["distanceKm"].mean()
        total_time_hours = running_activities["durationHours"].sum()

        print(f"📈 Total kilometers run: {total_km:.2f} km")
        print(f"🏃 Total number of runs: {total_runs}")
        print(f"📏 Average distance per run: {avg_distance:.2f} km")
        print(f"⏱️  Total running time: {total_time_hours:.1f} hours")

        if total_time_hours > 0:
            avg_pace = total_time_hours / total_km * 60  # minutes per km
            print(f"⚡ Average pace: {avg_pace:.2f} min/km")

        # Find longest run
        if not running_activities.empty:
            longest_run = running_activities.loc[
                running_activities["distanceKm"].idxmax()
            ]
            print(
                f"🏆 Longest run: {longest_run['distanceKm']:.2f} km on {longest_run['startTimeLocal'][:10]}"
            )

    def analyze_monthly_trends(self) -> None:
        """Analyze and visualize monthly running trends."""
        print("\n📅 MONTHLY RUNNING TRENDS")
        print("=" * 50)

        if not self.activities:
            print("No activities found.")
            return

        # Convert activities to DataFrame
        df = pd.DataFrame(self.activities)

        # Extract the actual activity type from the nested structure
        def get_activity_type(activity_type_obj):
            if isinstance(activity_type_obj, dict):
                return activity_type_obj.get("typeKey", "unknown")
            return str(activity_type_obj).lower()

        df["activityTypeKey"] = df["activityType"].apply(get_activity_type)

        # Filter for running activities (more flexible matching)
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
        running_pattern = "|".join(running_keywords)
        running_activities = df[
            df["activityTypeKey"].str.contains(running_pattern, case=False, na=False)
        ]

        if running_activities.empty:
            print("No running activities found.")
            return

        # Convert distance and add date columns
        running_activities = running_activities.copy()
        running_activities["distanceKm"] = running_activities["distance"] / 1000
        running_activities["date"] = pd.to_datetime(
            running_activities["startTimeLocal"]
        )
        running_activities["month"] = running_activities["date"].dt.to_period("M")

        # Group by month
        monthly_stats = (
            running_activities.groupby("month")
            .agg({"distanceKm": ["sum", "count", "mean"], "duration": "sum"})
            .round(2)
        )

        # Flatten column names
        monthly_stats.columns = [
            "total_km",
            "num_runs",
            "avg_distance",
            "total_duration",
        ]
        monthly_stats = monthly_stats.reset_index()
        monthly_stats["month_str"] = monthly_stats["month"].astype(str)

        print("Monthly Summary:")
        for _, row in monthly_stats.iterrows():
            duration_hours = row["total_duration"] / 3600
            print(
                f"  {row['month_str']}: {row['total_km']:.1f} km, {row['num_runs']} runs, {duration_hours:.1f}h"
            )

        # Create visualization
        if len(monthly_stats) > 1:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

            # Plot monthly distance
            ax1.bar(
                monthly_stats["month_str"],
                monthly_stats["total_km"],
                color="steelblue",
                alpha=0.7,
            )
            ax1.set_title("Monthly Running Distance", fontsize=14, fontweight="bold")
            ax1.set_ylabel("Distance (km)")
            ax1.tick_params(axis="x", rotation=45)
            ax1.grid(True, alpha=0.3)

            # Plot number of runs
            ax2.bar(
                monthly_stats["month_str"],
                monthly_stats["num_runs"],
                color="coral",
                alpha=0.7,
            )
            ax2.set_title("Monthly Number of Runs", fontsize=14, fontweight="bold")
            ax2.set_ylabel("Number of Runs")
            ax2.set_xlabel("Month")
            ax2.tick_params(axis="x", rotation=45)
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.savefig("monthly_running_trends.png", dpi=300, bbox_inches="tight")
            plt.show()
            print("📊 Monthly trends chart saved as 'monthly_running_trends.png'")

    def analyze_daily_steps(self) -> None:
        """Analyze daily steps data."""
        print("\n👣 DAILY STEPS ANALYSIS")
        print("=" * 50)

        try:
            # Get steps data for the last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            steps_data = []
            current_date = start_date

            print("Fetching daily steps data...")
            while current_date <= end_date:
                try:
                    date_str = current_date.strftime("%Y-%m-%d")
                    daily_stats = self.client.get_user_summary(date_str)

                    if daily_stats and "totalSteps" in daily_stats:
                        steps_data.append(
                            {
                                "date": current_date,
                                "steps": daily_stats["totalSteps"] or 0,
                            }
                        )

                except Exception:
                    # Skip days where data is not available
                    pass

                current_date += timedelta(days=1)

            if not steps_data:
                print("No steps data available.")
                return

            # Convert to DataFrame
            steps_df = pd.DataFrame(steps_data)

            # Calculate statistics
            avg_steps = steps_df["steps"].mean()
            max_steps = steps_df["steps"].max()
            min_steps = steps_df["steps"].min()
            total_steps = steps_df["steps"].sum()

            print(f"📊 Average daily steps: {avg_steps:.0f}")
            print(f"🏆 Maximum daily steps: {max_steps:,}")
            print(f"📉 Minimum daily steps: {min_steps:,}")
            print(f"🔢 Total steps (30 days): {total_steps:,}")

            # Days with > 10,000 steps
            active_days = len(steps_df[steps_df["steps"] >= 10000])
            print(f"🎯 Days with 10,000+ steps: {active_days} out of {len(steps_df)}")

            # Create visualization
            if len(steps_df) > 1:
                plt.figure(figsize=(12, 6))
                plt.plot(
                    steps_df["date"],
                    steps_df["steps"],
                    marker="o",
                    linewidth=2,
                    markersize=4,
                )
                plt.axhline(
                    y=10000,
                    color="red",
                    linestyle="--",
                    alpha=0.7,
                    label="10,000 steps goal",
                )
                plt.axhline(
                    y=avg_steps,
                    color="green",
                    linestyle="--",
                    alpha=0.7,
                    label=f"Average ({avg_steps:.0f})",
                )
                plt.title("Daily Steps - Last 30 Days", fontsize=14, fontweight="bold")
                plt.xlabel("Date")
                plt.ylabel("Steps")
                plt.xticks(rotation=45)
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig("daily_steps.png", dpi=300, bbox_inches="tight")
                plt.show()
                print("📊 Daily steps chart saved as 'daily_steps.png'")

        except Exception as e:
            print(f"❌ Error fetching steps data: {e}")

    def generate_summary_report(self) -> None:
        """Generate a comprehensive summary report."""
        print("\n📋 SUMMARY REPORT")
        print("=" * 50)

        if self.user_stats and "profile" in self.user_stats:
            print(f"👤 User: {self.user_stats['profile']}")

        print("📅 Analysis period: Last 365 days")
        print(f"📊 Total activities found: {len(self.activities)}")

        if self.activities:
            # Activity type breakdown
            df = pd.DataFrame(self.activities)

            # Extract the actual activity type from the nested structure
            def get_activity_type(activity_type_obj):
                if isinstance(activity_type_obj, dict):
                    return activity_type_obj.get("typeKey", "unknown")
                return str(activity_type_obj)

            df["activityTypeKey"] = df["activityType"].apply(get_activity_type)
            activity_types = df["activityTypeKey"].value_counts()

            print("\n🏃‍♂️ Activity Breakdown:")
            for activity_type, count in activity_types.head(5).items():
                print(f"  {activity_type}: {count} activities")

        print("\n📈 Charts generated:")
        print("  • monthly_running_trends.png")
        print("  • daily_steps.png")
        print("\n✨ Analysis complete!")


def main():
    """Main function to run the Garmin data analysis."""
    print("🏃‍♂️ Garmin Connect Data Analyzer")
    print("=" * 50)

    analyzer = GarminAnalyzer()

    # Authenticate
    if not analyzer.authenticate():
        print("Failed to authenticate. Exiting.")
        sys.exit(1)

    # Fetch data
    analyzer.fetch_user_stats()
    analyzer.fetch_activities(365)  # Last year

    # Perform analysis
    analyzer.analyze_running_stats()
    analyzer.analyze_monthly_trends()
    analyzer.analyze_daily_steps()
    analyzer.generate_summary_report()


if __name__ == "__main__":
    main()
