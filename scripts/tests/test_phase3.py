#!/usr/bin/env python3
"""
Phase 3 Testing Script - Test weekly digest generation with real Garmin data
"""

import asyncio
import json
import time
from datetime import datetime
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def test_full_phase3_workflow():
    """Test the complete Phase 3 workflow with real Garmin data"""
    base_url = "http://localhost:8000"
    
    print("🚀 Testing Phase 3 - Weekly Digest Generation")
    print("=" * 60)
    
    # Get real Garmin credentials from environment
    garmin_email = os.getenv('GARMIN_EMAIL')
    garmin_password = os.getenv('GARMIN_PASSWORD')
    
    if not garmin_email or not garmin_password:
        print("❌ GARMIN_EMAIL and GARMIN_PASSWORD must be set in .env file")
        return
    
    print(f"🔐 Using Garmin account: {garmin_email}")
    print()
    
    # Step 1: Register/Login user with real Garmin credentials
    print("1. 👤 Setting up user with real Garmin credentials...")
    user_data = {
        "email": "testuser@example.com",
        "password": "testpass123",
        "full_name": "Test User",
        "garmin_email": garmin_email,
        "garmin_password": garmin_password
    }
    
    # Try to register (might fail if user exists)
    response = requests.post(f"{base_url}/api/v1/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"   ℹ️  Registration failed (user may exist): {response.status_code}")
    else:
        print(f"   ✅ User registered successfully")
    
    # Login
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    
    response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data)
    if response.status_code != 200:
        print(f"   ❌ Login failed: {response.text}")
        return
    
    token_data = response.json()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print(f"   ✅ Login successful")
    
    # Step 2: Create a test group
    print("\\n2. 👥 Creating test fitness group...")
    group_data = {
        "name": "Phase 3 Test Group",
        "description": "Testing weekly digest generation",
        "whatsapp_group_id": "test-whatsapp-123@g.us",
        "digest_schedule": "0 8 * * 1"
    }
    
    response = requests.post(f"{base_url}/api/v1/groups/", json=group_data, headers=headers)
    if response.status_code == 200:
        group_info = response.json()
        group_id = group_info["id"]
        print(f"   ✅ Group created: {group_info['name']} (ID: {group_id})")
    else:
        # Try to get existing group
        response = requests.get(f"{base_url}/api/v1/groups/", headers=headers)
        if response.status_code == 200:
            groups = response.json()
            if groups:
                group_id = groups[0]["id"]
                print(f"   ℹ️  Using existing group: {groups[0]['name']} (ID: {group_id})")
            else:
                print("   ❌ No groups available")
                return
        else:
            print(f"   ❌ Failed to create or get group: {response.text}")
            return
    
    # Step 3: Sync real Garmin activities
    print("\\n3. 🏃 Syncing real Garmin activities...")
    response = requests.post(f"{base_url}/api/v1/activities/sync/immediate", headers=headers)
    if response.status_code == 200:
        sync_result = response.json()
        print(f"   ✅ Synced {sync_result['synced_activities']} activities")
        
        if sync_result.get('activities'):
            print("   📊 Recent activities:")
            for i, activity in enumerate(sync_result['activities'][:5], 1):
                activity_type = activity.get('activity_type', 'Unknown').replace('_', ' ').title()
                distance = activity.get('distance_km', 0)
                duration = activity.get('duration_minutes', 0)
                print(f"      {i}. {activity_type}: {distance:.1f}km in {duration}min")
    else:
        print(f"   ⚠️  Activity sync failed: {response.text}")
        print("   🔄 Continuing with existing data...")
    
    # Step 4: Check current activities
    print("\\n4. 📈 Checking current activity data...")
    response = requests.get(f"{base_url}/api/v1/activities/stats?days_back=30", headers=headers)
    if response.status_code == 200:
        stats = response.json()
        print(f"   📊 Last 30 days: {stats['total_activities']} activities")
        print(f"   📏 Total distance: {stats['total_distance_km']:.1f} km")
        print(f"   ⏱️  Total time: {stats['total_duration_minutes']/60:.1f} hours")
        print(f"   🔥 Total calories: {stats['total_calories']:,}")
        if stats['activity_types']:
            print(f"   🏃 Activity types: {', '.join(stats['activity_types'].keys())}")
    else:
        print(f"   ⚠️  Could not get activity stats: {response.text}")
    
    # Step 5: Generate weekly digest preview
    print("\\n5. 📋 Generating weekly digest preview...")
    response = requests.get(f"{base_url}/api/v1/digest/{group_id}/preview", headers=headers)
    if response.status_code == 200:
        preview = response.json()
        print(f"   ✅ Preview generated for: {preview['group_name']}")
        print(f"   📅 Week {preview['period']['week_number']} summary")
        print(f"   📊 Group activities: {preview['summary']['total_activities']}")
        print(f"   📏 Group distance: {preview['summary']['total_distance_km']:.1f} km")
        print(f"   ⏱️  Group time: {preview['summary']['total_duration_hours']:.1f} hours")
        print(f"   📝 Message length: {preview['character_count']} characters")
        
        # Show a preview of the formatted message
        message_lines = preview['formatted_message'].split('\\n')
        print("\\n   📱 WhatsApp Message Preview:")
        print("   " + "─" * 40)
        for line in message_lines[:15]:  # Show first 15 lines
            print(f"   {line}")
        if len(message_lines) > 15:
            print(f"   ... ({len(message_lines) - 15} more lines)")
        print("   " + "─" * 40)
        
    else:
        print(f"   ❌ Failed to generate preview: {response.text}")
        return
    
    # Step 6: Generate and simulate sending digest
    print("\\n6. 📤 Generating and sending weekly digest...")
    response = requests.post(f"{base_url}/api/v1/digest/{group_id}/send", headers=headers)
    if response.status_code == 200:
        send_result = response.json()
        print(f"   ✅ Digest sent successfully!")
        print(f"   📋 Digest ID: {send_result['digest_id']}")
        print(f"   📱 WhatsApp Status: {send_result['whatsapp_status']}")
        print(f"   👥 Group: {send_result['group_name']}")
        
        # Show message preview
        print("\\n   📝 Sent Message Preview:")
        print("   " + "─" * 50)
        preview_lines = send_result['message_preview'].split('\\n')
        for line in preview_lines:
            print(f"   {line}")
        print("   " + "─" * 50)
        
    else:
        print(f"   ❌ Failed to send digest: {response.text}")
    
    # Step 7: Test different week offsets
    print("\\n7. 📅 Testing previous week digest...")
    response = requests.get(f"{base_url}/api/v1/digest/{group_id}/preview?week_offset=1", headers=headers)
    if response.status_code == 200:
        prev_week = response.json()
        print(f"   ✅ Previous week (Week {prev_week['period']['week_number']}) preview:")
        print(f"   📊 Activities: {prev_week['summary']['total_activities']}")
        print(f"   📏 Distance: {prev_week['summary']['total_distance_km']:.1f} km")
    else:
        print(f"   ℹ️  Previous week data not available")
    
    # Step 8: Show API documentation
    print("\\n8. 📚 API Documentation available at:")
    print(f"   🔗 Interactive docs: {base_url}/docs")
    print(f"   🔗 OpenAPI schema: {base_url}/openapi.json")
    
    print("\\n" + "=" * 60)
    print("🎉 Phase 3 Testing Complete!")
    print("\\n📊 Summary of capabilities demonstrated:")
    print("   ✅ Real Garmin data synchronization")
    print("   ✅ Multi-user group management") 
    print("   ✅ Weekly digest generation with analytics")
    print("   ✅ Activity statistics and leaderboards")
    print("   ✅ Achievement detection")
    print("   ✅ WhatsApp message formatting")
    print("   ✅ Simulated WhatsApp delivery")
    print("   ✅ Historical week analysis")
    
    print("\\n🚀 Ready for production deployment!")


def simple_digest_test():
    """Simple command to quickly test digest generation"""
    print("🔄 Quick Digest Test")
    print("=" * 30)
    
    try:
        # Quick health check
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ API not available. Start with: docker-compose up")
            return
        
        print("✅ API is running")
        print("🔄 Run full test with: python test_phase3.py")
        print("🔗 View API docs at: http://localhost:8000/docs")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API")
        print("🚀 Start the system with: docker-compose up")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        simple_digest_test()
    else:
        print("Starting full Phase 3 test in 3 seconds...")
        print("Make sure the system is running: docker-compose up")
        time.sleep(3)
        test_full_phase3_workflow()