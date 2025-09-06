"""
Activity model for storing Garmin activity data
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Activity(Base):
    """Activity model for storing normalized Garmin activity data"""
    
    __tablename__ = "activities"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User reference
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Garmin activity identification
    garmin_activity_id = Column(String(100), nullable=False)
    
    # Activity details
    activity_type = Column(String(100), nullable=False)
    activity_name = Column(String(255), nullable=True)
    
    # Timing
    start_time = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    
    # Metrics
    distance = Column(Float, nullable=True)  # Distance in meters
    calories = Column(Integer, nullable=True)
    avg_heart_rate = Column(Integer, nullable=True)
    max_heart_rate = Column(Integer, nullable=True)
    elevation_gain = Column(Float, nullable=True)  # Elevation in meters
    
    # Raw and processed data
    raw_data = Column(JSON, nullable=True)  # Full Garmin response
    processed_metrics = Column(JSON, nullable=True)  # Calculated metrics
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="activities")
    
    def __repr__(self):
        return (
            f"<Activity(id={self.id}, user_id={self.user_id}, "
            f"type={self.activity_type}, date={self.start_time.date()})>"
        )
    
    @property
    def distance_km(self) -> float:
        """Get distance in kilometers"""
        return self.distance / 1000.0 if self.distance else 0.0
    
    @property
    def duration_minutes(self) -> int:
        """Get duration in minutes"""
        return self.duration // 60 if self.duration else 0