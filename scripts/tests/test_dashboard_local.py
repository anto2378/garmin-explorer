#!/usr/bin/env python3
"""
Local testing script for the dashboard
Creates test data and starts the server
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.database import Base
from app.models.user import User
from app.models.activity import Activity

# Create SQLite database and test data
def create_test_data():
    """Create test database with sample data"""
    
    # Create database
    DATABASE_URL = "sqlite:///./test_garmin.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if we already have data
        if db.query(User).count() > 0:
            print("✅ Test data already exists")
            return
        
        # Create test users
        users = [
            User(
                email="john@test.com",
                full_name="John Runner",
                garmin_email="encrypted_john_email",
                garmin_password="encrypted_john_password",
                is_active=True
            ),
            User(
                email="sarah@test.com", 
                full_name="Sarah Cyclist",
                garmin_email="encrypted_sarah_email",
                garmin_password="encrypted_sarah_password",
                is_active=True
            ),
            User(
                email="mike@test.com",
                full_name="Mike Walker",
                garmin_email="encrypted_mike_email",
                garmin_password="encrypted_mike_password",
                is_active=True
            ),
            User(
                email="emma@test.com",
                full_name="Emma Swimmer",
                garmin_email="encrypted_emma_email",
                garmin_password="encrypted_emma_password",
                is_active=True
            ),
            User(
                email="alex@test.com",
                full_name="Alex Hiker",
                garmin_email="encrypted_alex_email",
                garmin_password="encrypted_alex_password",
                is_active=True
            )
        ]
        
        # Add users to database
        for user in users:
            db.add(user)
        db.commit()
        
        # Refresh to get IDs
        for user in users:
            db.refresh(user)
        
        # Create test activities for current week
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        
        activities = []
        
        # John's activities (runner)
        for i in range(5):
            activity_date = week_start + timedelta(days=i)
            activities.append(Activity(
                user_id=users[0].id,
                garmin_activity_id=f"john_run_{i}",
                activity_type="running",
                activity_name=f"Morning Run {i+1}",
                start_time=activity_date.replace(hour=7, minute=0),
                duration=3600 + (i * 300),  # 1-2 hours
                distance=8000 + (i * 1000),  # 8-12 km in meters
                calories=600 + (i * 50),
                avg_heart_rate=150 + i,
                processed_metrics={
                    "steps": 10000 + (i * 1500),
                    "active_calories": 600 + (i * 50)
                }
            ))
        
        # Sarah's activities (cyclist)
        for i in range(4):
            activity_date = week_start + timedelta(days=i)
            activities.append(Activity(
                user_id=users[1].id,
                garmin_activity_id=f"sarah_cycle_{i}",
                activity_type="cycling",
                activity_name=f"Evening Ride {i+1}",
                start_time=activity_date.replace(hour=18, minute=0),
                duration=5400 + (i * 600),  # 1.5-2.5 hours
                distance=25000 + (i * 5000),  # 25-40 km in meters
                calories=800 + (i * 100),
                avg_heart_rate=140 + i,
                processed_metrics={
                    "steps": 200 + (i * 50),  # Cycling has fewer steps
                    "active_calories": 800 + (i * 100)
                }
            ))
        
        # Mike's activities (walker)
        for i in range(7):
            activity_date = week_start + timedelta(days=i)
            activities.append(Activity(
                user_id=users[2].id,
                garmin_activity_id=f"mike_walk_{i}",
                activity_type="walking",
                activity_name=f"Daily Walk {i+1}",
                start_time=activity_date.replace(hour=19, minute=0),
                duration=1800 + (i * 300),  # 30-65 minutes
                distance=3000 + (i * 500),  # 3-6 km in meters
                calories=200 + (i * 30),
                processed_metrics={
                    "steps": 5000 + (i * 800),
                    "active_calories": 200 + (i * 30)
                }
            ))
        
        # Emma's activities (swimmer + runner)
        for i in range(3):
            activity_date = week_start + timedelta(days=i * 2)
            # Swimming
            activities.append(Activity(
                user_id=users[3].id,
                garmin_activity_id=f"emma_swim_{i}",
                activity_type="swimming",
                activity_name=f"Pool Session {i+1}",
                start_time=activity_date.replace(hour=6, minute=0),
                duration=2700 + (i * 300),  # 45-60 minutes
                distance=1500 + (i * 300),  # 1.5-2.4 km in meters
                calories=400 + (i * 50),
                processed_metrics={
                    "steps": 0,  # Swimming doesn't count steps
                    "active_calories": 400 + (i * 50)
                }
            ))
            # Running
            activities.append(Activity(
                user_id=users[3].id,
                garmin_activity_id=f"emma_run_{i}",
                activity_type="running",
                activity_name=f"Recovery Run {i+1}",
                start_time=(activity_date + timedelta(days=1)).replace(hour=7, minute=30),
                duration=2400 + (i * 300),  # 40-55 minutes
                distance=5000 + (i * 1000),  # 5-8 km in meters
                calories=350 + (i * 40),
                processed_metrics={
                    "steps": 6500 + (i * 1200),
                    "active_calories": 350 + (i * 40)
                }
            ))
        
        # Alex's activities (hiker - weekend warrior)
        weekend_activities = [
            Activity(
                user_id=users[4].id,
                garmin_activity_id="alex_hike_1",
                activity_type="hiking",
                activity_name="Mountain Trail",
                start_time=(week_start + timedelta(days=5)).replace(hour=8, minute=0),
                duration=14400,  # 4 hours
                distance=15000,  # 15 km
                calories=1200,
                elevation_gain=800,
                processed_metrics={
                    "steps": 18000,
                    "active_calories": 1200
                }
            ),
            Activity(
                user_id=users[4].id,
                garmin_activity_id="alex_hike_2",
                activity_type="hiking",
                activity_name="Forest Loop",
                start_time=(week_start + timedelta(days=6)).replace(hour=9, minute=0),
                duration=10800,  # 3 hours
                distance=12000,  # 12 km
                calories=900,
                elevation_gain=500,
                processed_metrics={
                    "steps": 14500,
                    "active_calories": 900
                }
            )
        ]
        activities.extend(weekend_activities)
        
        # Add activities to database
        for activity in activities:
            db.add(activity)
        
        db.commit()
        
        print(f"✅ Created {len(users)} test users and {len(activities)} activities")
        print("Users created:")
        for user in users:
            user_activities = [a for a in activities if a.user_id == user.id]
            print(f"  - {user.full_name}: {len(user_activities)} activities")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Setting up test dashboard...")
    create_test_data()
    print("✅ Test data ready!")
    print("\nTo start the server:")
    print("  python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    print("\nThen visit:")
    print("  Dashboard: http://localhost:8000/fake-sporters")
    print("  API docs: http://localhost:8000/docs")
    print("  Weekly data: http://localhost:8000/api/v1/dashboard/weekly")
    print("  WhatsApp digest: http://localhost:8000/api/v1/whatsapp/weekly")