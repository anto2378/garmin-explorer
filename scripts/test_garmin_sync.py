#!/usr/bin/env python3
"""
Test script to sync real Garmin data
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from garminconnect import Garmin

async def test_garmin_connection():
    """Test direct Garmin connection"""
    
    print("🔗 Testing Garmin connection...")
    
    # Test credentials from .env.production
    anto_email = "antosidoti@gmail.com"
    anto_password = "21031993Garmin"
    
    jeff_email = "geoffroy.lepivan@gmail.com"
    jeff_password = "hawxoggikkuR9zawje"
    
    for name, email, password in [("Anto", anto_email, anto_password), ("Jeff", jeff_email, jeff_password)]:
        print(f"\n📡 Testing {name} ({email})...")
        
        try:
            # Initialize Garmin client
            client = Garmin(email, password)
            
            # Login
            await client.login()
            print(f"✅ {name}: Login successful")
            
            # Get recent activities (last 7 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            activities = await client.get_activities_by_date(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            print(f"📊 {name}: Found {len(activities)} activities in last 7 days")
            
            # Show sample activity
            if activities:
                activity = activities[0]
                print(f"   Latest: {activity.get('activityName', 'Unknown')} - {activity.get('startTimeLocal', 'Unknown time')}")
                print(f"   Distance: {activity.get('distance', 0)/1000:.1f}km")
                print(f"   Duration: {activity.get('duration', 0)//60}min")
                
        except Exception as e:
            print(f"❌ {name}: Connection failed - {str(e)}")
            print(f"   This could be due to invalid credentials or 2FA requirements")

def main():
    """Main function"""
    asyncio.run(test_garmin_connection())

if __name__ == "__main__":
    main()