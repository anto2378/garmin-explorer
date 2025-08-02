#!/usr/bin/env python3
"""
Garmin Connect Sleep Analysis Script

This script analyzes your sleep data from Garmin Connect, providing insights into:
- Sleep duration patterns
- Sleep quality trends
- Deep sleep, light sleep, and REM sleep analysis
- Weekly and monthly sleep patterns
- Sleep efficiency metrics

Usage:
    python sleep_analysis.py

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
import plotly.graph_objects as go
import seaborn as sns
from garminconnect import Garmin
from plotly.subplots import make_subplots

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Set up plotting style
plt.style.use("seaborn-v0_8")
sns.set_palette("viridis")


class GarminSleepAnalyzer:
    """Specialized class for analyzing Garmin Connect sleep data."""

    def __init__(self):
        """Initialize the Garmin sleep analyzer."""
        self.client = None
        self.sleep_data = []

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

    def fetch_sleep_data(self, days_back: int = 90) -> List[Dict[Any, Any]]:
        """
        Fetch sleep data from the last specified number of days.

        Args:
            days_back (int): Number of days to look back for sleep data.

        Returns:
            List[Dict]: List of sleep data dictionaries.
        """
        print(f"😴 Fetching sleep data from the last {days_back} days...")

        sleep_data = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        current_date = start_date

        while current_date <= end_date:
            try:
                date_str = current_date.strftime("%Y-%m-%d")

                # Get sleep data for this date
                sleep_info = self.client.get_sleep_data(date_str)

                if sleep_info and "dailySleepDTO" in sleep_info:
                    sleep_dto = sleep_info["dailySleepDTO"]

                    # Extract relevant sleep metrics
                    sleep_record = {
                        "date": current_date,
                        "bedtime": None,
                        "wakeup_time": None,
                        "total_sleep_minutes": sleep_dto.get("sleepTimeSeconds", 0)
                        // 60,
                        "deep_sleep_minutes": sleep_dto.get("deepSleepSeconds", 0)
                        // 60,
                        "light_sleep_minutes": sleep_dto.get("lightSleepSeconds", 0)
                        // 60,
                        "rem_sleep_minutes": sleep_dto.get("remSleepSeconds", 0) // 60,
                        "awake_minutes": sleep_dto.get("awakeDuration", 0) // 60,
                        "sleep_score": sleep_dto.get("overallSleepScore", 0),
                        "sleep_efficiency": sleep_dto.get("sleepEfficiency", 0),
                        "sleep_start_timestamp": sleep_dto.get(
                            "sleepStartTimestampGMT"
                        ),
                        "sleep_end_timestamp": sleep_dto.get("sleepEndTimestampGMT"),
                    }

                    # Convert timestamps to readable times if available
                    if sleep_record["sleep_start_timestamp"]:
                        bedtime = datetime.fromtimestamp(
                            sleep_record["sleep_start_timestamp"] / 1000
                        )
                        sleep_record["bedtime"] = bedtime.strftime("%H:%M")

                    if sleep_record["sleep_end_timestamp"]:
                        wakeup = datetime.fromtimestamp(
                            sleep_record["sleep_end_timestamp"] / 1000
                        )
                        sleep_record["wakeup_time"] = wakeup.strftime("%H:%M")

                    sleep_data.append(sleep_record)

            except Exception as e:
                # Skip days where sleep data is not available
                print(f"No sleep data for {date_str}: {e}")
                pass

            current_date += timedelta(days=1)

        self.sleep_data = sleep_data
        print(f"✅ Found sleep data for {len(self.sleep_data)} days")
        return self.sleep_data

    def analyze_sleep_duration(self) -> None:
        """Analyze sleep duration patterns."""
        print("\n😴 SLEEP DURATION ANALYSIS")
        print("=" * 50)

        if not self.sleep_data:
            print("No sleep data available.")
            return

        # Convert to DataFrame
        df = pd.DataFrame(self.sleep_data)
        df["total_sleep_hours"] = df["total_sleep_minutes"] / 60

        # Calculate statistics
        avg_sleep = df["total_sleep_hours"].mean()
        median_sleep = df["total_sleep_hours"].median()
        min_sleep = df["total_sleep_hours"].min()
        max_sleep = df["total_sleep_hours"].max()
        std_sleep = df["total_sleep_hours"].std()

        print(f"📊 Average sleep duration: {avg_sleep:.1f} hours")
        print(f"📈 Median sleep duration: {median_sleep:.1f} hours")
        print(f"⬇️ Minimum sleep: {min_sleep:.1f} hours")
        print(f"⬆️ Maximum sleep: {max_sleep:.1f} hours")
        print(f"📏 Standard deviation: {std_sleep:.1f} hours")

        # Sleep quality categories
        excellent_sleep = len(df[df["total_sleep_hours"] >= 8])
        good_sleep = len(
            df[(df["total_sleep_hours"] >= 7) & (df["total_sleep_hours"] < 8)]
        )
        fair_sleep = len(
            df[(df["total_sleep_hours"] >= 6) & (df["total_sleep_hours"] < 7)]
        )
        poor_sleep = len(df[df["total_sleep_hours"] < 6])

        total_nights = len(df)

        print("\n📊 Sleep Quality Distribution:")
        print(
            f"  🌟 Excellent (8+ hours): {excellent_sleep} nights ({excellent_sleep / total_nights * 100:.1f}%)"
        )
        print(
            f"  👍 Good (7-8 hours): {good_sleep} nights ({good_sleep / total_nights * 100:.1f}%)"
        )
        print(
            f"  😐 Fair (6-7 hours): {fair_sleep} nights ({fair_sleep / total_nights * 100:.1f}%)"
        )
        print(
            f"  😴 Poor (<6 hours): {poor_sleep} nights ({poor_sleep / total_nights * 100:.1f}%)"
        )

    def analyze_sleep_stages(self) -> None:
        """Analyze sleep stage distribution."""
        print("\n🌙 SLEEP STAGES ANALYSIS")
        print("=" * 50)

        if not self.sleep_data:
            print("No sleep data available.")
            return

        # Convert to DataFrame
        df = pd.DataFrame(self.sleep_data)

        # Calculate averages for each sleep stage
        avg_deep = df["deep_sleep_minutes"].mean()
        avg_light = df["light_sleep_minutes"].mean()
        avg_rem = df["rem_sleep_minutes"].mean()
        avg_awake = df["awake_minutes"].mean()

        print(
            f"💤 Average Deep Sleep: {avg_deep:.0f} minutes ({avg_deep / 60:.1f} hours)"
        )
        print(
            f"🌅 Average Light Sleep: {avg_light:.0f} minutes ({avg_light / 60:.1f} hours)"
        )
        print(f"🧠 Average REM Sleep: {avg_rem:.0f} minutes ({avg_rem / 60:.1f} hours)")
        print(
            f"👁️ Average Awake Time: {avg_awake:.0f} minutes ({avg_awake / 60:.1f} hours)"
        )

        # Calculate percentages
        total_sleep = avg_deep + avg_light + avg_rem
        if total_sleep > 0:
            deep_pct = (avg_deep / total_sleep) * 100
            light_pct = (avg_light / total_sleep) * 100
            rem_pct = (avg_rem / total_sleep) * 100

            print("\n📊 Sleep Stage Distribution:")
            print(f"  💤 Deep Sleep: {deep_pct:.1f}%")
            print(f"  🌅 Light Sleep: {light_pct:.1f}%")
            print(f"  🧠 REM Sleep: {rem_pct:.1f}%")

    def analyze_sleep_efficiency(self) -> None:
        """Analyze sleep efficiency and quality scores."""
        print("\n⚡ SLEEP EFFICIENCY ANALYSIS")
        print("=" * 50)

        if not self.sleep_data:
            print("No sleep data available.")
            return

        # Convert to DataFrame
        df = pd.DataFrame(self.sleep_data)

        # Filter out zero scores (no data)
        df_scores = df[df["sleep_score"] > 0]
        df_efficiency = df[df["sleep_efficiency"] > 0]

        if not df_scores.empty:
            avg_score = df_scores["sleep_score"].mean()
            median_score = df_scores["sleep_score"].median()
            min_score = df_scores["sleep_score"].min()
            max_score = df_scores["sleep_score"].max()

            print(f"🎯 Average Sleep Score: {avg_score:.0f}/100")
            print(f"📈 Median Sleep Score: {median_score:.0f}/100")
            print(f"⬇️ Lowest Score: {min_score:.0f}/100")
            print(f"⬆️ Highest Score: {max_score:.0f}/100")

        if not df_efficiency.empty:
            avg_efficiency = df_efficiency["sleep_efficiency"].mean()
            median_efficiency = df_efficiency["sleep_efficiency"].median()

            print(f"\n💯 Average Sleep Efficiency: {avg_efficiency:.1f}%")
            print(f"📈 Median Sleep Efficiency: {median_efficiency:.1f}%")

    def create_sleep_visualizations(self) -> None:
        """Create comprehensive sleep visualizations."""
        print("\n📊 CREATING SLEEP VISUALIZATIONS")
        print("=" * 50)

        if not self.sleep_data:
            print("No sleep data available.")
            return

        # Convert to DataFrame
        df = pd.DataFrame(self.sleep_data)
        df["total_sleep_hours"] = df["total_sleep_minutes"] / 60

        # Create a comprehensive dashboard
        fig = make_subplots(
            rows=3,
            cols=2,
            subplot_titles=[
                "Sleep Duration Over Time",
                "Sleep Stages Distribution",
                "Sleep Efficiency Trend",
                "Bedtime vs Wake Time",
                "Sleep Score Distribution",
                "Weekly Sleep Pattern",
            ],
            specs=[
                [{"secondary_y": False}, {"type": "pie"}],
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"type": "histogram"}, {"secondary_y": False}],
            ],
        )

        # 1. Sleep Duration Over Time
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["total_sleep_hours"],
                mode="lines+markers",
                name="Sleep Duration",
                line=dict(color="royalblue", width=2),
            ),
            row=1,
            col=1,
        )

        # Add ideal sleep range
        fig.add_hline(
            y=8, line_dash="dash", line_color="green", opacity=0.5, row=1, col=1
        )
        fig.add_hline(
            y=7, line_dash="dash", line_color="orange", opacity=0.5, row=1, col=1
        )

        # 2. Average Sleep Stages Pie Chart
        avg_deep = df["deep_sleep_minutes"].mean()
        avg_light = df["light_sleep_minutes"].mean()
        avg_rem = df["rem_sleep_minutes"].mean()

        fig.add_trace(
            go.Pie(
                labels=["Deep Sleep", "Light Sleep", "REM Sleep"],
                values=[avg_deep, avg_light, avg_rem],
                hole=0.3,
                marker_colors=["darkblue", "lightblue", "purple"],
            ),
            row=1,
            col=2,
        )

        # 3. Sleep Efficiency Trend
        efficiency_data = df[df["sleep_efficiency"] > 0]
        if not efficiency_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=efficiency_data["date"],
                    y=efficiency_data["sleep_efficiency"],
                    mode="lines+markers",
                    name="Sleep Efficiency",
                    line=dict(color="green", width=2),
                ),
                row=2,
                col=1,
            )

        # 4. Bedtime vs Wake Time (if available)
        bedtime_data = df.dropna(subset=["bedtime", "wakeup_time"])
        if not bedtime_data.empty:
            # Convert times to hours for plotting
            bedtime_hours = bedtime_data["bedtime"].apply(
                lambda x: int(x.split(":")[0]) + int(x.split(":")[1]) / 60
                if x
                else None
            )
            wakeup_hours = bedtime_data["wakeup_time"].apply(
                lambda x: int(x.split(":")[0]) + int(x.split(":")[1]) / 60
                if x
                else None
            )

            fig.add_trace(
                go.Scatter(
                    x=bedtime_data["date"],
                    y=bedtime_hours,
                    mode="markers",
                    name="Bedtime",
                    marker=dict(color="darkred", size=6),
                ),
                row=2,
                col=2,
            )

            fig.add_trace(
                go.Scatter(
                    x=bedtime_data["date"],
                    y=wakeup_hours,
                    mode="markers",
                    name="Wake Time",
                    marker=dict(color="orange", size=6),
                ),
                row=2,
                col=2,
            )

        # 5. Sleep Score Distribution
        score_data = df[df["sleep_score"] > 0]
        if not score_data.empty:
            fig.add_trace(
                go.Histogram(
                    x=score_data["sleep_score"],
                    name="Sleep Score",
                    marker_color="teal",
                    nbinsx=20,
                ),
                row=3,
                col=1,
            )

        # 6. Weekly Sleep Pattern
        df["day_of_week"] = df["date"].dt.day_name()
        weekly_avg = (
            df.groupby("day_of_week")["total_sleep_hours"]
            .mean()
            .reindex(
                [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ]
            )
        )

        fig.add_trace(
            go.Bar(
                x=weekly_avg.index,
                y=weekly_avg.values,
                name="Weekly Average",
                marker_color="lightcoral",
            ),
            row=3,
            col=2,
        )

        # Update layout
        fig.update_layout(
            height=1200,
            title_text="Comprehensive Sleep Analysis Dashboard",
            title_x=0.5,
            showlegend=False,
        )

        # Update y-axis labels
        fig.update_yaxes(title_text="Hours", row=1, col=1)
        fig.update_yaxes(title_text="Efficiency %", row=2, col=1)
        fig.update_yaxes(title_text="Hour of Day", row=2, col=2)
        fig.update_yaxes(title_text="Frequency", row=3, col=1)
        fig.update_yaxes(title_text="Hours", row=3, col=2)

        # Save and show
        fig.write_html("sleep_analysis_dashboard.html")
        fig.show()

        print("📊 Interactive sleep dashboard saved as 'sleep_analysis_dashboard.html'")

        # Create additional matplotlib plots
        self._create_detailed_plots(df)

    def _create_detailed_plots(self, df: pd.DataFrame) -> None:
        """Create detailed matplotlib plots."""

        # Sleep trends plot
        plt.figure(figsize=(15, 10))

        # Plot 1: Sleep duration trend
        plt.subplot(2, 2, 1)
        plt.plot(
            df["date"], df["total_sleep_hours"], marker="o", linewidth=2, markersize=4
        )
        plt.axhline(y=8, color="green", linestyle="--", alpha=0.7, label="Ideal (8h)")
        plt.axhline(y=7, color="orange", linestyle="--", alpha=0.7, label="Good (7h)")
        plt.title("Sleep Duration Trend", fontweight="bold")
        plt.ylabel("Hours")
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Plot 2: Sleep stages stacked area
        plt.subplot(2, 2, 2)
        plt.stackplot(
            df["date"],
            df["deep_sleep_minutes"] / 60,
            df["light_sleep_minutes"] / 60,
            df["rem_sleep_minutes"] / 60,
            labels=["Deep", "Light", "REM"],
            alpha=0.8,
        )
        plt.title("Sleep Stages Over Time", fontweight="bold")
        plt.ylabel("Hours")
        plt.legend(loc="upper right")
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)

        # Plot 3: Sleep efficiency
        efficiency_data = df[df["sleep_efficiency"] > 0]
        if not efficiency_data.empty:
            plt.subplot(2, 2, 3)
            plt.plot(
                efficiency_data["date"],
                efficiency_data["sleep_efficiency"],
                marker="o",
                linewidth=2,
                markersize=4,
                color="green",
            )
            plt.title("Sleep Efficiency Trend", fontweight="bold")
            plt.ylabel("Efficiency %")
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)

        # Plot 4: Weekly pattern
        plt.subplot(2, 2, 4)
        df["day_of_week"] = df["date"].dt.day_name()
        weekly_avg = (
            df.groupby("day_of_week")["total_sleep_hours"]
            .mean()
            .reindex(
                [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ]
            )
        )

        bars = plt.bar(
            weekly_avg.index, weekly_avg.values, color="lightcoral", alpha=0.8
        )
        plt.title("Average Sleep by Day of Week", fontweight="bold")
        plt.ylabel("Hours")
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 0.05,
                f"{height:.1f}h",
                ha="center",
                va="bottom",
            )

        plt.tight_layout()
        plt.savefig("detailed_sleep_analysis.png", dpi=300, bbox_inches="tight")
        plt.show()

        print("📊 Detailed sleep analysis plots saved as 'detailed_sleep_analysis.png'")

    def generate_sleep_report(self) -> None:
        """Generate a comprehensive sleep analysis report."""
        print("\n📋 SLEEP ANALYSIS REPORT")
        print("=" * 50)

        if not self.sleep_data:
            print("No sleep data available for analysis.")
            return

        df = pd.DataFrame(self.sleep_data)
        df["total_sleep_hours"] = df["total_sleep_minutes"] / 60

        print(f"📅 Analysis period: {len(self.sleep_data)} nights")
        print(
            f"📊 Data completeness: {len(df[df['total_sleep_hours'] > 0])}/{len(df)} nights with data"
        )

        # Sleep recommendations
        avg_sleep = df["total_sleep_hours"].mean()

        print("\n💡 SLEEP INSIGHTS & RECOMMENDATIONS:")
        print("=" * 40)

        if avg_sleep >= 8:
            print("🌟 Excellent! You're getting adequate sleep on average.")
        elif avg_sleep >= 7:
            print("👍 Good sleep duration, but there's room for improvement.")
        elif avg_sleep >= 6:
            print("😐 Fair sleep duration. Consider prioritizing more sleep.")
        else:
            print("😴 You may be sleep-deprived. Consider improving sleep hygiene.")

        # Consistency analysis
        sleep_std = df["total_sleep_hours"].std()
        if sleep_std < 0.5:
            print("📈 Great sleep consistency!")
        elif sleep_std < 1.0:
            print("📊 Moderate sleep consistency - try to maintain regular bedtimes.")
        else:
            print(
                "📉 Inconsistent sleep patterns - focus on sleep schedule regularity."
            )

        # Files generated
        print("\n📊 Generated Files:")
        print("  • sleep_analysis_dashboard.html (Interactive dashboard)")
        print("  • detailed_sleep_analysis.png (Detailed plots)")

        print("\n✨ Sleep analysis complete!")


def main():
    """Main function to run the sleep analysis."""
    print("😴 Garmin Connect Sleep Data Analyzer")
    print("=" * 50)

    analyzer = GarminSleepAnalyzer()

    # Authenticate
    if not analyzer.authenticate():
        print("Failed to authenticate. Exiting.")
        sys.exit(1)

    # Fetch sleep data
    analyzer.fetch_sleep_data(90)  # Last 3 months

    # Perform analysis
    analyzer.analyze_sleep_duration()
    analyzer.analyze_sleep_stages()
    analyzer.analyze_sleep_efficiency()
    analyzer.create_sleep_visualizations()
    analyzer.generate_sleep_report()


if __name__ == "__main__":
    main()
