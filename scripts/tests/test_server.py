#!/usr/bin/env python3
"""
Minimal test server for the dashboard with test data
Includes only dashboard endpoints without complex dependencies
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel

# Create FastAPI app
app = FastAPI(title="Garmin Dashboard Test Server")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = "sqlite:///./test_garmin.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    garmin_email = Column(Text, nullable=False)
    garmin_password = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Activity(Base):
    __tablename__ = "activities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    garmin_activity_id = Column(String(100), nullable=False)
    activity_type = Column(String(100), nullable=False)
    activity_name = Column(String(255), nullable=True)
    start_time = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=True)
    distance = Column(Float, nullable=True)
    calories = Column(Integer, nullable=True)
    avg_heart_rate = Column(Integer, nullable=True)
    max_heart_rate = Column(Integer, nullable=True)
    elevation_gain = Column(Float, nullable=True)
    processed_metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    @property
    def distance_km(self) -> float:
        return self.distance / 1000.0 if self.distance else 0.0

    @property
    def duration_minutes(self) -> int:
        return self.duration // 60 if self.duration else 0

# Pydantic Models
class UserWeeklyStats(BaseModel):
    name: str
    email: str
    total_steps: int = 0
    running_distance_km: float = 0.0
    active_calories: int = 0
    total_activities: int = 0
    activities_breakdown: Dict[str, int] = {}

class WeeklyDashboard(BaseModel):
    week_start: str
    week_end: str
    week_number: int
    year: int
    users: List[UserWeeklyStats]
    totals: Dict[str, Any]
    previous_week_comparison: Dict[str, Any] = {}
    monthly_comparison: Dict[str, Any] = {}
    year_to_date_comparison: Dict[str, Any] = {}

class WhatsAppDigest(BaseModel):
    week_start: str
    week_end: str
    week_number: int
    year: int
    message: str
    summary_stats: Dict[str, Any]

# API Routes
@app.get("/")
async def root():
    return {"message": "Garmin Dashboard Test Server", "status": "running"}

@app.get("/fake-sporters")
async def fake_sporters_dashboard():
    """Public dashboard endpoint"""
    static_path = os.path.join("static", "dashboard.html")
    if os.path.exists(static_path):
        return FileResponse(static_path)
    else:
        return {"error": "Dashboard not found", "path": static_path}

@app.get("/api/v1/dashboard/weekly", response_model=WeeklyDashboard)
async def get_weekly_dashboard(
    week_offset: int = Query(0, description="Weeks back from current week (0 = current week)"),
    db: Session = Depends(get_db)
):
    """Get weekly activity dashboard for all users"""
    
    # Calculate week period
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday() + (week_offset * 7))
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    
    # Get all active users
    users = db.query(User).filter(User.is_active == True).all()
    
    user_stats = []
    totals = {
        "total_steps": 0,
        "total_running_distance": 0.0,
        "total_active_calories": 0,
        "total_activities": 0,
        "active_users": 0
    }
    
    for user in users:
        # Get user's activities for the week
        activities = (
            db.query(Activity)
            .filter(Activity.user_id == user.id)
            .filter(Activity.start_time >= week_start)
            .filter(Activity.start_time < week_end)
            .all()
        )
        
        if not activities:
            user_stats.append(UserWeeklyStats(
                name=user.full_name,
                email=user.email,
                total_steps=0,
                running_distance_km=0.0,
                active_calories=0,
                total_activities=0,
                activities_breakdown={}
            ))
            continue
        
        # Calculate user metrics
        total_steps = 0
        running_distance = 0.0
        active_calories = 0
        activities_breakdown = {}
        
        for activity in activities:
            # Extract steps from processed_metrics
            if activity.processed_metrics and 'steps' in activity.processed_metrics:
                total_steps += activity.processed_metrics.get('steps', 0)
            
            # Calculate running distance
            if activity.activity_type.lower() in ['running', 'run', 'jogging']:
                running_distance += activity.distance_km if activity.distance_km else 0.0
            
            # Active calories
            if activity.calories:
                active_calories += activity.calories
            elif activity.processed_metrics and 'active_calories' in activity.processed_metrics:
                active_calories += activity.processed_metrics.get('active_calories', 0)
            
            # Activity breakdown
            activity_type = activity.activity_type.replace('_', ' ').title()
            activities_breakdown[activity_type] = activities_breakdown.get(activity_type, 0) + 1
        
        user_stat = UserWeeklyStats(
            name=user.full_name,
            email=user.email,
            total_steps=int(total_steps),
            running_distance_km=round(running_distance, 2),
            active_calories=int(active_calories),
            total_activities=len(activities),
            activities_breakdown=activities_breakdown
        )
        
        user_stats.append(user_stat)
        
        # Add to totals
        totals["total_steps"] += user_stat.total_steps
        totals["total_running_distance"] += user_stat.running_distance_km
        totals["total_active_calories"] += user_stat.active_calories
        totals["total_activities"] += user_stat.total_activities
        if user_stat.total_activities > 0:
            totals["active_users"] += 1
    
    # Sort users by total activity (most active first)
    user_stats.sort(key=lambda x: (x.total_activities, x.total_steps, x.active_calories), reverse=True)
    
    return WeeklyDashboard(
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        week_number=week_start.isocalendar()[1],
        year=week_start.year,
        users=user_stats,
        totals=totals,
        previous_week_comparison={},  # Simplified for testing
        monthly_comparison={},
        year_to_date_comparison={}
    )

@app.get("/api/v1/whatsapp/weekly", response_model=WhatsAppDigest)
async def get_whatsapp_digest(
    week_offset: int = Query(0, description="Weeks back from current week (0 = current week)"),
    db: Session = Depends(get_db)
):
    """Generate WhatsApp-formatted weekly digest"""
    
    # Calculate week period
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday() + (week_offset * 7))
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    
    # Get dashboard data
    dashboard_data = await get_weekly_dashboard(week_offset, db)
    
    # Create WhatsApp message
    message_parts = []
    message_parts.append("🏃‍♂️ *FAKE SPORTERS WEEKLY DIGEST* 🏃‍♀️")
    message_parts.append(f"📅 Week {dashboard_data.week_number}, {dashboard_data.year}")
    message_parts.append("")
    
    # Group totals
    message_parts.append("📊 *GROUP TOTALS*")
    message_parts.append(f"👟 Total Steps: *{dashboard_data.totals['total_steps']:,}*")
    message_parts.append(f"🏃‍♂️ Running Distance: *{dashboard_data.totals['total_running_distance']:.1f} km*")
    message_parts.append(f"🔥 Active Calories: *{dashboard_data.totals['total_active_calories']:,}*")
    message_parts.append(f"⚡ Total Activities: *{dashboard_data.totals['total_activities']}*")
    message_parts.append(f"👥 Active Members: *{dashboard_data.totals['active_users']}*")
    message_parts.append("")
    
    # Top performers
    if dashboard_data.users:
        message_parts.append("🏆 *TOP PERFORMERS*")
        top_user = dashboard_data.users[0]
        message_parts.append(f"🥇 Most Active: *{top_user.name}* ({top_user.total_activities} activities)")
        
        # Find user with most steps
        most_steps_user = max(dashboard_data.users, key=lambda x: x.total_steps)
        message_parts.append(f"👟 Most Steps: *{most_steps_user.name}* ({most_steps_user.total_steps:,} steps)")
        
        message_parts.append("")
    
    # Individual summary
    if dashboard_data.users:
        message_parts.append("👥 *INDIVIDUAL SUMMARY*")
        for i, user in enumerate(dashboard_data.users[:5]):  # Top 5
            rank_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
            message_parts.append(f"{rank_emoji} *{user.name}*: {user.total_activities} activities")
            if user.total_steps > 0 or user.active_calories > 0:
                parts = []
                if user.total_steps > 0:
                    parts.append(f"{user.total_steps:,} steps")
                if user.running_distance_km > 0:
                    parts.append(f"{user.running_distance_km:.1f}km run")
                if user.active_calories > 0:
                    parts.append(f"{user.active_calories:,} cal")
                message_parts.append(f"    {' • '.join(parts)}")
        message_parts.append("")
    
    message_parts.append("💪 *Keep up the great work, everyone!*")
    message_parts.append("📱 View dashboard: localhost:8001/fake-sporters")
    
    return WhatsAppDigest(
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        week_number=week_start.isocalendar()[1],
        year=week_start.year,
        message="\n".join(message_parts),
        summary_stats={
            "totals": dashboard_data.totals,
            "user_count": len([u for u in dashboard_data.users if u.total_activities > 0])
        }
    )

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Create tables and load test data
@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    
    # Check if we already have data
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            print("Loading test data...")
            
            # Create test users and activities (same as in test_dashboard_local.py)
            users = [
                User(email="john@test.com", full_name="John Runner", garmin_email="enc", garmin_password="enc"),
                User(email="sarah@test.com", full_name="Sarah Cyclist", garmin_email="enc", garmin_password="enc"),
                User(email="mike@test.com", full_name="Mike Walker", garmin_email="enc", garmin_password="enc"),
                User(email="emma@test.com", full_name="Emma Swimmer", garmin_email="enc", garmin_password="enc"),
                User(email="alex@test.com", full_name="Alex Hiker", garmin_email="enc", garmin_password="enc")
            ]
            
            for user in users:
                db.add(user)
            db.commit()
            
            for user in users:
                db.refresh(user)
            
            # Create activities for current week
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            
            activities = []
            
            # John's running activities
            for i in range(5):
                activity_date = week_start + timedelta(days=i)
                activities.append(Activity(
                    user_id=users[0].id,
                    garmin_activity_id=f"john_run_{i}",
                    activity_type="running",
                    activity_name=f"Morning Run {i+1}",
                    start_time=activity_date.replace(hour=7, minute=0),
                    duration=3600 + (i * 300),
                    distance=8000 + (i * 1000),
                    calories=600 + (i * 50),
                    processed_metrics={"steps": 10000 + (i * 1500), "active_calories": 600 + (i * 50)}
                ))
            
            # Sarah's cycling activities  
            for i in range(4):
                activity_date = week_start + timedelta(days=i)
                activities.append(Activity(
                    user_id=users[1].id,
                    garmin_activity_id=f"sarah_cycle_{i}",
                    activity_type="cycling",
                    activity_name=f"Evening Ride {i+1}",
                    start_time=activity_date.replace(hour=18, minute=0),
                    duration=5400 + (i * 600),
                    distance=25000 + (i * 5000),
                    calories=800 + (i * 100),
                    processed_metrics={"steps": 200 + (i * 50), "active_calories": 800 + (i * 100)}
                ))
            
            # Mike's walking activities
            for i in range(7):
                activity_date = week_start + timedelta(days=i)
                activities.append(Activity(
                    user_id=users[2].id,
                    garmin_activity_id=f"mike_walk_{i}",
                    activity_type="walking",
                    activity_name=f"Daily Walk {i+1}",
                    start_time=activity_date.replace(hour=19, minute=0),
                    duration=1800 + (i * 300),
                    distance=3000 + (i * 500),
                    calories=200 + (i * 30),
                    processed_metrics={"steps": 5000 + (i * 800), "active_calories": 200 + (i * 30)}
                ))
            
            # Emma's mixed activities
            for i in range(3):
                activity_date = week_start + timedelta(days=i * 2)
                activities.extend([
                    Activity(
                        user_id=users[3].id,
                        garmin_activity_id=f"emma_swim_{i}",
                        activity_type="swimming",
                        activity_name=f"Pool Session {i+1}",
                        start_time=activity_date.replace(hour=6, minute=0),
                        duration=2700 + (i * 300),
                        distance=1500 + (i * 300),
                        calories=400 + (i * 50),
                        processed_metrics={"steps": 0, "active_calories": 400 + (i * 50)}
                    ),
                    Activity(
                        user_id=users[3].id,
                        garmin_activity_id=f"emma_run_{i}",
                        activity_type="running",
                        activity_name=f"Recovery Run {i+1}",
                        start_time=(activity_date + timedelta(days=1)).replace(hour=7, minute=30),
                        duration=2400 + (i * 300),
                        distance=5000 + (i * 1000),
                        calories=350 + (i * 40),
                        processed_metrics={"steps": 6500 + (i * 1200), "active_calories": 350 + (i * 40)}
                    )
                ])
            
            # Alex's hiking activities
            weekend_activities = [
                Activity(
                    user_id=users[4].id,
                    garmin_activity_id="alex_hike_1",
                    activity_type="hiking",
                    activity_name="Mountain Trail",
                    start_time=(week_start + timedelta(days=5)).replace(hour=8, minute=0),
                    duration=14400,
                    distance=15000,
                    calories=1200,
                    elevation_gain=800,
                    processed_metrics={"steps": 18000, "active_calories": 1200}
                ),
                Activity(
                    user_id=users[4].id,
                    garmin_activity_id="alex_hike_2",
                    activity_type="hiking",
                    activity_name="Forest Loop",
                    start_time=(week_start + timedelta(days=6)).replace(hour=9, minute=0),
                    duration=10800,
                    distance=12000,
                    calories=900,
                    elevation_gain=500,
                    processed_metrics={"steps": 14500, "active_calories": 900}
                )
            ]
            activities.extend(weekend_activities)
            
            for activity in activities:
                db.add(activity)
            
            db.commit()
            print(f"✅ Loaded {len(users)} users and {len(activities)} activities")
        else:
            print("✅ Test data already exists")
            
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Garmin Dashboard Test Server...")
    print("Dashboard: http://localhost:8001/fake-sporters")
    print("API docs: http://localhost:8001/docs")
    print("Weekly API: http://localhost:8001/api/v1/dashboard/weekly")
    print("WhatsApp API: http://localhost:8001/api/v1/whatsapp/weekly")
    uvicorn.run(app, host="0.0.0.0", port=8001)