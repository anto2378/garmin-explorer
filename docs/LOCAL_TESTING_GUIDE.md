# Local Testing Guide for Fake Sporters Dashboard

This guide will help you set up and test the Garmin activity dashboard locally.

## ✅ Quick Start (Recommended)

### Option 1: Using the Test Server (Easiest)

1. **Setup virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings
   ```

2. **Start the test server:**
   ```bash
   python test_server.py
   ```

3. **Access the dashboard:**
   - **Dashboard**: http://localhost:8001/fake-sporters
   - **API Docs**: http://localhost:8001/docs
   - **Weekly Data API**: http://localhost:8001/api/v1/dashboard/weekly
   - **WhatsApp Digest API**: http://localhost:8001/api/v1/whatsapp/weekly

The test server automatically creates 5 test users with 24 activities for the current week.

### Option 2: Using the Full Application

1. **Setup environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Create test database:**
   ```bash
   python test_dashboard_local.py
   ```

3. **Start the server:**
   ```bash
   source .venv/bin/activate
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access the dashboard:**
   - **Dashboard**: http://localhost:8000/fake-sporters

## 📊 Test Data

The test database includes 5 users with realistic activity data:

### Users & Activities:
- **John Runner**: 5 running activities, 65K steps, 50km distance
- **Sarah Cyclist**: 4 cycling activities, 3.8K calories burned  
- **Mike Walker**: 7 walking activities (daily walker), 51.8K steps
- **Emma Swimmer**: 6 mixed activities (swimming + running), 18km running
- **Alex Hiker**: 2 hiking activities (weekend warrior), 32.5K steps

### Week Coverage:
- Activities span the current week (Monday to Sunday)
- Mix of different activity types: running, cycling, walking, swimming, hiking
- Realistic metrics: steps, distance, calories, heart rate, duration

## 🧪 Testing Features

### Dashboard Features to Test:
1. **Weekly Overview Cards**: Total steps, running distance, active calories, activities
2. **User Rankings**: Sorted by activity count and performance
3. **Individual Stats**: Each user's detailed metrics and activity breakdown
4. **Week Navigation**: Switch between current week, last week, etc.
5. **Responsive Design**: Test on different screen sizes

### API Endpoints to Test:

#### Weekly Dashboard Data
```bash
curl http://localhost:8001/api/v1/dashboard/weekly
curl http://localhost:8001/api/v1/dashboard/weekly?week_offset=1  # Previous week
```

#### WhatsApp Digest
```bash
curl http://localhost:8001/api/v1/whatsapp/weekly
```

Expected response includes formatted message ready for WhatsApp sharing.

## 🔧 Troubleshooting

### Common Issues:

1. **Port already in use**:
   ```bash
   # Try different port
   python test_server.py  # Uses port 8001
   # or
   python -m uvicorn main:app --port 8002
   ```

2. **Module not found errors**:
   ```bash
   # Make sure virtual environment is activated
   source .venv/bin/activate
   pip install fastapi uvicorn sqlalchemy pydantic
   ```

3. **Database issues**:
   ```bash
   # Remove and recreate database
   rm test_garmin.db
   python test_server.py  # Will recreate with fresh data
   ```

4. **Dashboard shows "Unauthorized"**:
   - This indicates the dashboard endpoints require authentication
   - Use the `test_server.py` which has public endpoints
   - Or modify the main application to make dashboard endpoints public

## 🎯 What You Should See

### Dashboard Display:
- **Header**: "Fake Sporters" with week navigation
- **Total Cards**: 4 cards showing group totals (173.5K steps, 68km running, etc.)
- **User Cards**: 5 user performance cards with rankings and breakdowns
- **Responsive Layout**: Works on desktop and mobile

### API Responses:
- **Dashboard API**: JSON with users array, totals object, week info
- **WhatsApp API**: Formatted message with emojis, rankings, and summaries

### Sample WhatsApp Message:
```
🏃‍♂️ *FAKE SPORTERS WEEKLY DIGEST* 🏃‍♀️
📅 Week 35, 2025

📊 *GROUP TOTALS*
👟 Total Steps: *173,500*
🏃‍♂️ Running Distance: *68.0 km*
🔥 Active Calories: *13,950*
⚡ Total Activities: *24*
👥 Active Members: *5*

🏆 *TOP PERFORMERS*
🥇 Most Active: *Mike Walker* (7 activities)
👟 Most Steps: *John Runner* (65,000 steps)
...
```

## 🚀 Deployment Notes

When deploying to production (nebluda.com):

1. **Update API base URL** in `static/dashboard.html` if needed
2. **Configure CORS** for your domain in FastAPI settings
3. **Set up proper database** (PostgreSQL instead of SQLite)
4. **Configure reverse proxy** to route `/fake-sporters` to your FastAPI app
5. **Update WhatsApp message** to use your actual domain URL

## 📝 Files Created/Modified

### New Files:
- `test_server.py` - Minimal test server with embedded test data
- `test_dashboard_local.py` - Test data creation script
- `.env.local` - Local testing configuration
- `LOCAL_TESTING_GUIDE.md` - This guide

### Modified Files:
- `main.py` - Added `/fake-sporters` route and static file serving
- `static/dashboard.html` - Dashboard frontend
- `app/api/v1/endpoints/dashboard.py` - Dashboard API endpoints
- `app/api/v1/endpoints/whatsapp_digest.py` - WhatsApp digest API
- `app/api/v1/api.py` - Added new router includes

The dashboard is now fully functional and ready for testing! 🎉