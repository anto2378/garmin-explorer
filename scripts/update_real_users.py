#!/usr/bin/env python3
"""
Update database with real user names and sync Garmin data
"""

import sys
import os
from datetime import datetime
import uuid

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User

def update_users(db: Session):
    """Update existing users with real names and credentials"""
    
    # Get existing users in order
    users = db.query(User).order_by(User.created_at).all()
    
    if len(users) >= 3:
        # Update first user to Anto
        users[0].full_name = "Anto"
        users[0].email = "anto@example.com"
        users[0].garmin_email = "antosidoti@gmail.com"
        users[0].garmin_password = "21031993Garmin"
        users[0].updated_at = datetime.utcnow()
        print(f"Updated user 1: {users[0].full_name}")
        
        # Update second user to Jeff  
        users[1].full_name = "Jeff"
        users[1].email = "jeff@example.com"
        users[1].garmin_email = "geoffroy.lepivan@gmail.com"
        users[1].garmin_password = "hawxoggikkuR9zawje"
        users[1].updated_at = datetime.utcnow()
        print(f"Updated user 2: {users[1].full_name}")
        
        # Update third user to Arnaud
        users[2].full_name = "Arnaud"
        users[2].email = "arnaud@example.com"
        users[2].garmin_email = "arnaud.garmin@example.com"
        users[2].garmin_password = "arnaud_password"
        users[2].updated_at = datetime.utcnow()
        print(f"Updated user 3: {users[2].full_name}")
        
        # Remove 4th user (Diana) since we only need 3
        if len(users) >= 4:
            # Delete activities first
            from app.models.activity import Activity
            db.query(Activity).filter(Activity.user_id == users[3].id).delete()
            db.delete(users[3])
            print("Removed Diana (4th user)")
    
    db.commit()
    return users[:3]

def sync_real_garmin_data(db: Session, users: list):
    """Sync real data from Garmin for Anto and Jeff"""
    
    print("\n🔄 Attempting to sync real Garmin data...")
    
    try:
        from app.services.garmin_service import GarminService
        garmin_service = GarminService(db)
        
        for user in users[:2]:  # Only sync for Anto and Jeff
            if user.full_name in ["Anto", "Jeff"]:
                print(f"\n📡 Syncing data for {user.full_name}...")
                try:
                    # This will attempt to connect to Garmin and sync activities
                    activities = garmin_service.sync_user_activities(user)
                    print(f"✅ Synced {len(activities) if activities else 0} activities for {user.full_name}")
                except Exception as e:
                    print(f"⚠️  Could not sync {user.full_name}: {str(e)}")
                    print("   (This is expected if Garmin credentials are invalid or network issues)")
    
    except Exception as e:
        print(f"⚠️  Garmin service not available: {str(e)}")
        print("   Keeping existing test data for now")

def main():
    """Main function"""
    print("👥 Updating users to real names...")
    
    db = SessionLocal()
    
    try:
        # Update user names
        users = update_users(db)
        
        # Try to sync real Garmin data
        sync_real_garmin_data(db, users)
        
        print(f"\n✅ Successfully updated users!")
        
        # Show current users
        print(f"\n📊 Current users:")
        for i, user in enumerate(users, 1):
            from app.models.activity import Activity
            activity_count = db.query(Activity).filter(Activity.user_id == user.id).count()
            print(f"  {i}. {user.full_name} ({user.email}) - {activity_count} activities")
        
    except Exception as e:
        print(f"❌ Error updating users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()