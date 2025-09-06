"""
Weekly digest endpoints
"""

from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.group import GroupMembership
from app.services.digest_service import DigestService
from app.services.whatsapp_service import WhatsAppService

router = APIRouter()


class DigestResponse(BaseModel):
    """Digest response schema"""
    digest_id: str
    group_name: str
    period: dict
    summary: dict
    leaderboard: dict
    achievements: list
    formatted_message: str
    
    class Config:
        from_attributes = True


class DigestSendResponse(BaseModel):
    """Digest send response schema"""
    digest_id: str
    group_name: str
    whatsapp_status: str
    message_preview: str
    
    class Config:
        from_attributes = True


@router.get("/{group_id}/generate", response_model=DigestResponse)
async def generate_digest(
    group_id: str,
    week_offset: int = 0,  # 0 = current week, 1 = last week, etc.
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate weekly digest for a group"""
    # Verify user is a member of the group
    membership = (
        db.query(GroupMembership)
        .filter(GroupMembership.group_id == group_id)
        .filter(GroupMembership.user_id == current_user.id)
        .first()
    )
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found or access denied"
        )
    
    # Calculate week start (Monday)
    today = datetime.now()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday + (week_offset * 7))
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    try:
        digest_service = DigestService(db)
        digest_data = digest_service.generate_weekly_digest(group_id, week_start)
        
        # Format message
        formatted_message = digest_service.format_digest_message(digest_data)
        digest_data["formatted_message"] = formatted_message
        
        return DigestResponse(
            digest_id=digest_data["digest_id"],
            group_name=digest_data["group"]["name"],
            period=digest_data["period"],
            summary=digest_data["summary"],
            leaderboard=digest_data["leaderboard"],
            achievements=digest_data["achievements"],
            formatted_message=formatted_message
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate digest: {str(e)}"
        )


@router.post("/{group_id}/send", response_model=DigestSendResponse)
async def send_digest(
    group_id: str,
    week_offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate and send weekly digest to WhatsApp group"""
    # Verify user is admin of the group
    membership = (
        db.query(GroupMembership)
        .filter(GroupMembership.group_id == group_id)
        .filter(GroupMembership.user_id == current_user.id)
        .first()
    )
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    if membership.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can send digests"
        )
    
    # Calculate week start
    today = datetime.now()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday + (week_offset * 7))
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    try:
        # Generate digest
        digest_service = DigestService(db)
        digest_data = digest_service.generate_weekly_digest(group_id, week_start)
        
        # Format message
        formatted_message = digest_service.format_digest_message(digest_data)
        
        # Send to WhatsApp
        whatsapp_service = WhatsAppService()
        group = digest_data["group"]
        
        # Get group's WhatsApp ID from database
        from app.models.group import Group
        group_record = db.query(Group).filter(Group.id == group_id).first()
        whatsapp_group_id = group_record.whatsapp_group_id
        
        send_result = whatsapp_service.send_digest(whatsapp_group_id, formatted_message)
        
        # Update digest status
        from app.models.digest import WeeklyDigest
        digest_record = db.query(WeeklyDigest).filter(WeeklyDigest.id == digest_data["digest_id"]).first()
        if digest_record:
            digest_record.status = "sent" if send_result["status"] in ["sent", "simulated"] else "failed"
            digest_record.sent_at = datetime.utcnow()
            db.commit()
        
        return DigestSendResponse(
            digest_id=digest_data["digest_id"],
            group_name=group["name"],
            whatsapp_status=send_result["status"],
            message_preview=formatted_message[:200] + "..." if len(formatted_message) > 200 else formatted_message
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send digest: {str(e)}"
        )


@router.get("/{group_id}/preview")
async def preview_digest(
    group_id: str,
    week_offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview digest message without saving or sending"""
    # Verify user is a member of the group
    membership = (
        db.query(GroupMembership)
        .filter(GroupMembership.group_id == group_id)
        .filter(GroupMembership.user_id == current_user.id)
        .first()
    )
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found or access denied"
        )
    
    # Calculate week start
    today = datetime.now()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday + (week_offset * 7))
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    try:
        digest_service = DigestService(db)
        
        # Generate digest data without saving to database
        from app.models.group import Group
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise ValueError(f"Group {group_id} not found")
        
        week_end = week_start + timedelta(days=7)
        
        # Get group members
        from app.models.user import User
        members = (
            db.query(User)
            .join(GroupMembership)
            .filter(GroupMembership.group_id == group_id)
            .all()
        )
        
        # Generate preview data
        preview_data = {
            "group": {
                "id": str(group.id),
                "name": group.name,
                "member_count": len(members)
            },
            "period": {
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "week_number": week_start.isocalendar()[1]
            },
            "summary": digest_service._generate_group_summary(members, week_start, week_end),
            "leaderboard": digest_service._generate_leaderboard(members, week_start, week_end),
            "achievements": digest_service._generate_achievements(members, week_start, week_end)
        }
        
        formatted_message = digest_service.format_digest_message(preview_data)
        
        return {
            "preview": True,
            "group_name": group.name,
            "period": preview_data["period"],
            "summary": preview_data["summary"],
            "formatted_message": formatted_message,
            "character_count": len(formatted_message)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )