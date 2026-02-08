#!/usr/bin/env python3
"""
Test script to verify Garmin data fetching and display dashboard statistics
This script fetches real data from Garmin Connect using credentials from .env file
and displays the same statistics shown in the dashboard.
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.activity import Activity
from garminconnect import Garmin
from app.core.config import settings
from app.services.garmin_service import GarminService


class GarminStatsTest:
    """Test class to verify Garmin data and dashboard statistics"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.garmin_service = GarminService(self.db)
        self.users = []
        
    async def test_garmin_connections(self):
        """Test connections to Garmin Connect for each user"""
        print("🔗 Testing Garmin Connect API connections...")
        print("=" * 60)
        
        # Test credentials from environment
        test_users = [
            {
                "name": "Anto", 
                "email": getattr(settings, 'ANTO_GARMIN_EMAIL', None),
                "password": getattr(settings, 'ANTO_GARMIN_PASSWORD', None)
            },
            {
                "name": "Jeff", 
                "email": getattr(settings, 'JEFF_GARMIN_EMAIL', None),
                "password": getattr(settings, 'JEFF_GARMIN_PASSWORD', None)
            }
        ]
        
        successful_connections = []
        
        for user_data in test_users:
            if not user_data["email"] or not user_data["password"]:
                print(f"⚠️  {user_data['name']}: Missing credentials in .env file")
                continue
                
            print(f"\n📡 Testing {user_data['name']} ({user_data['email']})...")
            
            try:
                # Initialize Garmin client
                client = Garmin(user_data["email"], user_data["password"])
                
                # Login
                await client.login()
                print(f"✅ {user_data['name']}: Login successful")
                
                # Get recent activities (last 7 days)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)
                
                activities = await client.get_activities_by_date(
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
                
                print(f"📊 {user_data['name']}: Found {len(activities)} activities in last 7 days")
                
                # Show sample activity details
                if activities:
                    activity = activities[0]
                    print(f"   Latest: {activity.get('activityName', 'Unknown')} - {activity.get('startTimeLocal', 'Unknown time')}")
                    print(f"   Distance: {activity.get('distance', 0)/1000:.1f}km")
                    print(f"   Duration: {activity.get('duration', 0)//60}min")
                    print(f"   Calories: {activity.get('calories', 0)}")
                    
                successful_connections.append({
                    **user_data,
                    "recent_activities": activities,
                    "client": client
                })
                
            except Exception as e:
                print(f"❌ {user_data['name']}: Connection failed - {str(e)}")
                print(f"   This could be due to invalid credentials, 2FA requirements, or network issues")
        
        return successful_connections
    
    def get_database_statistics(self):
        """Get current statistics from local database"""
        print("\n\n🗄️ Current Database Statistics")
        print("=" * 60)
        
        # Get all users
        users = self.db.query(User).filter(User.is_active == True).all()
        
        current_date = datetime.now()
        year_start = datetime(current_date.year, 1, 1)
        week_start = current_date - timedelta(days=current_date.weekday())
        month_start = week_start - timedelta(days=28)  # Last 4 weeks
        
        stats = {
            "users": [],
            "group_totals": {
                "ytd_activities": 0,
                "ytd_running_km": 0,
                "ytd_steps": 0,
                "ytd_calories": 0,
                "weekly_activities": 0,
                "weekly_running_km": 0,
                "weekly_steps": 0,
                "weekly_calories": 0
            }
        }
        
        for user in users:
            print(f"\n👤 {user.full_name}")
            print("-" * 40)
            
            # Year-to-date activities
            ytd_activities = (
                self.db.query(Activity)
                .filter(Activity.user_id == user.id)
                .filter(Activity.start_time >= year_start)
                .all()
            )
            
            # Weekly activities
            weekly_activities = (
                self.db.query(Activity)
                .filter(Activity.user_id == user.id)
                .filter(Activity.start_time >= week_start)
                .all()
            )
            
            # Calculate YTD metrics
            ytd_running_km = sum(
                activity.distance_km 
                for activity in ytd_activities 
                if activity.activity_type.lower() == 'running' and activity.distance_km
            )
            
            ytd_cycling_km = sum(
                activity.distance_km 
                for activity in ytd_activities 
                if activity.activity_type.lower() == 'cycling' and activity.distance_km
            )
            
            ytd_steps = sum(
                activity.processed_metrics.get('steps', 0) if activity.processed_metrics else 0
                for activity in ytd_activities
            )
            
            ytd_calories = sum(
                activity.calories for activity in ytd_activities if activity.calories
            )
            
            # Calculate weekly metrics
            weekly_running_km = sum(
                activity.distance_km 
                for activity in weekly_activities 
                if activity.activity_type.lower() == 'running' and activity.distance_km
            )
            
            weekly_steps = sum(
                activity.processed_metrics.get('steps', 0) if activity.processed_metrics else 0
                for activity in weekly_activities
            )
            
            weekly_calories = sum(
                activity.calories for activity in weekly_activities if activity.calories
            )
            
            # Activity breakdown
            activity_breakdown = {}
            for activity in ytd_activities:
                activity_type = activity.activity_type.replace('_', ' ').title()
                activity_breakdown[activity_type] = activity_breakdown.get(activity_type, 0) + 1
            
            user_stats = {
                "name": user.full_name,
                "ytd_activities": len(ytd_activities),
                "ytd_running_km": ytd_running_km,
                "ytd_cycling_km": ytd_cycling_km,
                "ytd_steps": ytd_steps,
                "ytd_calories": ytd_calories,
                "weekly_activities": len(weekly_activities),
                "weekly_running_km": weekly_running_km,
                "weekly_steps": weekly_steps,
                "weekly_calories": weekly_calories,
                "activity_breakdown": activity_breakdown,
                "avg_weekly_activities": len(ytd_activities) / 36,  # Current week of year
                "avg_weekly_running": ytd_running_km / 36
            }
            
            # Print user statistics
            print(f"📊 Year-to-Date (2025):")
            print(f"   • Total Activities: {user_stats['ytd_activities']}")
            print(f"   • Running Distance: {user_stats['ytd_running_km']:.1f}km")
            print(f"   • Cycling Distance: {user_stats['ytd_cycling_km']:.1f}km")
            print(f"   • Total Steps: {user_stats['ytd_steps']:,}")
            print(f"   • Total Calories: {user_stats['ytd_calories']:,}")
            print(f"   • Activity Breakdown: {dict(list(activity_breakdown.items())[:3])}")
            
            print(f"\n📈 Weekly Averages:")
            print(f"   • Activities per week: {user_stats['avg_weekly_activities']:.1f}")
            print(f"   • Running per week: {user_stats['avg_weekly_running']:.1f}km")
            
            print(f"\n📅 Current Week:")
            print(f"   • Activities: {user_stats['weekly_activities']}")
            print(f"   • Running: {user_stats['weekly_running_km']:.1f}km")
            print(f"   • Steps: {user_stats['weekly_steps']:,}")
            print(f"   • Calories: {user_stats['weekly_calories']:,}")
            
            # Add to group totals
            stats["group_totals"]["ytd_activities"] += user_stats['ytd_activities']
            stats["group_totals"]["ytd_running_km"] += user_stats['ytd_running_km']
            stats["group_totals"]["ytd_steps"] += user_stats['ytd_steps']
            stats["group_totals"]["ytd_calories"] += user_stats['ytd_calories']
            stats["group_totals"]["weekly_activities"] += user_stats['weekly_activities']
            stats["group_totals"]["weekly_running_km"] += user_stats['weekly_running_km']
            stats["group_totals"]["weekly_steps"] += user_stats['weekly_steps']
            stats["group_totals"]["weekly_calories"] += user_stats['weekly_calories']
            
            stats["users"].append(user_stats)
        
        return stats
    
    def print_group_summary(self, stats: Dict):
        """Print group summary statistics"""
        print("\n\n🏆 Group Summary")
        print("=" * 60)
        
        group = stats["group_totals"]
        
        print(f"📊 Year-to-Date Group Totals:")
        print(f"   • Total Activities: {group['ytd_activities']}")
        print(f"   • Total Running: {group['ytd_running_km']:.1f}km")
        print(f"   • Total Steps: {group['ytd_steps']:,}")
        print(f"   • Total Calories: {group['ytd_calories']:,}")
        
        print(f"\n📅 Current Week Group Totals:")
        print(f"   • Activities: {group['weekly_activities']}")
        print(f"   • Running: {group['weekly_running_km']:.1f}km")
        print(f"   • Steps: {group['weekly_steps']:,}")
        print(f"   • Calories: {group['weekly_calories']:,}")
        
        # Leaderboards
        users = stats["users"]
        
        print(f"\n🥇 Leaderboards (Year-to-Date):")
        print(f"   • Most Running: {max(users, key=lambda u: u['ytd_running_km'])['name']} ({max(u['ytd_running_km'] for u in users):.0f}km)")
        print(f"   • Most Active: {max(users, key=lambda u: u['ytd_activities'])['name']} ({max(u['ytd_activities'] for u in users)} activities)")
        print(f"   • Most Steps: {max(users, key=lambda u: u['ytd_steps'])['name']} ({max(u['ytd_steps'] for u in users):,} steps)")
        print(f"   • Most Calories: {max(users, key=lambda u: u['ytd_calories'])['name']} ({max(u['ytd_calories'] for u in users):,} calories)")
    
    def test_api_endpoints(self):
        """Test API endpoints that provide dashboard data"""
        print("\n\n🌐 API Endpoint Tests")
        print("=" * 60)
        
        import requests
        
        base_url = "http://localhost:8000/api/v1"
        
        try:
            # Test weekly dashboard endpoint
            print("📡 Testing /dashboard/weekly endpoint...")
            response = requests.get(f"{base_url}/dashboard/weekly", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Weekly endpoint: {len(data.get('users', []))} users, {data.get('totals', {}).get('total_activities', 0)} activities")
                
                # Show sample user data
                if data.get('users'):
                    user = data['users'][0]
                    print(f"   Sample user: {user['name']} - {user['ytd_total_activities']} YTD activities, {user['ytd_running_distance_km']:.0f}km running")
            else:
                print(f"❌ Weekly endpoint failed: HTTP {response.status_code}")
            
            # Test digest endpoint
            print("\n📡 Testing /dashboard/digest/latest endpoint...")
            response = requests.get(f"{base_url}/dashboard/digest/latest", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Digest endpoint: {data.get('summary', {}).get('total_activities', 0)} activities this week")
                print(f"   Most popular activity: {data.get('summary', {}).get('most_popular_activity', 'Unknown')}")
            else:
                print(f"❌ Digest endpoint failed: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API test failed: {e}")
            print("   Make sure the FastAPI server is running on localhost:8000")
    
    async def run_complete_test(self):
        """Run complete test suite"""
        print("🏃‍♂️ Garmin Explorer - Data Verification Test")
        print("=" * 60)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test 1: Garmin API connections
        await self.test_garmin_connections()
        
        # Test 2: Database statistics
        stats = self.get_database_statistics()
        
        # Test 3: Group summary
        self.print_group_summary(stats)
        
        # Test 4: API endpoints
        self.test_api_endpoints()
        
        print("\n" + "=" * 60)
        print("✅ Test suite completed!")
        print("\n💡 To view the dashboard:")
        print("   http://localhost:8000/static/dashboard.html")
        print("\n📚 API Documentation:")
        print("   http://localhost:8000/docs")
        
        self.db.close()


async def main():
    """Main function to run tests"""
    test = GarminStatsTest()
    await test.run_complete_test()


if __name__ == "__main__":
    asyncio.run(main())