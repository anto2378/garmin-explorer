#!/usr/bin/env python3
"""
Simple Weekly Digest Test - Using existing demo data
"""

import requests
import json

def test_digest_with_demo_data():
    """Test digest generation with existing demo data"""
    base_url = "http://localhost:8000"
    
    print("🔄 Testing Weekly Digest Generation")
    print("=" * 50)
    
    # Check API health
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API not available")
            return
        print("✅ API is running")
    except:
        print("❌ Cannot connect to API. Run: docker-compose up")
        return
    
    # Create a test user for digest demo
    print("\n1. 👤 Setting up test user...")
    user_data = {
        "email": "digest-test@example.com",
        "password": "testpass123",
        "full_name": "Digest Test User",
        "garmin_email": "demo_encrypted",
        "garmin_password": "demo_encrypted"
    }
    
    # Try to register (ignore if exists)
    requests.post(f"{base_url}/api/v1/auth/register", json=user_data)
    
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
    print("   ✅ User authenticated")
    
    # Create test group
    print("\n2. 👥 Creating test group...")
    group_data = {
        "name": "Weekly Digest Demo Group",
        "description": "Testing weekly digest functionality",
        "whatsapp_group_id": "demo-group-123@g.us",
        "digest_schedule": "0 8 * * 1"
    }
    
    response = requests.post(f"{base_url}/api/v1/groups/", json=group_data, headers=headers)
    if response.status_code == 200:
        group_info = response.json()
        group_id = group_info["id"]
        print(f"   ✅ Group created: {group_info['name']}")
    else:
        # Get existing groups
        response = requests.get(f"{base_url}/api/v1/groups/", headers=headers)
        if response.status_code == 200:
            groups = response.json()
            if groups:
                group_id = groups[0]["id"]
                print(f"   ℹ️  Using existing group: {groups[0]['name']}")
            else:
                print("   ❌ No groups available")
                return
        else:
            print(f"   ❌ Failed to get groups")
            return
    
    # Add some demo activities if none exist
    print("\n3. 🏃 Checking activity data...")
    response = requests.get(f"{base_url}/api/v1/activities/stats?days_back=7", headers=headers)
    if response.status_code == 200:
        stats = response.json()
        print(f"   📊 Last 7 days: {stats['total_activities']} activities")
        print(f"   📏 Distance: {stats['total_distance_km']:.1f} km")
        print(f"   ⏱️  Time: {stats['total_duration_minutes']/60:.1f} hours")
        
        if stats['total_activities'] == 0:
            print("   ℹ️  No recent activities found")
            print("   💡 Run demo_activity.py first to add sample data")
    
    # Generate digest preview
    print("\n4. 📋 Generating weekly digest preview...")
    response = requests.get(f"{base_url}/api/v1/digest/{group_id}/preview", headers=headers)
    
    if response.status_code == 200:
        preview = response.json()
        print(f"   ✅ Preview generated successfully!")
        print(f"   👥 Group: {preview['group_name']}")
        print(f"   📅 Week {preview['period']['week_number']}")
        print(f"   📊 Activities: {preview['summary']['total_activities']}")
        print(f"   📏 Distance: {preview['summary']['total_distance_km']:.1f} km")
        print(f"   ⏱️  Duration: {preview['summary']['total_duration_hours']:.1f} hours")
        print(f"   📝 Message length: {preview['character_count']} chars")
        
        # Show formatted WhatsApp message
        print("\n   📱 WhatsApp Digest Message:")
        print("   " + "=" * 45)
        message_lines = preview['formatted_message'].split('\n')
        for line in message_lines:
            print(f"   {line}")
        print("   " + "=" * 45)
        
    else:
        print(f"   ❌ Failed to generate preview: {response.status_code}")
        print(f"   Error: {response.text}")
        return
    
    # Test sending the digest
    print("\n5. 📤 Testing digest send (simulation)...")
    response = requests.post(f"{base_url}/api/v1/digest/{group_id}/send", headers=headers)
    
    if response.status_code == 200:
        send_result = response.json()
        print(f"   ✅ Digest sent successfully!")
        print(f"   📋 Digest ID: {send_result['digest_id']}")
        print(f"   📱 WhatsApp Status: {send_result['whatsapp_status']}")
        print(f"   👥 Group: {send_result['group_name']}")
    else:
        print(f"   ❌ Failed to send digest: {response.status_code}")
        print(f"   Error: {response.text}")
    
    # Show available endpoints
    print("\n6. 🔗 Available digest endpoints:")
    print(f"   📋 Preview: GET {base_url}/api/v1/digest/{{group_id}}/preview")
    print(f"   📤 Send: POST {base_url}/api/v1/digest/{{group_id}}/send")
    print(f"   📚 API Docs: {base_url}/docs")
    
    print("\n" + "=" * 50)
    print("🎉 Weekly Digest Test Complete!")
    print("\n✅ Phase 3 Features Demonstrated:")
    print("   • Weekly digest generation")
    print("   • Activity analysis and statistics")
    print("   • Leaderboard calculations")
    print("   • Achievement detection")
    print("   • WhatsApp message formatting")
    print("   • Simulated message delivery")
    
    print(f"\n💡 Next Steps:")
    print(f"   • Add real Garmin credentials to .env file")
    print(f"   • Configure WhatsApp Business API")
    print(f"   • Set up automated scheduling")


if __name__ == "__main__":
    test_digest_with_demo_data()