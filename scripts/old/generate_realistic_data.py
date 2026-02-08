#!/usr/bin/env python3
"""
Generate realistic annual fitness data for serious athletes
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

def clear_existing_data(db: Session):
    """Clear existing activity data"""
    db.query(Activity).delete()
    db.commit()
    print("🧹 Cleared existing activity data")

def generate_annual_activities(db: Session):
    """Generate realistic annual data for serious athletes"""
    
    # Get users
    users = db.query(User).order_by(User.created_at).all()
    
    # Define realistic annual targets for each user
    user_profiles = {
        "Anto": {
            "annual_running_km": 800,  # Serious runner - ~15km/week
            "annual_cycling_km": 2500, # Cycling enthusiast 
            "weekly_activities": 5,     # Very active
            "strength_sessions": 80,    # 1.5x/week
            "preferred_activities": ["running", "cycling", "strength_training"]
        },
        "Jeff": {
            "annual_running_km": 1200,  # More serious runner - ~23km/week  
            "annual_cycling_km": 1800,
            "weekly_activities": 4,
            "strength_sessions": 60,
            "preferred_activities": ["running", "cycling", "walking"]
        },
        "Arnaud": {
            "annual_running_km": 600,   # Moderate runner - ~12km/week
            "annual_cycling_km": 3000,  # Serious cyclist
            "weekly_activities": 4,
            "strength_sessions": 50,
            "preferred_activities": ["cycling", "running", "swimming"]
        }
    }
    
    # Generate activities for the full year (Jan 1 - current date)
    current_date = datetime.now()
    start_date = datetime(current_date.year, 1, 1)
    total_weeks = ((current_date - start_date).days // 7) + 1
    
    print(f"📅 Generating {total_weeks} weeks of data for {current_date.year}")
    
    for user in users:
        if user.full_name not in user_profiles:
            continue
            
        profile = user_profiles[user.full_name]
        user_activities = []
        
        print(f"\n👤 Generating data for {user.full_name}")
        print(f"   Target: {profile['annual_running_km']}km running, {profile['annual_cycling_km']}km cycling")
        
        # Weekly distribution
        weekly_running = profile['annual_running_km'] / 52
        weekly_cycling = profile['annual_cycling_km'] / 52
        
        # Generate week by week
        for week in range(total_weeks):
            week_start = start_date + timedelta(weeks=week)
            
            # Skip future weeks
            if week_start > current_date:
                break
            
            activities_this_week = random.randint(
                max(1, profile['weekly_activities'] - 2),
                profile['weekly_activities'] + 2
            )
            
            # Distribute running and cycling across the week
            weekly_running_actual = weekly_running * random.uniform(0.7, 1.3)
            weekly_cycling_actual = weekly_cycling * random.uniform(0.8, 1.2)
            
            running_sessions = random.randint(1, 3) if weekly_running_actual > 5 else 1
            cycling_sessions = random.randint(1, 2) if weekly_cycling_actual > 20 else (1 if weekly_cycling_actual > 0 else 0)
            
            # Create running activities
            for session in range(running_sessions):
                distance_km = (weekly_running_actual / running_sessions) * random.uniform(0.8, 1.2)
                distance_km = max(3.0, min(25.0, distance_km))  # Realistic range
                
                # Random day and time
                day_offset = random.randint(0, 6)
                hour = random.choice([6, 7, 8, 17, 18, 19])
                activity_date = week_start + timedelta(days=day_offset, hours=hour, minutes=random.randint(0, 59))
                
                # Skip future dates
                if activity_date > current_date:
                    continue
                
                # Realistic running metrics
                pace_min_per_km = random.uniform(4.5, 6.5)  # 4:30-6:30 min/km
                duration_seconds = int(distance_km * pace_min_per_km * 60)
                speed_kmh = 60 / pace_min_per_km
                
                calories = int(distance_km * random.uniform(65, 85))  # 65-85 cal/km
                steps = int(distance_km * random.randint(1250, 1400))  # realistic steps/km
                
                activity = Activity(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    garmin_activity_id=f"run_{uuid.uuid4().hex[:8]}",
                    activity_type="running",
                    activity_name=f"Morning Run" if hour < 12 else f"Evening Run",
                    start_time=activity_date,
                    duration=duration_seconds,
                    distance=distance_km * 1000,  # meters
                    calories=calories,
                    avg_heart_rate=random.randint(140, 165),
                    max_heart_rate=random.randint(170, 190),
                    elevation_gain=random.uniform(10, 150),
                    raw_data={
                        "steps": steps,
                        "activeCalories": calories,
                        "totalCalories": int(calories * 1.15),
                        "averageSpeed": speed_kmh,
                        "maxSpeed": speed_kmh * 1.3,
                        "averagePace": pace_min_per_km
                    },
                    processed_metrics={
                        "steps": steps,
                        "active_calories": calories,
                        "pace_minutes_per_km": pace_min_per_km
                    },
                    created_at=datetime.utcnow()
                )
                user_activities.append(activity)
            
            # Create cycling activities
            for session in range(cycling_sessions):
                distance_km = (weekly_cycling_actual / max(1, cycling_sessions)) * random.uniform(0.9, 1.1)
                distance_km = max(10.0, min(80.0, distance_km))  # Realistic cycling range
                
                day_offset = random.randint(0, 6)
                hour = random.choice([7, 8, 9, 16, 17, 18])
                activity_date = week_start + timedelta(days=day_offset, hours=hour, minutes=random.randint(0, 59))
                
                if activity_date > current_date:
                    continue
                
                # Realistic cycling metrics
                speed_kmh = random.uniform(22, 32)  # 22-32 km/h
                duration_seconds = int((distance_km / speed_kmh) * 3600)
                
                calories = int(distance_km * random.uniform(35, 45))  # 35-45 cal/km cycling
                
                activity = Activity(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    garmin_activity_id=f"bike_{uuid.uuid4().hex[:8]}",
                    activity_type="cycling",
                    activity_name=f"Road Cycling",
                    start_time=activity_date,
                    duration=duration_seconds,
                    distance=distance_km * 1000,
                    calories=calories,
                    avg_heart_rate=random.randint(120, 150),
                    max_heart_rate=random.randint(160, 180),
                    elevation_gain=random.uniform(50, 300),
                    raw_data={
                        "steps": 0,  # No steps in cycling
                        "activeCalories": calories,
                        "totalCalories": int(calories * 1.1),
                        "averageSpeed": speed_kmh,
                        "maxSpeed": speed_kmh * 1.4
                    },
                    processed_metrics={
                        "steps": 0,
                        "active_calories": calories,
                        "average_speed_kmh": speed_kmh
                    },
                    created_at=datetime.utcnow()
                )
                user_activities.append(activity)
            
            # Add some strength training and other activities
            remaining_activities = max(0, activities_this_week - running_sessions - cycling_sessions)
            
            for _ in range(remaining_activities):
                activity_type = random.choice(["strength_training", "walking", "swimming"])
                
                day_offset = random.randint(0, 6)
                hour = random.choice([6, 7, 18, 19])
                activity_date = week_start + timedelta(days=day_offset, hours=hour, minutes=random.randint(0, 59))
                
                if activity_date > current_date:
                    continue
                
                if activity_type == "strength_training":
                    duration_seconds = random.randint(2400, 5400)  # 40-90 min
                    calories = int(duration_seconds / 60 * 8)  # ~8 cal/min
                    steps = random.randint(800, 1500)
                    distance_km = 0
                elif activity_type == "walking":
                    distance_km = random.uniform(3, 8)
                    speed_kmh = random.uniform(4.5, 6.5)
                    duration_seconds = int((distance_km / speed_kmh) * 3600)
                    calories = int(distance_km * 50)
                    steps = int(distance_km * 1500)
                else:  # swimming
                    distance_km = random.uniform(1, 3)
                    duration_seconds = random.randint(1800, 3600)  # 30-60 min
                    calories = int(distance_km * 400)  # High calorie burn
                    steps = 0
                
                activity = Activity(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    garmin_activity_id=f"{activity_type}_{uuid.uuid4().hex[:8]}",
                    activity_type=activity_type,
                    activity_name=activity_type.replace('_', ' ').title(),
                    start_time=activity_date,
                    duration=duration_seconds,
                    distance=distance_km * 1000 if distance_km > 0 else None,
                    calories=calories,
                    avg_heart_rate=random.randint(90, 140) if activity_type == "walking" else random.randint(130, 160),
                    max_heart_rate=random.randint(120, 160) if activity_type == "walking" else random.randint(150, 180),
                    elevation_gain=random.uniform(0, 100) if activity_type == "walking" else 0,
                    raw_data={
                        "steps": steps,
                        "activeCalories": calories,
                        "totalCalories": int(calories * 1.2)
                    },
                    processed_metrics={
                        "steps": steps,
                        "active_calories": calories
                    },
                    created_at=datetime.utcnow()
                )
                user_activities.append(activity)
        
        # Save all activities for this user
        db.add_all(user_activities)
        
        # Calculate totals
        total_running = sum(a.distance_km for a in user_activities if a.activity_type == "running" and a.distance)
        total_cycling = sum(a.distance_km for a in user_activities if a.activity_type == "cycling" and a.distance)
        total_activities = len(user_activities)
        
        print(f"   ✅ Generated: {total_activities} activities")
        print(f"   🏃 Running: {total_running:.0f}km")
        print(f"   🚴 Cycling: {total_cycling:.0f}km")
        
    db.commit()

def main():
    """Main function"""
    print("🏃‍♂️ Generating realistic annual fitness data...")
    
    db = SessionLocal()
    
    try:
        # Clear existing data
        clear_existing_data(db)
        
        # Generate realistic data
        generate_annual_activities(db)
        
        print("\n✅ Realistic data generation completed!")
        
        # Show summary
        total_users = db.query(User).count()
        total_activities = db.query(Activity).count()
        
        print(f"\n📊 Summary:")
        print(f"  - Users: {total_users}")
        print(f"  - Total activities: {total_activities}")
        
    except Exception as e:
        print(f"❌ Error generating data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()