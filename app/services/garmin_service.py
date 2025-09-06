"""
Multi-user Garmin integration service extending existing functionality
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session

from garminconnect import Garmin

from app.core.encryption import decrypt_credential
from app.models.user import User
from app.models.activity import Activity

logger = logging.getLogger(__name__)


class GarminService:
    """Multi-user Garmin integration service"""
    
    def __init__(self, db: Session):
        self.db = db
        self._clients: Dict[str, Garmin] = {}  # Cache authenticated clients
    
    async def get_authenticated_client(self, user: User) -> Garmin:
        """Get authenticated Garmin client for user"""
        user_id = str(user.id)
        
        # Return cached client if available
        if user_id in self._clients:
            return self._clients[user_id]
        
        try:
            # Decrypt credentials
            garmin_email = decrypt_credential(user.garmin_email)
            garmin_password = decrypt_credential(user.garmin_password)
            
            # Create and authenticate client
            client = Garmin(garmin_email, garmin_password)
            client.login()
            
            # Cache the authenticated client
            self._clients[user_id] = client
            logger.info(f"Successfully authenticated Garmin client for user {user.email}")
            
            return client
            
        except Exception as e:
            logger.error(f"Failed to authenticate Garmin client for user {user.email}: {e}")
            raise Exception(f"Garmin authentication failed: {str(e)}")
    
    async def fetch_user_activities(
        self, 
        user: User, 
        start_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch activities for a specific user"""
        try:
            client = await self.get_authenticated_client(user)
            
            # Fetch activities from Garmin
            activities = client.get_activities(0, limit)
            
            if not activities:
                logger.warning(f"No activities found for user {user.email}")
                return []
            
            # Filter by start_date if provided
            if start_date:
                filtered_activities = []
                for activity in activities:
                    activity_date_str = activity.get("startTimeLocal", "")
                    if activity_date_str:
                        try:
                            activity_date = datetime.fromisoformat(activity_date_str.replace("Z", "+00:00"))
                            if activity_date >= start_date:
                                filtered_activities.append(activity)
                        except ValueError:
                            continue
                activities = filtered_activities
            
            logger.info(f"Fetched {len(activities)} activities for user {user.email}")
            return activities
            
        except Exception as e:
            logger.error(f"Failed to fetch activities for user {user.email}: {e}")
            raise
    
    async def sync_user_activities(
        self, 
        user: User, 
        days_back: int = 7
    ) -> List[Activity]:
        """Sync activities for a user (incremental sync)"""
        try:
            # Calculate start date for sync
            start_date = datetime.now() - timedelta(days=days_back)
            
            # Get last sync date if available
            if user.last_sync_at:
                start_date = max(start_date, user.last_sync_at - timedelta(hours=1))
            
            # Fetch activities from Garmin
            garmin_activities = await self.fetch_user_activities(user, start_date)
            
            synced_activities = []
            
            for garmin_activity in garmin_activities:
                # Check if activity already exists
                garmin_id = str(garmin_activity.get("activityId"))
                existing_activity = (
                    self.db.query(Activity)
                    .filter(Activity.user_id == user.id)
                    .filter(Activity.garmin_activity_id == garmin_id)
                    .first()
                )
                
                if existing_activity:
                    continue  # Skip already synced activities
                
                # Create new activity record
                activity = self._create_activity_from_garmin_data(user, garmin_activity)
                self.db.add(activity)
                synced_activities.append(activity)
            
            # Update user's last sync time
            user.last_sync_at = datetime.utcnow()
            
            # Commit all changes
            self.db.commit()
            
            logger.info(f"Synced {len(synced_activities)} new activities for user {user.email}")
            return synced_activities
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to sync activities for user {user.email}: {e}")
            raise
    
    def _create_activity_from_garmin_data(self, user: User, garmin_data: Dict[str, Any]) -> Activity:
        """Create Activity model from Garmin data"""
        # Extract activity type information
        activity_type_info = garmin_data.get("activityType", {})
        activity_type = "unknown"
        if isinstance(activity_type_info, dict):
            activity_type = activity_type_info.get("typeKey", "unknown")
        elif isinstance(activity_type_info, str):
            activity_type = activity_type_info
        
        # Parse start time
        start_time_str = garmin_data.get("startTimeLocal", "")
        start_time = datetime.utcnow()  # Default fallback
        if start_time_str:
            try:
                # Handle different datetime formats from Garmin
                start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                if start_time.tzinfo:
                    start_time = start_time.replace(tzinfo=None)  # Remove timezone for storage
            except ValueError:
                logger.warning(f"Could not parse start time: {start_time_str}")
        
        # Create activity
        activity = Activity(
            user_id=user.id,
            garmin_activity_id=str(garmin_data.get("activityId", "")),
            activity_type=activity_type,
            activity_name=garmin_data.get("activityName", ""),
            start_time=start_time,
            duration=garmin_data.get("duration"),  # Duration in seconds
            distance=garmin_data.get("distance"),  # Distance in meters
            calories=garmin_data.get("calories"),
            avg_heart_rate=garmin_data.get("averageHR"),
            max_heart_rate=garmin_data.get("maxHR"),
            elevation_gain=garmin_data.get("elevationGain"),
            raw_data=garmin_data,  # Store complete Garmin response
            processed_metrics=self._calculate_processed_metrics(garmin_data)
        )
        
        return activity
    
    def _calculate_processed_metrics(self, garmin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate additional processed metrics from Garmin data"""
        metrics = {}
        
        # Calculate pace (minutes per km) for running activities
        distance = garmin_data.get("distance")
        duration = garmin_data.get("duration")
        
        if distance and duration and distance > 0:
            # Pace in seconds per meter, converted to minutes per km
            pace_sec_per_m = duration / distance
            pace_min_per_km = (pace_sec_per_m * 1000) / 60
            metrics["pace_min_per_km"] = round(pace_min_per_km, 2)
        
        # Calculate average speed in km/h
        if distance and duration and duration > 0:
            speed_ms = distance / duration  # meters per second
            speed_kmh = (speed_ms * 3600) / 1000  # km/h
            metrics["avg_speed_kmh"] = round(speed_kmh, 2)
        
        # Extract training effect if available
        if "aerobicTrainingEffect" in garmin_data:
            metrics["aerobic_training_effect"] = garmin_data["aerobicTrainingEffect"]
        
        if "anaerobicTrainingEffect" in garmin_data:
            metrics["anaerobic_training_effect"] = garmin_data["anaerobicTrainingEffect"]
        
        # Extract VO2 Max if available
        if "vO2MaxValue" in garmin_data:
            metrics["vo2_max"] = garmin_data["vO2MaxValue"]
        
        return metrics
    
    async def sync_all_users(self) -> Dict[str, Any]:
        """Sync activities for all active users"""
        active_users = self.db.query(User).filter(User.is_active == True).all()
        
        results = {
            "total_users": len(active_users),
            "successful_syncs": 0,
            "failed_syncs": 0,
            "total_activities_synced": 0,
            "errors": []
        }
        
        for user in active_users:
            try:
                synced_activities = await self.sync_user_activities(user)
                results["successful_syncs"] += 1
                results["total_activities_synced"] += len(synced_activities)
                
            except Exception as e:
                results["failed_syncs"] += 1
                results["errors"].append({
                    "user_email": user.email,
                    "error": str(e)
                })
                logger.error(f"Failed to sync user {user.email}: {e}")
        
        return results