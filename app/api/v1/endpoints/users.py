"""
User management endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.garmin_service import GarminService

router = APIRouter()


class UserProfile(BaseModel):
    """User profile response"""
    id: str
    email: str
    full_name: str
    is_active: bool
    last_sync_at: str = None
    
    class Config:
        from_attributes = True


class ActivitySummary(BaseModel):
    """Activity summary for user"""
    id: str
    activity_type: str
    activity_name: str
    start_time: str
    distance_km: float
    duration_minutes: int
    calories: int = None
    
    class Config:
        from_attributes = True


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile"""
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        last_sync_at=current_user.last_sync_at.isoformat() if current_user.last_sync_at else None
    )


@router.get("/", response_model=List[UserProfile])
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all users (for admin purposes)"""
    users = db.query(User).filter(User.is_active == True).all()
    
    return [
        UserProfile(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            last_sync_at=user.last_sync_at.isoformat() if user.last_sync_at else None
        )
        for user in users
    ]


@router.post("/sync-activities")
async def sync_user_activities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger activity sync for current user"""
    try:
        garmin_service = GarminService(db)
        synced_activities = await garmin_service.sync_user_activities(current_user)
        
        return {
            "message": f"Successfully synced {len(synced_activities)} new activities",
            "synced_count": len(synced_activities)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync activities: {str(e)}"
        )


@router.get("/activities", response_model=List[ActivitySummary])
async def get_user_activities(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's recent activities"""
    from app.models.activity import Activity
    
    activities = (
        db.query(Activity)
        .filter(Activity.user_id == current_user.id)
        .order_by(Activity.start_time.desc())
        .limit(limit)
        .all()
    )
    
    return [
        ActivitySummary(
            id=str(activity.id),
            activity_type=activity.activity_type,
            activity_name=activity.activity_name or f"{activity.activity_type.title()} Activity",
            start_time=activity.start_time.isoformat(),
            distance_km=activity.distance_km,
            duration_minutes=activity.duration_minutes,
            calories=activity.calories
        )
        for activity in activities
    ]