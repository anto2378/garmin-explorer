#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "garminconnect>=0.2.19",
#     "rich>=13.7.0",
# ]
# ///
"""
Command-line tool to test Garmin authentication and fetch recent activities.

Usage:
    # With credentials file
    uv run cli_test.py --credentials creds.json
    
    # With direct input
    uv run cli_test.py --email your@email.com --password yourpass
    
    # Custom date range
    uv run cli_test.py --credentials creds.json --days 60
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from garminconnect import Garmin
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except ImportError:
    print("❌ Dependencies not installed. Run with: uv run cli_test.py")
    sys.exit(1)

console = Console()


def load_credentials_from_file(filepath: str) -> dict:
    """Load credentials from JSON file"""
    try:
        with open(filepath, 'r') as f:
            creds = json.load(f)
            
        # Support multiple formats
        if isinstance(creds, list) and len(creds) > 0:
            creds = creds[0]
            
        email = creds.get('email') or creds.get('garmin_email') or creds.get('username')
        password = creds.get('password') or creds.get('garmin_password')
        
        if not email or not password:
            console.print("[red]❌ JSON must contain 'email' and 'password' fields[/red]")
            sys.exit(1)
            
        return {'email': email, 'password': password}
    except FileNotFoundError:
        console.print(f"[red]❌ File not found: {filepath}[/red]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]❌ Invalid JSON: {e}[/red]")
        sys.exit(1)


def test_garmin_auth(email: str, password: str, days_back: int = 30) -> bool:
    """Test Garmin authentication and fetch recent activities"""
    
    console.print(Panel.fit(
        f"[bold cyan]🔐 Garmin Connect Authentication Test[/bold cyan]\n"
        f"Email: [yellow]{email}[/yellow]\n"
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        border_style="cyan"
    ))
    
    # Step 1: Initialize
    console.print("\n[bold]Step 1:[/bold] Initializing Garmin client...")
    try:
        client = Garmin(email, password)
        console.print("[green]✓[/green] Client initialized")
    except Exception as e:
        console.print(f"[red]✗ Failed: {e}[/red]")
        return False
    
    # Step 2: Authenticate
    console.print("\n[bold]Step 2:[/bold] Authenticating...")
    try:
        client.login()
        console.print("[green]✓[/green] Authentication successful!")
    except Exception as e:
        console.print(f"[red]✗ Authentication failed: {e}[/red]")
        console.print("\n[yellow]Troubleshooting:[/yellow]")
        console.print("  1. Verify email and password")
        console.print("  2. Check if 2FA is enabled (not supported)")
        console.print("  3. Try https://connect.garmin.com")
        return False
    
    # Step 3: Get user info
    console.print("\n[bold]Step 3:[/bold] Fetching profile...")
    try:
        user_summary = client.get_user_summary(datetime.now().strftime('%Y-%m-%d'))
        display_name = user_summary.get('displayName', 'Unknown')
        console.print(f"[green]✓[/green] Welcome, [bold]{display_name}[/bold]!")
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Could not fetch profile: {e}")
    
    # Step 4: Fetch activities
    console.print(f"\n[bold]Step 4:[/bold] Fetching activities (last {days_back} days)...")
    try:
        start_date = datetime.now() - timedelta(days=days_back)
        activities = client.get_activities(0, 100)
        
        if not activities:
            console.print("[yellow]⚠[/yellow] No activities found")
            return True
        
        # Filter by date
        filtered = []
        for activity in activities:
            date_str = activity.get("startTimeLocal", "")
            if date_str:
                try:
                    activity_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    activity_date = activity_date.replace(tzinfo=None)
                    if activity_date >= start_date:
                        filtered.append(activity)
                except:
                    continue
        
        console.print(f"[green]✓[/green] Found {len(filtered)} activities")
        
        # Display table
        if filtered:
            console.print(f"\n[bold]Recent Activities:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Date", style="cyan", width=12)
            table.add_column("Activity", style="green", width=25)
            table.add_column("Distance", justify="right", width=10)
            table.add_column("Duration", justify="right", width=10)
            table.add_column("Calories", justify="right", width=10)
            
            total_distance = 0
            total_calories = 0
            total_duration = 0
            
            for activity in filtered[:20]:
                date_str = activity.get("startTimeLocal", "")[:10]
                name = activity.get("activityName", "Unnamed")
                activity_type = activity.get("activityType", {}).get("typeKey", "")
                
                distance_m = activity.get("distance", 0)
                distance_km = distance_m / 1000 if distance_m else 0
                
                duration_s = activity.get("duration", 0)
                h = int(duration_s // 3600)
                m = int((duration_s % 3600) // 60)
                s = int(duration_s % 60)
                duration_str = f"{h:02d}:{m:02d}:{s:02d}" if duration_s else "-"
                
                calories = activity.get("calories", 0)
                
                table.add_row(
                    date_str,
                    f"{name} ({activity_type})"[:25],
                    f"{distance_km:.2f} km" if distance_km else "-",
                    duration_str,
                    f"{calories:,}" if calories else "-"
                )
                
                total_distance += distance_km
                total_calories += calories
                total_duration += duration_s
            
            console.print(table)
            
            # Summary
            console.print(f"\n[bold]Summary:[/bold]")
            console.print(f"  • Activities: [cyan]{len(filtered)}[/cyan]")
            console.print(f"  • Distance: [cyan]{total_distance:.2f} km[/cyan]")
            console.print(f"  • Calories: [cyan]{total_calories:,}[/cyan]")
            console.print(f"  • Time: [cyan]{total_duration/3600:.2f} hours[/cyan]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Failed to fetch activities: {e}[/red]")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test Garmin Connect authentication",
        epilog="""
Examples:
  uv run cli_test.py --credentials creds.json
  uv run cli_test.py --email user@email.com --password pass
  uv run cli_test.py --credentials creds.json --days 60
        """
    )
    
    parser.add_argument('--credentials', '-c', help='Path to JSON credentials file')
    parser.add_argument('--email', '-e', help='Garmin email')
    parser.add_argument('--password', '-p', help='Garmin password')
    parser.add_argument('--days', '-d', type=int, default=30, help='Days back (default: 30)')
    
    args = parser.parse_args()
    
    # Get credentials
    if args.credentials:
        creds = load_credentials_from_file(args.credentials)
        email = creds['email']
        password = creds['password']
    elif args.email and args.password:
        email = args.email
        password = args.password
    else:
        console.print("[red]❌ Provide --credentials or --email + --password[/red]")
        parser.print_help()
        sys.exit(1)
    
    # Run test
    success = test_garmin_auth(email, password, args.days)
    
    if success:
        console.print("\n[bold green]✅ Test completed successfully![/bold green]")
        sys.exit(0)
    else:
        console.print("\n[bold red]❌ Test failed[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
