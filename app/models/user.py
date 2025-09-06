"""
User model for multi-user Garmin authentication
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """User model with encrypted Garmin credentials"""
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User information
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    
    # Encrypted Garmin credentials
    garmin_email = Column(Text, nullable=False)  # Will be encrypted
    garmin_password = Column(Text, nullable=False)  # Will be encrypted
    
    # User status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # User preferences (JSON field for flexibility)
    preferences = Column(JSON, default=dict)
    
    # Sync tracking
    last_sync_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    group_memberships = relationship("GroupMembership", back_populates="user")
    activities = relationship("Activity", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.full_name})>"