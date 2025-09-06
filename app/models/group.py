"""
Group and GroupMembership models for organizing users
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, Enum):
    """User roles within a group"""
    ADMIN = "admin"
    MEMBER = "member"


class Group(Base):
    """Group model for organizing users and WhatsApp integration"""
    
    __tablename__ = "groups"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Group information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # WhatsApp integration
    whatsapp_group_id = Column(String(255), nullable=False, unique=True)
    
    # Group admin (foreign key to User)
    admin_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Group status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Digest scheduling (cron format)
    digest_schedule = Column(String(100), default="0 8 * * 1")  # Every Monday at 8 AM
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    admin_user = relationship("User", foreign_keys=[admin_user_id])
    memberships = relationship("GroupMembership", back_populates="group")
    weekly_digests = relationship("WeeklyDigest", back_populates="group")
    
    def __repr__(self):
        return f"<Group(id={self.id}, name={self.name}, whatsapp_id={self.whatsapp_group_id})>"


class GroupMembership(Base):
    """Many-to-many relationship between Users and Groups with roles"""
    
    __tablename__ = "group_memberships"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Membership details
    role = Column(SQLEnum(UserRole), default=UserRole.MEMBER, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    group = relationship("Group", back_populates="memberships")
    user = relationship("User", back_populates="group_memberships")
    
    def __repr__(self):
        return f"<GroupMembership(group_id={self.group_id}, user_id={self.user_id}, role={self.role})>"