"""
Database models for the Garmin Companion System
"""

from app.core.database import Base

# Import all models to register them with SQLAlchemy
from .user import User
from .group import Group, GroupMembership
from .activity import Activity
from .digest import WeeklyDigest

__all__ = [
    "Base",
    "User",
    "Group",
    "GroupMembership", 
    "Activity",
    "WeeklyDigest"
]