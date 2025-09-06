"""
Activity endpoints
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.activity import Activity
from app.services.garmin_service import GarminService
from app.tasks import sync_user_activities_task

router = APIRouter()


class ActivityDetail(BaseModel):
    """Detailed activity response"""
    id: str
    activity_type: str
    activity_name: str
    start_time: str
    duration_minutes: int
    distance_km: float
    calories: int = None
    avg_heart_rate: int = None
    max_heart_rate: int = None
    elevation_gain: float = None
    processed_metrics: dict = {}
    
    class Config:
        from_attributes = True


class ActivityStats(BaseModel):
    """Activity statistics"""
    total_activities: int
    total_distance_km: float
    total_duration_minutes: int
    total_calories: int
    activity_types: dict
    weekly_summary: dict


@router.get("/", response_model=List[ActivityDetail])
async def list_activities(
    limit: int = Query(50, le=200),
    activity_type: Optional[str] = None,
    days_back: Optional[int] = Query(None, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's activities with optional filtering"""
    query = db.query(Activity).filter(Activity.user_id == current_user.id)
    
    # Filter by activity type
    if activity_type:
        query = query.filter(Activity.activity_type == activity_type)
    
    # Filter by date range
    if days_back:
        cutoff_date = datetime.now() - timedelta(days=days_back)
        query = query.filter(Activity.start_time >= cutoff_date)
    
    activities = query.order_by(Activity.start_time.desc()).limit(limit).all()
    
    return [
        ActivityDetail(
            id=str(activity.id),
            activity_type=activity.activity_type,
            activity_name=activity.activity_name or f"{activity.activity_type.title()} Activity",
            start_time=activity.start_time.isoformat(),
            duration_minutes=activity.duration_minutes,
            distance_km=activity.distance_km,
            calories=activity.calories,
            avg_heart_rate=activity.avg_heart_rate,
            max_heart_rate=activity.max_heart_rate,
            elevation_gain=activity.elevation_gain,
            processed_metrics=activity.processed_metrics or {}
        )
        for activity in activities
    ]


@router.get("/stats", response_model=ActivityStats)
async def get_activity_stats(
    days_back: int = Query(30, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's activity statistics"""
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    activities = (
        db.query(Activity)
        .filter(Activity.user_id == current_user.id)
        .filter(Activity.start_time >= cutoff_date)
        .all()
    )
    
    if not activities:
        return ActivityStats(
            total_activities=0,
            total_distance_km=0.0,
            total_duration_minutes=0,
            total_calories=0,
            activity_types={},
            weekly_summary={}
        )
    
    # Calculate totals
    total_distance = sum(a.distance_km for a in activities if a.distance_km)
    total_duration = sum(a.duration_minutes for a in activities if a.duration_minutes)
    total_calories = sum(a.calories for a in activities if a.calories)
    
    # Activity type breakdown
    activity_types = {}
    for activity in activities:
        activity_type = activity.activity_type
        if activity_type not in activity_types:
            activity_types[activity_type] = {
                "count": 0,
                "total_distance_km": 0.0,
                "total_duration_minutes": 0
            }
        
        activity_types[activity_type]["count"] += 1
        if activity.distance_km:
            activity_types[activity_type]["total_distance_km"] += activity.distance_km
        if activity.duration_minutes:
            activity_types[activity_type]["total_duration_minutes"] += activity.duration_minutes
    
    # Weekly summary (last 4 weeks)
    weekly_summary = {}
    for week_offset in range(4):
        week_start = datetime.now() - timedelta(days=(week_offset + 1) * 7)
        week_end = week_start + timedelta(days=7)
        
        week_activities = [
            a for a in activities
            if week_start <= a.start_time < week_end
        ]
        
        week_key = f"week_{week_offset + 1}"
        weekly_summary[week_key] = {
            "activities": len(week_activities),
            "distance_km": sum(a.distance_km for a in week_activities if a.distance_km),
            "duration_minutes": sum(a.duration_minutes for a in week_activities if a.duration_minutes)
        }
    
    return ActivityStats(
        total_activities=len(activities),
        total_distance_km=round(total_distance, 2),
        total_duration_minutes=total_duration,
        total_calories=total_calories,
        activity_types=activity_types,
        weekly_summary=weekly_summary
    )


@router.get("/{activity_id}", response_model=ActivityDetail)
async def get_activity(
    activity_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed activity information"""
    activity = (
        db.query(Activity)
        .filter(Activity.id == activity_id)
        .filter(Activity.user_id == current_user.id)
        .first()
    )
    
    if not activity:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    return ActivityDetail(
        id=str(activity.id),
        activity_type=activity.activity_type,
        activity_name=activity.activity_name or f"{activity.activity_type.title()} Activity",
        start_time=activity.start_time.isoformat(),
        duration_minutes=activity.duration_minutes,
        distance_km=activity.distance_km,
        calories=activity.calories,
        avg_heart_rate=activity.avg_heart_rate,
        max_heart_rate=activity.max_heart_rate,
        elevation_gain=activity.elevation_gain,
        processed_metrics=activity.processed_metrics or {}
    )


@router.post("/sync")
async def sync_activities(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger activity sync for current user"""
    # Trigger background task
    task = sync_user_activities_task.delay(str(current_user.id))
    
    return {
        "message": "Activity sync started",
        "task_id": task.id,
        "user": current_user.email
    }


@router.post("/sync/immediate")
async def sync_activities_immediate(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually sync activities immediately (for testing)"""
    try:
        garmin_service = GarminService(db)
        synced_activities = await garmin_service.sync_user_activities(current_user)
        
        return {
            "message": "Activity sync completed",
            "synced_activities": len(synced_activities),
            "activities": [
                {
                    "activity_type": activity.activity_type,
                    "activity_name": activity.activity_name,
                    "start_time": activity.start_time.isoformat(),
                    "duration_minutes": activity.duration_minutes,
                    "distance_km": activity.distance_km
                }
                for activity in synced_activities
            ]
        }
        
    except Exception as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync activities: {str(e)}"
        )