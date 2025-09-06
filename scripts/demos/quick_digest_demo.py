#!/usr/bin/env python3
"""
Quick Digest Demo - Using existing demo data to show Phase 3 functionality
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker

from app.core.database import engine
from app.models.user import User
from app.models.group import Group, GroupMembership, UserRole
from app.models.activity import Activity
from app.services.digest_service import DigestService
from app.services.whatsapp_service import WhatsAppService


def demo_digest_generation():
    """Demo digest generation with existing data"""
    print("🚀 Phase 3 Weekly Digest Demo")
    print("=" * 50)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Use existing demo user
        print("1. 👤 Using existing demo user...")
        demo_user = db.query(User).filter(User.email == "demo@example.com").first()
        if not demo_user:
            print("   ❌ Demo user not found. Run demo_activity.py first!")
            return
        print(f"   ✅ Found user: {demo_user.full_name}")
        
        # Create test group
        print("\\n2. 👥 Creating test group...")
        test_group = Group(
            name="Demo Fitness Group", 
            description="Phase 3 digest demo",
            whatsapp_group_id="demo-group@g.us",
            admin_user_id=demo_user.id
        )
        db.add(test_group)
        db.commit()
        db.refresh(test_group)
        
        # Add membership
        membership = GroupMembership(
            group_id=test_group.id,
            user_id=demo_user.id,
            role=UserRole.ADMIN
        )
        db.add(membership)
        db.commit()
        print("   ✅ Created group and membership")
        
        # Check activities
        print("\\n3. 📊 Checking activity data...")
        activities = db.query(Activity).filter(Activity.user_id == demo_user.id).all()
        print(f"   📈 Found {len(activities)} activities")
        
        if activities:
            total_distance = sum(a.distance_km for a in activities if a.distance_km)
            total_duration = sum(a.duration_minutes for a in activities if a.duration_minutes) 
            total_calories = sum(a.calories for a in activities if a.calories)
            
            print(f"   📏 Total distance: {total_distance:.1f} km")
            print(f"   ⏱️  Total time: {total_duration/60:.1f} hours") 
            print(f"   🔥 Total calories: {total_calories:,}")
            
            # Show recent activities
            print("   🏃 Recent activities:")
            for i, activity in enumerate(activities[:3], 1):
                activity_type = activity.activity_type.replace('_', ' ').title()
                distance = f"{activity.distance_km:.1f}km" if activity.distance_km else "No distance"
                duration = f"{activity.duration_minutes}min" if activity.duration_minutes else "No time"
                print(f"      {i}. {activity_type}: {distance}, {duration}")
        
        # Generate digest
        print("\\n4. 📋 Generating weekly digest...")
        digest_service = DigestService(db)
        
        # Use a week that includes our demo activities
        week_start = datetime(2024, 1, 15)  # Monday of the week with demo activities
        digest_data = digest_service.generate_weekly_digest(str(test_group.id), week_start)
        
        print("   ✅ Digest generated successfully!")
        print(f"   👥 Group: {digest_data['group']['name']}")
        print(f"   📅 Week {digest_data['period']['week_number']}")
        print(f"   📊 Activities: {digest_data['summary']['total_activities']}")
        print(f"   📏 Distance: {digest_data['summary']['total_distance_km']} km")
        print(f"   ⏱️  Time: {digest_data['summary']['total_duration_hours']} hours")
        print(f"   🔥 Calories: {digest_data['summary']['total_calories']:,}")
        
        if digest_data['summary']['most_popular_activity'] != "None":
            print(f"   🏆 Most popular: {digest_data['summary']['most_popular_activity']}")
        
        # Show achievements
        if digest_data['achievements']:
            print("\\n   🎉 Achievements found:")
            for achievement in digest_data['achievements']:
                print(f"      {achievement['badge']} {achievement['description']}")
        
        # Format WhatsApp message
        print("\\n5. 📱 Formatting WhatsApp message...")
        formatted_message = digest_service.format_digest_message(digest_data)
        
        print(f"   ✅ Message formatted ({len(formatted_message)} characters)")
        print("\\n   📱 WhatsApp Weekly Digest:")
        print("   " + "=" * 60)
        lines = formatted_message.split('\\n')
        for line in lines:
            print(f"   {line}")
        print("   " + "=" * 60)
        
        # Simulate WhatsApp send
        print("\\n6. 📤 Simulating WhatsApp delivery...")
        whatsapp_service = WhatsAppService()
        send_result = whatsapp_service.send_digest(test_group.whatsapp_group_id, formatted_message)
        
        print(f"   ✅ WhatsApp Status: {send_result['status']}")
        print(f"   📋 Message ID: {send_result.get('message_id', 'N/A')}")
        print(f"   📏 Length: {send_result.get('message_length', len(formatted_message))} chars")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()
    
    print("\\n" + "=" * 50)
    print("🎉 Phase 3 Demo Complete!")
    print("\\n✅ Features Demonstrated:")
    print("   • Weekly digest generation")
    print("   • Activity analysis & statistics")
    print("   • Leaderboard calculations")
    print("   • Achievement detection") 
    print("   • WhatsApp message formatting")
    print("   • Simulated message delivery")
    
    print("\\n🚀 Ready for real Garmin data and WhatsApp!")


if __name__ == "__main__":
    demo_digest_generation()