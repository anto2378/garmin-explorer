#!/usr/bin/env python3
"""
Phase 2 Testing Script - Test the complete system functionality
"""

import asyncio
import json
import time
from datetime import datetime

import requests
import uvicorn
from sqlalchemy.orm import sessionmaker

from app.core.database import engine
from app.models.user import User
from app.models.group import Group, GroupMembership
from app.services.garmin_service import GarminService


def test_api_endpoints():
    """Test API endpoints"""
    base_url = "http://localhost:8000"
    
    print("🚀 Testing Phase 2 Implementation")
    print("=" * 50)
    
    # Test health check
    print("\n1. Testing Health Check...")
    response = requests.get(f"{base_url}/health")
    print(f"Health Check: {response.status_code} - {response.json()}")
    
    # Test user registration
    print("\n2. Testing User Registration...")
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "garmin_email": "your-garmin-email@example.com",
        "garmin_password": "your-garmin-password"
    }
    
    response = requests.post(f"{base_url}/api/v1/auth/register", json=user_data)
    print(f"User Registration: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ User registered successfully")
    else:
        print(f"❌ Registration failed: {response.text}")
    
    # Test login
    print("\n3. Testing User Login...")
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    
    response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data)
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        print("✅ Login successful")
        
        # Test group creation
        print("\n4. Testing Group Creation...")
        group_data = {
            "name": "Test Fitness Group",
            "description": "A test group for Phase 2 testing",
            "whatsapp_group_id": "test-whatsapp-group-123",
            "digest_schedule": "0 8 * * 1"
        }
        
        response = requests.post(f"{base_url}/api/v1/groups/", json=group_data, headers=headers)
        print(f"Group Creation: {response.status_code}")
        if response.status_code == 200:
            group_info = response.json()
            print(f"✅ Group created: {group_info['name']} (ID: {group_info['id']})")
            
            # Test listing groups
            print("\n5. Testing Group Listing...")
            response = requests.get(f"{base_url}/api/v1/groups/", headers=headers)
            if response.status_code == 200:
                groups = response.json()
                print(f"✅ Found {len(groups)} group(s)")
                for group in groups:
                    print(f"   - {group['name']} ({group['member_count']} members)")
            
            # Test group members
            print("\n6. Testing Group Members...")
            group_id = group_info['id']
            response = requests.get(f"{base_url}/api/v1/groups/{group_id}/members", headers=headers)
            if response.status_code == 200:
                members = response.json()
                print(f"✅ Group has {len(members)} member(s)")
                for member in members:
                    print(f"   - {member['full_name']} ({member['role']})")
        
        # Test activity sync (immediate)
        print("\n7. Testing Immediate Activity Sync...")
        response = requests.post(f"{base_url}/api/v1/activities/sync/immediate", headers=headers)
        print(f"Activity Sync: {response.status_code}")
        if response.status_code == 200:
            sync_result = response.json()
            print(f"✅ Synced {sync_result['synced_activities']} activities")
            for activity in sync_result.get('activities', []):
                print(f"   - {activity['activity_type']}: {activity['activity_name']}")
        else:
            print(f"⚠️  Activity sync failed (possibly no Garmin credentials): {response.text}")
        
        # Test activity listing
        print("\n8. Testing Activity Listing...")
        response = requests.get(f"{base_url}/api/v1/activities/", headers=headers)
        if response.status_code == 200:
            activities = response.json()
            print(f"✅ Found {len(activities)} activities")
            for activity in activities[:3]:  # Show first 3
                print(f"   - {activity['activity_type']}: {activity.get('distance_km', 0):.2f}km, {activity.get('duration_minutes', 0)}min")
        
        # Test activity stats
        print("\n9. Testing Activity Statistics...")
        response = requests.get(f"{base_url}/api/v1/activities/stats", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Activity Stats:")
            print(f"   - Total Activities: {stats['total_activities']}")
            print(f"   - Total Distance: {stats['total_distance_km']:.2f} km")
            print(f"   - Total Duration: {stats['total_duration_minutes']} minutes")
            print(f"   - Activity Types: {list(stats['activity_types'].keys())}")
    
    else:
        print(f"❌ Login failed: {response.text}")
    
    print("\n" + "=" * 50)
    print("📊 Phase 2 Testing Complete!")


def test_database_models():
    """Test database models and relationships"""
    print("\n🗄️  Testing Database Models...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Test user count
        user_count = db.query(User).count()
        print(f"✅ Users in database: {user_count}")
        
        # Test group count
        group_count = db.query(Group).count()
        print(f"✅ Groups in database: {group_count}")
        
        # Test group memberships
        membership_count = db.query(GroupMembership).count()
        print(f"✅ Group memberships: {membership_count}")
        
        # Show sample user data
        users = db.query(User).limit(3).all()
        for user in users:
            print(f"   - User: {user.email} (Active: {user.is_active}, Last sync: {user.last_sync_at})")
        
    finally:
        db.close()


def run_development_server():
    """Start the development server"""
    print("🚀 Starting Garmin Companion System...")
    print("Access the API at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Use Ctrl+C to stop the server")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        run_development_server()
    else:
        # Wait a moment for server to be ready if it's running
        time.sleep(2)
        
        try:
            test_api_endpoints()
            test_database_models()
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the API server.")
            print("   Start the server first with: python test_phase2.py server")
            print("   Or use Docker: docker-compose up")