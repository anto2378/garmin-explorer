"""
WeeklyDigest model for storing generated digest content
"""

import uuid
from datetime import datetime, date
from enum import Enum

from sqlalchemy import Column, String, DateTime, Date, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DigestStatus(str, Enum):
    """Status of digest generation and delivery"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class WeeklyDigest(Base):
    """Weekly digest model for storing generated summaries"""
    
    __tablename__ = "weekly_digests"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Group reference
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False)
    
    # Week period
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)
    
    # Digest content
    content = Column(Text, nullable=False)  # Formatted message for WhatsApp
    
    # Status tracking
    status = Column(SQLEnum(DigestStatus), default=DigestStatus.PENDING, nullable=False)
    
    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Relationships
    group = relationship("Group", back_populates="weekly_digests")
    
    def __repr__(self):
        return (
            f"<WeeklyDigest(id={self.id}, group_id={self.group_id}, "
            f"week={self.week_start} - {self.week_end}, status={self.status})>"
        )