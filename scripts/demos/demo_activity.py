#!/usr/bin/env python3
"""
Demo script to show activity data processing without requiring real Garmin credentials
"""

import json
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker

from app.core.database import engine
from app.models.user import User
from app.models.activity import Activity
from app.services.garmin_service import GarminService

# Sample Garmin activity data (realistic structure)
SAMPLE_ACTIVITIES = [
    {
        "activityId": 12345678901,
        "activityName": "Morning Run",
        "activityType": {"typeKey": "running"},
        "startTimeLocal": "2024-01-15T07:30:00.000",
        "duration": 2400,  # 40 minutes
        "distance": 8000,  # 8km in meters
        "calories": 480,
        "averageHR": 145,
        "maxHR": 165,
        "elevationGain": 120,
        "aerobicTrainingEffect": 3.2,
        "anaerobicTrainingEffect": 1.8
    },
    {
        "activityId": 12345678902,
        "activityName": "Cycling Adventure",
        "activityType": {"typeKey": "cycling"},
        "startTimeLocal": "2024-01-16T16:00:00.000",
        "duration": 5400,  # 90 minutes
        "distance": 35000,  # 35km in meters
        "calories": 850,
        "averageHR": 132,
        "maxHR": 178,
        "elevationGain": 450,
        "aerobicTrainingEffect": 4.1,
        "anaerobicTrainingEffect": 2.3
    },
    {
        "activityId": 12345678903,
        "activityName": "Strength Training",
        "activityType": {"typeKey": "strength_training"},
        "startTimeLocal": "2024-01-17T18:15:00.000",
        "duration": 3600,  # 60 minutes
        "distance": None,
        "calories": 320,
        "averageHR": 125,
        "maxHR": 155,
        "elevationGain": None,
        "aerobicTrainingEffect": 2.1,
        "anaerobicTrainingEffect": 3.5
    },
    {
        "activityId": 12345678904,
        "activityName": "Evening Walk",
        "activityType": {"typeKey": "walking"},
        "startTimeLocal": "2024-01-18T19:00:00.000",
        "duration": 1800,  # 30 minutes
        "distance": 2500,  # 2.5km in meters
        "calories": 180,
        "averageHR": 95,
        "maxHR": 110,
        "elevationGain": 15,
        "aerobicTrainingEffect": 1.8,
        "anaerobicTrainingEffect": 0.5
    }
]


def demo_activity_parsing():
    """Demonstrate activity data parsing and processing"""
    print("🏃 Garmin Activity Data Processing Demo")
    print("=" * 50)
    
    # Create a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create a demo user if not exists
        demo_user = db.query(User).filter(User.email == "demo@example.com").first()
        if not demo_user:
            demo_user = User(
                email="demo@example.com",
                full_name="Demo User",
                garmin_email="encrypted_dummy",
                garmin_password="encrypted_dummy",
                is_active=True
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            print("✅ Created demo user")
        
        # Initialize Garmin service
        garmin_service = GarminService(db)
        
        print(f"\n📊 Processing {len(SAMPLE_ACTIVITIES)} sample activities...")
        
        for i, garmin_data in enumerate(SAMPLE_ACTIVITIES, 1):
            print(f"\n{i}. Processing: {garmin_data['activityName']}")
            print("-" * 30)
            
            # Create activity from Garmin data
            activity = garmin_service._create_activity_from_garmin_data(demo_user, garmin_data)
            
            # Display processed activity
            print(f"   🏃 Activity Type: {activity.activity_type}")
            print(f"   📅 Start Time: {activity.start_time}")
            print(f"   ⏱️  Duration: {activity.duration_minutes} minutes")
            
            if activity.distance_km:
                print(f"   📏 Distance: {activity.distance_km:.2f} km")
            
            if activity.calories:
                print(f"   🔥 Calories: {activity.calories}")
            
            if activity.avg_heart_rate:
                print(f"   💓 Avg Heart Rate: {activity.avg_heart_rate} bpm")
            
            if activity.elevation_gain:
                print(f"   ⛰️  Elevation Gain: {activity.elevation_gain} m")
            
            # Show processed metrics
            if activity.processed_metrics:
                print(f"   📈 Processed Metrics:")
                for key, value in activity.processed_metrics.items():
                    if key == "pace_min_per_km":
                        minutes = int(value)
                        seconds = int((value - minutes) * 60)
                        print(f"      - Pace: {minutes}:{seconds:02d} min/km")
                    elif key == "avg_speed_kmh":
                        print(f"      - Avg Speed: {value:.1f} km/h")
                    else:
                        print(f"      - {key}: {value}")
            
            # Save to database (check for duplicates first)
            existing = db.query(Activity).filter(
                Activity.garmin_activity_id == activity.garmin_activity_id,
                Activity.user_id == demo_user.id
            ).first()
            
            if not existing:
                db.add(activity)
                print("   ✅ Saved to database")
            else:
                print("   ℹ️  Already exists in database")
        
        db.commit()
        
        # Show summary statistics
        print(f"\n📊 Activity Summary for {demo_user.full_name}")
        print("=" * 50)
        
        activities = db.query(Activity).filter(Activity.user_id == demo_user.id).all()
        
        if activities:
            total_activities = len(activities)
            total_distance = sum(a.distance_km for a in activities if a.distance_km)
            total_duration = sum(a.duration_minutes for a in activities if a.duration_minutes)
            total_calories = sum(a.calories for a in activities if a.calories)
            
            print(f"📈 Total Activities: {total_activities}")
            print(f"📏 Total Distance: {total_distance:.2f} km")
            print(f"⏱️  Total Duration: {total_duration} minutes ({total_duration/60:.1f} hours)")
            print(f"🔥 Total Calories: {total_calories}")
            
            # Activity type breakdown
            activity_types = {}
            for activity in activities:
                activity_type = activity.activity_type
                if activity_type not in activity_types:
                    activity_types[activity_type] = {"count": 0, "distance": 0, "duration": 0}
                activity_types[activity_type]["count"] += 1
                if activity.distance_km:
                    activity_types[activity_type]["distance"] += activity.distance_km
                if activity.duration_minutes:
                    activity_types[activity_type]["duration"] += activity.duration_minutes
            
            print(f"\n📊 Activity Types:")
            for activity_type, stats in activity_types.items():
                print(f"   🏃 {activity_type.title()}: {stats['count']} activities")
                if stats['distance']:
                    print(f"      - Distance: {stats['distance']:.2f} km")
                if stats['duration']:
                    print(f"      - Duration: {stats['duration']} minutes")
        else:
            print("No activities found in database")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()
    
    print("\n🎉 Demo completed successfully!")
    print("\nNext steps:")
    print("1. Run the full system: python test_phase2.py server")
    print("2. Test with Docker: docker-compose up")
    print("3. Add real Garmin credentials to test live data sync")


if __name__ == "__main__":
    demo_activity_parsing()