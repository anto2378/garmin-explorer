"""
Celery background tasks
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from celery import current_task
from sqlalchemy.orm import sessionmaker

from app.celery_app import celery
from app.core.database import engine
from app.models.user import User
from app.models.group import Group
from app.services.garmin_service import GarminService

# Create session factory for tasks
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = logging.getLogger(__name__)


@celery.task(bind=True)
def sync_user_activities_task(self, user_id: str) -> Dict[str, Any]:
    """Sync activities for a specific user"""
    try:
        db = SessionLocal()
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": f"User {user_id} not found"}
        
        # Sync activities (convert async to sync)
        import asyncio
        garmin_service = GarminService(db)
        
        # Run async function in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        synced_activities = loop.run_until_complete(
            garmin_service.sync_user_activities(user)
        )
        
        db.close()
        
        return {
            "user_email": user.email,
            "synced_activities": len(synced_activities),
            "status": "success"
        }
        
    except Exception as exc:
        logger.error(f"Failed to sync activities for user {user_id}: {exc}")
        
        # Update task state
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc), "user_id": user_id}
        )
        
        return {"error": str(exc), "user_id": user_id}


@celery.task
def sync_all_users_activities() -> Dict[str, Any]:
    """Sync activities for all active users"""
    try:
        db = SessionLocal()
        
        # Convert async to sync
        import asyncio
        garmin_service = GarminService(db)
        
        # Run async function in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        results = loop.run_until_complete(garmin_service.sync_all_users())
        
        db.close()
        
        logger.info(f"Bulk sync completed: {results}")
        return results
        
    except Exception as exc:
        logger.error(f"Failed to sync all users: {exc}")
        return {"error": str(exc)}


@celery.task
def generate_weekly_digests() -> Dict[str, Any]:
    """Generate and send weekly digests for all active groups"""
    try:
        db = SessionLocal()
        
        # Get all active groups
        groups = db.query(Group).filter(Group.is_active == True).all()
        
        results = {
            "total_groups": len(groups),
            "successful_digests": 0,
            "failed_digests": 0,
            "errors": []
        }
        
        for group in groups:
            try:
                # TODO: Implement digest generation and WhatsApp sending
                # This would involve:
                # 1. Generate weekly digest for group members
                # 2. Send to WhatsApp group
                # 3. Store digest record
                
                results["successful_digests"] += 1
                logger.info(f"Generated digest for group {group.name}")
                
            except Exception as e:
                results["failed_digests"] += 1
                results["errors"].append({
                    "group_name": group.name,
                    "error": str(e)
                })
                logger.error(f"Failed to generate digest for group {group.name}: {e}")
        
        db.close()
        
        return results
        
    except Exception as exc:
        logger.error(f"Failed to generate weekly digests: {exc}")
        return {"error": str(exc)}


@celery.task
def cleanup_old_data() -> Dict[str, Any]:
    """Clean up old activity data and digest records"""
    try:
        db = SessionLocal()
        
        # Delete activities older than 1 year
        cutoff_date = datetime.now() - timedelta(days=365)
        
        from app.models.activity import Activity
        from app.models.digest import WeeklyDigest
        
        deleted_activities = (
            db.query(Activity)
            .filter(Activity.start_time < cutoff_date)
            .count()
        )
        
        db.query(Activity).filter(Activity.start_time < cutoff_date).delete()
        
        # Delete digest records older than 6 months
        digest_cutoff = datetime.now() - timedelta(days=180)
        deleted_digests = (
            db.query(WeeklyDigest)
            .filter(WeeklyDigest.generated_at < digest_cutoff)
            .count()
        )
        
        db.query(WeeklyDigest).filter(WeeklyDigest.generated_at < digest_cutoff).delete()
        
        db.commit()
        db.close()
        
        results = {
            "deleted_activities": deleted_activities,
            "deleted_digests": deleted_digests,
            "status": "success"
        }
        
        logger.info(f"Cleanup completed: {results}")
        return results
        
    except Exception as exc:
        logger.error(f"Failed to cleanup old data: {exc}")
        return {"error": str(exc)}