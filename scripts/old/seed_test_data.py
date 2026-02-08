#!/usr/bin/env python3
"""
Seed script to create test users and activities for development
"""

import sys
import os
from datetime import datetime, timedelta
import uuid
import json
import random

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.models.activity import Activity
from app.models import Base

def create_test_users(db: Session):
    """Create test users matching the mockup"""
    
    test_users = [
        {
            "email": "alice@example.com",
            "full_name": "Alice",
            "garmin_email": "alice.test@example.com",
            "garmin_password": "encrypted_password_1"
        },
        {
            "email": "bob@example.com", 
            "full_name": "Bob",
            "garmin_email": "bob.test@example.com",
            "garmin_password": "encrypted_password_2"
        },
        {
            "email": "charlie@example.com",
            "full_name": "Charlie", 
            "garmin_email": "charlie.test@example.com",
            "garmin_password": "encrypted_password_3"
        },
        {
            "email": "diana@example.com",
            "full_name": "Diana",
            "garmin_email": "diana.test@example.com", 
            "garmin_password": "encrypted_password_4"
        }
    ]
    
    created_users = []
    
    for user_data in test_users:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            print(f"User {user_data['email']} already exists")
            created_users.append(existing_user)
            continue
            
        user = User(
            id=uuid.uuid4(),
            email=user_data["email"],
            full_name=user_data["full_name"],
            garmin_email=user_data["garmin_email"],
            garmin_password=user_data["garmin_password"],
            is_active=True,
            preferences={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(user)
        created_users.append(user)
        print(f"Created user: {user.full_name}")
    
    db.commit()
    return created_users

def create_test_activities(db: Session, users: list):
    """Create test activities for the past month"""
    
    # Activity types and their typical metrics
    activity_types = {
        "running": {"avg_speed": 12, "calories_per_km": 80, "steps_per_km": 1300},
        "cycling": {"avg_speed": 25, "calories_per_km": 40, "steps_per_km": 0},
        "walking": {"avg_speed": 5, "calories_per_km": 60, "steps_per_km": 1500},
        "swimming": {"avg_speed": 3, "calories_per_km": 100, "steps_per_km": 0},
        "strength_training": {"avg_speed": 0, "calories_per_minute": 8, "steps_per_session": 500}
    }
    
    # Generate activities for the past 4 weeks
    end_date = datetime.now()
    start_date = end_date - timedelta(days=28)
    
    for user in users:
        user_activities = []
        
        # Alice - Most active
        if user.full_name == "Alice":
            activity_count = random.randint(20, 25)
            preferred_activities = ["running", "cycling", "strength_training"]
        # Bob - Moderate activity
        elif user.full_name == "Bob":
            activity_count = random.randint(15, 20)
            preferred_activities = ["running", "walking", "cycling"]
        # Charlie - Lower activity
        elif user.full_name == "Charlie":
            activity_count = random.randint(10, 15)
            preferred_activities = ["walking", "running", "swimming"]
        # Diana - Varied activities
        else:  # Diana
            activity_count = random.randint(12, 18)
            preferred_activities = ["strength_training", "walking", "cycling"]
        
        # Create activities
        for _ in range(activity_count):
            # Random date in the past 4 weeks
            days_ago = random.randint(0, 27)
            activity_date = end_date - timedelta(days=days_ago)
            
            # Random time of day
            hour = random.choice([6, 7, 8, 17, 18, 19])  # Morning or evening
            activity_date = activity_date.replace(
                hour=hour, 
                minute=random.randint(0, 59),
                second=0,
                microsecond=0
            )
            
            # Choose activity type
            activity_type = random.choice(preferred_activities)
            
            # Generate realistic metrics
            if activity_type == "strength_training":
                duration_minutes = random.randint(30, 90)
                distance_km = 0
                calories = duration_minutes * activity_types[activity_type]["calories_per_minute"]
                steps = activity_types[activity_type]["steps_per_session"]
            else:
                distance_km = round(random.uniform(2, 15), 2)
                speed = activity_types[activity_type]["avg_speed"]
                duration_minutes = int((distance_km / speed) * 60)
                calories = int(distance_km * activity_types[activity_type]["calories_per_km"])
                steps = int(distance_km * activity_types[activity_type]["steps_per_km"])
            
            # Add some randomness
            calories = int(calories * random.uniform(0.8, 1.2))
            if steps > 0:
                steps = int(steps * random.uniform(0.9, 1.1))
            
            activity = Activity(
                id=uuid.uuid4(),
                user_id=user.id,
                garmin_activity_id=f"test_activity_{uuid.uuid4().hex[:8]}",
                activity_type=activity_type,
                activity_name=f"{activity_type.replace('_', ' ').title()} Workout",
                start_time=activity_date,
                duration=duration_minutes * 60,  # Convert to seconds
                distance=distance_km * 1000 if distance_km > 0 else None,  # Convert to meters
                calories=calories,
                avg_heart_rate=random.randint(120, 170) if activity_type != "walking" else random.randint(90, 130),
                max_heart_rate=random.randint(150, 190) if activity_type != "walking" else random.randint(110, 150),
                elevation_gain=random.uniform(0, 200) if activity_type in ["running", "cycling"] else 0,
                raw_data={
                    "steps": steps,
                    "activeCalories": calories,
                    "totalCalories": int(calories * 1.2),
                    "averageSpeed": speed if activity_type != "strength_training" else 0,
                    "maxSpeed": speed * 1.3 if activity_type != "strength_training" else 0
                },
                processed_metrics={
                    "steps": steps,
                    "active_calories": calories,
                    "pace_minutes_per_km": (duration_minutes / distance_km) if distance_km > 0 else 0
                },
                created_at=datetime.utcnow()
            )
            
            user_activities.append(activity)
        
        db.add_all(user_activities)
        print(f"Created {len(user_activities)} activities for {user.full_name}")
    
    db.commit()

def main():
    """Main function to seed the database"""
    print("🌱 Seeding database with test data...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = SessionLocal()
    
    try:
        # Create test users
        print("\n👥 Creating test users...")
        users = create_test_users(db)
        
        # Create test activities
        print("\n🏃‍♂️ Creating test activities...")
        create_test_activities(db, users)
        
        print("\n✅ Database seeding completed successfully!")
        
        # Print summary
        total_users = db.query(User).count()
        total_activities = db.query(Activity).count()
        
        print(f"\n📊 Summary:")
        print(f"  - Total users: {total_users}")
        print(f"  - Total activities: {total_activities}")
        
        # Show user stats
        print(f"\n👤 User Statistics:")
        for user in users:
            user_activity_count = db.query(Activity).filter(Activity.user_id == user.id).count()
            total_distance = db.query(Activity).filter(Activity.user_id == user.id).filter(Activity.distance.isnot(None)).all()
            total_km = sum(a.distance_km for a in total_distance)
            print(f"  - {user.full_name}: {user_activity_count} activities, {total_km:.1f}km total")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()