#!/usr/bin/env python3
"""
System Setup Command - Initialize users and groups from .env configuration
"""

import asyncio
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from app.core.database import engine, Base
from app.services.simple_auth_service import auth_service
from app.services.garmin_service import GarminService

# Load environment variables
load_dotenv()


async def setup_system():
    """Setup the complete system with users and groups"""
    print("🚀 Setting up Garmin Companion System")
    print("=" * 50)
    
    # Create database session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Ensure database tables exist
        print("1. 🗄️  Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("   ✅ Database tables ready")
        
        # Setup users from .env
        print("\\n2. 👥 Setting up users from .env configuration...")
        user_ids = auth_service.setup_database_users(db)
        
        if not user_ids:
            print("   ❌ No users configured in .env")
            print("   💡 Add USER1_EMAIL, USER1_PASSWORD, etc. to .env")
            return
        
        print(f"   ✅ Setup {len(user_ids)} users")
        
        # Setup default group
        print("\\n3. 👥 Setting up default group...")
        group_id = auth_service.setup_default_group(db, user_ids)
        
        if group_id:
            print(f"   ✅ Default group created: {group_id}")
        
        # Show configured users
        print("\\n4. 📋 Configured Users:")
        print("   " + "-" * 40)
        for user_creds in auth_service.get_all_users():
            print(f"   📧 {user_creds.email}")
            print(f"      Name: {user_creds.name}")
            print(f"      Role: {user_creds.role}")
            print(f"      Garmin: {user_creds.garmin_email}")
            print()
        
        # Test Garmin sync for first user (optional)
        print("5. 🏃 Testing Garmin sync (optional)...")
        first_user_email = list(user_ids.keys())[0]
        from app.models.user import User
        test_user = db.query(User).filter(User.email == first_user_email).first()
        
        if test_user:
            try:
                garmin_service = GarminService(db)
                activities = await garmin_service.sync_user_activities(test_user, days_back=7)
                print(f"   ✅ Synced {len(activities)} activities for {test_user.full_name}")
                
                if activities:
                    print("   📊 Recent activities:")
                    for activity in activities[:3]:
                        activity_type = activity.activity_type.replace('_', ' ').title()
                        distance = f"{activity.distance_km:.1f}km" if activity.distance_km else "No distance"
                        duration = f"{activity.duration_minutes}min" if activity.duration_minutes else "No time"
                        print(f"      • {activity_type}: {distance}, {duration}")
            except Exception as e:
                print(f"   ⚠️  Garmin sync test failed: {e}")
                print("   💡 Check Garmin credentials in .env")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()
    
    print("\\n" + "=" * 50)
    print("🎉 System Setup Complete!")
    
    print("\\n🌐 System Ready:")
    print("   📱 Web Interface: http://localhost:8000")
    print("   📚 API Documentation: http://localhost:8000/docs")
    print("   🔐 Simple Auth: POST /api/v1/simple-auth/login")
    
    print("\\n🔑 Login Credentials:")
    for user_creds in auth_service.get_all_users():
        print(f"   📧 {user_creds.email} / {user_creds.password}")
    
    print("\\n🚀 Ready for weekly digest generation!")


if __name__ == "__main__":
    asyncio.run(setup_system())