"""
Group management endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.group import Group, GroupMembership, UserRole

router = APIRouter()


class GroupCreate(BaseModel):
    """Group creation schema"""
    name: str
    description: str = ""
    whatsapp_group_id: str
    digest_schedule: str = "0 8 * * 1"  # Monday 8 AM default


class GroupResponse(BaseModel):
    """Group response schema"""
    id: str
    name: str
    description: str
    whatsapp_group_id: str
    digest_schedule: str
    is_active: bool
    member_count: int = 0
    
    class Config:
        from_attributes = True


class GroupMemberResponse(BaseModel):
    """Group member response schema"""
    user_id: str
    email: str
    full_name: str
    role: str
    joined_at: str
    
    class Config:
        from_attributes = True


@router.post("/", response_model=GroupResponse)
async def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new group"""
    # Check if WhatsApp group ID is already used
    existing_group = db.query(Group).filter(Group.whatsapp_group_id == group_data.whatsapp_group_id).first()
    if existing_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WhatsApp group ID already in use"
        )
    
    # Create group
    group = Group(
        name=group_data.name,
        description=group_data.description,
        whatsapp_group_id=group_data.whatsapp_group_id,
        admin_user_id=current_user.id,
        digest_schedule=group_data.digest_schedule
    )
    
    db.add(group)
    db.commit()
    db.refresh(group)
    
    # Add creator as admin member
    membership = GroupMembership(
        group_id=group.id,
        user_id=current_user.id,
        role=UserRole.ADMIN
    )
    
    db.add(membership)
    db.commit()
    
    return GroupResponse(
        id=str(group.id),
        name=group.name,
        description=group.description,
        whatsapp_group_id=group.whatsapp_group_id,
        digest_schedule=group.digest_schedule,
        is_active=group.is_active,
        member_count=1
    )


@router.get("/", response_model=List[GroupResponse])
async def list_user_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List groups the current user is a member of"""
    memberships = (
        db.query(GroupMembership)
        .filter(GroupMembership.user_id == current_user.id)
        .all()
    )
    
    groups = []
    for membership in memberships:
        group = membership.group
        member_count = db.query(GroupMembership).filter(GroupMembership.group_id == group.id).count()
        
        groups.append(GroupResponse(
            id=str(group.id),
            name=group.name,
            description=group.description,
            whatsapp_group_id=group.whatsapp_group_id,
            digest_schedule=group.digest_schedule,
            is_active=group.is_active,
            member_count=member_count
        ))
    
    return groups


@router.get("/{group_id}/members", response_model=List[GroupMemberResponse])
async def get_group_members(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get members of a group"""
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
    
    # Get all group members
    members = (
        db.query(GroupMembership)
        .join(User)
        .filter(GroupMembership.group_id == group_id)
        .all()
    )
    
    return [
        GroupMemberResponse(
            user_id=str(member.user_id),
            email=member.user.email,
            full_name=member.user.full_name,
            role=member.role.value,
            joined_at=member.joined_at.isoformat()
        )
        for member in members
    ]


@router.post("/{group_id}/join")
async def join_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join an existing group"""
    # Check if group exists
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group or not group.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Check if user is already a member
    existing_membership = (
        db.query(GroupMembership)
        .filter(GroupMembership.group_id == group_id)
        .filter(GroupMembership.user_id == current_user.id)
        .first()
    )
    
    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member of this group"
        )
    
    # Add membership
    membership = GroupMembership(
        group_id=group.id,
        user_id=current_user.id,
        role=UserRole.MEMBER
    )
    
    db.add(membership)
    db.commit()
    
    return {"message": f"Successfully joined group '{group.name}'"}


@router.delete("/{group_id}/leave")
async def leave_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Leave a group"""
    membership = (
        db.query(GroupMembership)
        .filter(GroupMembership.group_id == group_id)
        .filter(GroupMembership.user_id == current_user.id)
        .first()
    )
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not a member of this group"
        )
    
    # Check if user is the admin
    group = db.query(Group).filter(Group.id == group_id).first()
    if group and group.admin_user_id == current_user.id:
        # Check if there are other members
        other_members = (
            db.query(GroupMembership)
            .filter(GroupMembership.group_id == group_id)
            .filter(GroupMembership.user_id != current_user.id)
            .count()
        )
        
        if other_members > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot leave group as admin while other members exist"
            )
    
    db.delete(membership)
    db.commit()
    
    return {"message": "Successfully left the group"}