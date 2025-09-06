"""
Weekly Digest Service for generating activity summaries and comparisons
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.group import Group, GroupMembership
from app.models.activity import Activity
from app.models.digest import WeeklyDigest

logger = logging.getLogger(__name__)


class DigestService:
    """Service for generating weekly activity digests"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_weekly_digest(self, group_id: str, week_start: datetime = None) -> Dict[str, Any]:
        """Generate weekly digest for a group"""
        try:
            # Get group and members
            group = self.db.query(Group).filter(Group.id == group_id).first()
            if not group:
                raise ValueError(f"Group {group_id} not found")
            
            # Calculate week period
            if week_start is None:
                # Get last Monday
                today = datetime.now()
                week_start = today - timedelta(days=today.weekday())
                week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            
            week_end = week_start + timedelta(days=7)
            
            # Get group members
            members = (
                self.db.query(User)
                .join(GroupMembership)
                .filter(GroupMembership.group_id == group_id)
                .all()
            )
            
            if not members:
                return {"error": "No members in group"}
            
            # Generate digest data
            digest_data = {
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
                "summary": self._generate_group_summary(members, week_start, week_end),
                "leaderboard": self._generate_leaderboard(members, week_start, week_end),
                "member_stats": self._generate_member_stats(members, week_start, week_end),
                "achievements": self._generate_achievements(members, week_start, week_end)
            }
            
            # Store digest in database
            digest_record = WeeklyDigest(
                group_id=group.id,
                week_start=week_start,
                week_end=week_end,
                content=digest_data,
                status="generated"
            )
            
            self.db.add(digest_record)
            self.db.commit()
            self.db.refresh(digest_record)
            
            digest_data["digest_id"] = str(digest_record.id)
            
            logger.info(f"Generated weekly digest for group {group.name} - {len(members)} members")
            return digest_data
            
        except Exception as e:
            logger.error(f"Failed to generate weekly digest: {e}")
            raise
    
    def _generate_group_summary(self, members: List[User], week_start: datetime, week_end: datetime) -> Dict[str, Any]:
        """Generate overall group activity summary"""
        # Get all activities for the week
        activities = (
            self.db.query(Activity)
            .filter(Activity.user_id.in_([member.id for member in members]))
            .filter(Activity.start_time >= week_start)
            .filter(Activity.start_time < week_end)
            .all()
        )
        
        if not activities:
            return {
                "total_activities": 0,
                "total_distance_km": 0,
                "total_duration_hours": 0,
                "total_calories": 0,
                "avg_activities_per_member": 0,
                "most_popular_activity": "None"
            }
        
        # Calculate totals
        total_distance = sum(a.distance_km for a in activities if a.distance_km)
        total_duration = sum(a.duration_minutes for a in activities if a.duration_minutes) / 60  # Convert to hours
        total_calories = sum(a.calories for a in activities if a.calories)
        
        # Activity type popularity
        activity_types = {}
        for activity in activities:
            activity_type = activity.activity_type
            activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
        
        most_popular = max(activity_types.items(), key=lambda x: x[1])[0] if activity_types else "None"
        
        return {
            "total_activities": len(activities),
            "total_distance_km": round(total_distance, 2),
            "total_duration_hours": round(total_duration, 1),
            "total_calories": int(total_calories),
            "avg_activities_per_member": round(len(activities) / len(members), 1),
            "most_popular_activity": most_popular.replace("_", " ").title(),
            "activity_breakdown": {k.replace("_", " ").title(): v for k, v in activity_types.items()}
        }
    
    def _generate_leaderboard(self, members: List[User], week_start: datetime, week_end: datetime) -> Dict[str, Any]:
        """Generate leaderboards for different metrics"""
        member_metrics = {}
        
        for member in members:
            activities = (
                self.db.query(Activity)
                .filter(Activity.user_id == member.id)
                .filter(Activity.start_time >= week_start)
                .filter(Activity.start_time < week_end)
                .all()
            )
            
            total_distance = sum(a.distance_km for a in activities if a.distance_km)
            total_duration = sum(a.duration_minutes for a in activities if a.duration_minutes)
            total_calories = sum(a.calories for a in activities if a.calories)
            total_activities = len(activities)
            
            member_metrics[member.id] = {
                "name": member.full_name,
                "email": member.email,
                "activities": total_activities,
                "distance_km": round(total_distance, 2),
                "duration_minutes": total_duration,
                "calories": int(total_calories)
            }
        
        # Create leaderboards
        leaderboards = {
            "most_active": sorted(
                member_metrics.values(), 
                key=lambda x: x["activities"], 
                reverse=True
            )[:5],
            "longest_distance": sorted(
                member_metrics.values(), 
                key=lambda x: x["distance_km"], 
                reverse=True
            )[:5],
            "most_calories": sorted(
                member_metrics.values(), 
                key=lambda x: x["calories"], 
                reverse=True
            )[:5],
            "most_time": sorted(
                member_metrics.values(), 
                key=lambda x: x["duration_minutes"], 
                reverse=True
            )[:5]
        }
        
        return leaderboards
    
    def _generate_member_stats(self, members: List[User], week_start: datetime, week_end: datetime) -> List[Dict[str, Any]]:
        """Generate individual member statistics"""
        member_stats = []
        
        for member in members:
            activities = (
                self.db.query(Activity)
                .filter(Activity.user_id == member.id)
                .filter(Activity.start_time >= week_start)
                .filter(Activity.start_time < week_end)
                .all()
            )
            
            if not activities:
                member_stats.append({
                    "name": member.full_name,
                    "email": member.email,
                    "activities": 0,
                    "status": "inactive",
                    "message": "No activities this week"
                })
                continue
            
            # Calculate member-specific stats
            total_distance = sum(a.distance_km for a in activities if a.distance_km)
            total_duration = sum(a.duration_minutes for a in activities if a.duration_minutes)
            total_calories = sum(a.calories for a in activities if a.calories)
            
            # Activity breakdown
            activity_types = {}
            for activity in activities:
                activity_type = activity.activity_type.replace("_", " ").title()
                activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
            
            # Determine status
            status = "very_active" if len(activities) >= 5 else "active" if len(activities) >= 2 else "light"
            
            member_stats.append({
                "name": member.full_name,
                "email": member.email,
                "activities": len(activities),
                "distance_km": round(total_distance, 2),
                "duration_hours": round(total_duration / 60, 1),
                "calories": int(total_calories),
                "activity_types": activity_types,
                "status": status,
                "favorite_activity": max(activity_types.items(), key=lambda x: x[1])[0] if activity_types else "None"
            })
        
        return sorted(member_stats, key=lambda x: x["activities"], reverse=True)
    
    def _generate_achievements(self, members: List[User], week_start: datetime, week_end: datetime) -> List[Dict[str, Any]]:
        """Generate achievements and milestones"""
        achievements = []
        
        # Most improved (compare with previous week)
        prev_week_start = week_start - timedelta(days=7)
        prev_week_end = week_start
        
        for member in members:
            current_activities = (
                self.db.query(Activity)
                .filter(Activity.user_id == member.id)
                .filter(Activity.start_time >= week_start)
                .filter(Activity.start_time < week_end)
                .count()
            )
            
            prev_activities = (
                self.db.query(Activity)
                .filter(Activity.user_id == member.id)
                .filter(Activity.start_time >= prev_week_start)
                .filter(Activity.start_time < prev_week_end)
                .count()
            )
            
            if current_activities > prev_activities and current_activities >= 3:
                improvement = current_activities - prev_activities
                achievements.append({
                    "type": "improvement",
                    "member": member.full_name,
                    "description": f"{member.full_name} increased activities by {improvement} this week! 📈",
                    "badge": "🏆"
                })
        
        # Weekly milestones
        for member in members:
            activities = (
                self.db.query(Activity)
                .filter(Activity.user_id == member.id)
                .filter(Activity.start_time >= week_start)
                .filter(Activity.start_time < week_end)
                .all()
            )
            
            if not activities:
                continue
            
            total_distance = sum(a.distance_km for a in activities if a.distance_km)
            total_activities = len(activities)
            
            # Distance milestones
            if total_distance >= 100:
                achievements.append({
                    "type": "distance",
                    "member": member.full_name,
                    "description": f"{member.full_name} covered {total_distance:.1f}km this week! 🚴‍♂️",
                    "badge": "🥇"
                })
            elif total_distance >= 50:
                achievements.append({
                    "type": "distance", 
                    "member": member.full_name,
                    "description": f"{member.full_name} hit {total_distance:.1f}km this week! 🏃‍♂️",
                    "badge": "🥈"
                })
            
            # Activity count milestones
            if total_activities >= 7:
                achievements.append({
                    "type": "consistency",
                    "member": member.full_name, 
                    "description": f"{member.full_name} was active every day this week! ⚡",
                    "badge": "🔥"
                })
            elif total_activities >= 5:
                achievements.append({
                    "type": "consistency",
                    "member": member.full_name,
                    "description": f"{member.full_name} stayed consistent with {total_activities} activities! 💪",
                    "badge": "⭐"
                })
        
        return achievements[:10]  # Limit to top 10 achievements
    
    def format_digest_message(self, digest_data: Dict[str, Any]) -> str:
        """Format digest data into a WhatsApp-friendly message"""
        group = digest_data["group"]
        period = digest_data["period"]
        summary = digest_data["summary"]
        leaderboard = digest_data["leaderboard"]
        achievements = digest_data["achievements"]
        
        message_parts = []
        
        # Header
        message_parts.append(f"🏃‍♂️ *{group['name']} Weekly Digest*")
        message_parts.append(f"📅 Week {period['week_number']} Summary")
        message_parts.append("")
        
        # Group Summary
        message_parts.append("📊 *GROUP SUMMARY*")
        message_parts.append(f"• Total Activities: {summary['total_activities']}")
        message_parts.append(f"• Total Distance: {summary['total_distance_km']}km")
        message_parts.append(f"• Total Time: {summary['total_duration_hours']}h")
        message_parts.append(f"• Total Calories: {summary['total_calories']:,}")
        message_parts.append(f"• Most Popular: {summary['most_popular_activity']}")
        message_parts.append("")
        
        # Top Performers
        if leaderboard["most_active"]:
            message_parts.append("🏆 *TOP PERFORMERS*")
            
            # Most Active
            if leaderboard["most_active"]:
                top_active = leaderboard["most_active"][0]
                message_parts.append(f"🥇 Most Active: {top_active['name']} ({top_active['activities']} activities)")
            
            # Longest Distance
            if leaderboard["longest_distance"]:
                top_distance = leaderboard["longest_distance"][0]
                message_parts.append(f"🥇 Longest Distance: {top_distance['name']} ({top_distance['distance_km']}km)")
            
            # Most Calories
            if leaderboard["most_calories"]:
                top_calories = leaderboard["most_calories"][0]
                message_parts.append(f"🥇 Most Calories: {top_calories['name']} ({top_calories['calories']:,} cal)")
            
            message_parts.append("")
        
        # Achievements
        if achievements:
            message_parts.append("🎉 *ACHIEVEMENTS*")
            for achievement in achievements[:5]:  # Top 5 achievements
                message_parts.append(f"{achievement['badge']} {achievement['description']}")
            message_parts.append("")
        
        # Footer
        message_parts.append("Keep up the great work, everyone! 💪")
        message_parts.append(f"Generated by Garmin Companion System")
        
        return "\n".join(message_parts)