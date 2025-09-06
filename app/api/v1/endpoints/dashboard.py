"""
Public dashboard endpoints for displaying weekly activity data
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.models.activity import Activity
from app.services.digest_service import DigestService

router = APIRouter()


class UserWeeklyStats(BaseModel):
    """User weekly statistics for dashboard"""
    name: str
    email: str
    total_steps: int = 0
    running_distance_km: float = 0.0
    active_calories: int = 0
    total_activities: int = 0
    activities_breakdown: Dict[str, int] = {}
    ytd_total_steps: int = 0
    ytd_running_distance_km: float = 0.0
    ytd_active_calories: int = 0
    ytd_total_activities: int = 0


class WeeklyDashboard(BaseModel):
    """Weekly dashboard data"""
    week_start: str
    week_end: str
    week_number: int
    year: int
    users: List[UserWeeklyStats]
    totals: Dict[str, Any]
    previous_week_comparison: Dict[str, Any] = {}
    monthly_comparison: Dict[str, Any] = {}
    year_to_date_comparison: Dict[str, Any] = {}


class WeeklyDigestSummary(BaseModel):
    """Weekly digest summary for WhatsApp sharing"""
    digest_id: str
    week_start: str
    week_end: str
    group_name: str
    summary: Dict[str, Any]
    formatted_message: str


@router.get("/weekly", response_model=WeeklyDashboard)
async def get_weekly_dashboard(
    week_offset: int = Query(0, description="Weeks back from current week (0 = current week)"),
    db: Session = Depends(get_db)
):
    """Get weekly activity dashboard for all users"""
    
    # Calculate week period
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday() + (week_offset * 7))
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    
    # Get all active users
    users = db.query(User).filter(User.is_active == True).all()
    
    user_stats = []
    totals = {
        "total_steps": 0,
        "total_running_distance": 0.0,
        "total_active_calories": 0,
        "total_activities": 0,
        "active_users": 0
    }
    
    # Calculate YTD period
    year_start = datetime(week_start.year, 1, 1)
    
    for user in users:
        # Get user's activities for the week
        activities = (
            db.query(Activity)
            .filter(Activity.user_id == user.id)
            .filter(Activity.start_time >= week_start)
            .filter(Activity.start_time < week_end)
            .all()
        )
        
        # Get user's YTD activities
        ytd_activities = (
            db.query(Activity)
            .filter(Activity.user_id == user.id)
            .filter(Activity.start_time >= year_start)
            .filter(Activity.start_time < week_end)
            .all()
        )
        
        # Calculate weekly metrics
        total_steps = 0
        running_distance = 0.0
        active_calories = 0
        activities_breakdown = {}
        
        # Calculate YTD metrics
        ytd_total_steps = 0
        ytd_running_distance = 0.0
        ytd_active_calories = 0
        
        # Process weekly activities
        for activity in activities:
            # Extract steps from processed_metrics or raw_data
            if activity.processed_metrics and 'steps' in activity.processed_metrics:
                total_steps += activity.processed_metrics.get('steps', 0)
            elif activity.raw_data and isinstance(activity.raw_data, dict):
                # Try to extract steps from raw Garmin data
                steps = activity.raw_data.get('steps', 0) or activity.raw_data.get('totalSteps', 0)
                total_steps += steps
            
            # Calculate running distance
            if activity.activity_type.lower() in ['running', 'run', 'jogging']:
                running_distance += activity.distance_km if activity.distance_km else 0.0
            
            # Active calories (use calories field or extract from data)
            if activity.calories:
                active_calories += activity.calories
            elif activity.processed_metrics and 'active_calories' in activity.processed_metrics:
                active_calories += activity.processed_metrics.get('active_calories', 0)
            elif activity.raw_data and isinstance(activity.raw_data, dict):
                cal = activity.raw_data.get('calories', 0) or activity.raw_data.get('activeCalories', 0)
                active_calories += cal
            
            # Activity breakdown
            activity_type = activity.activity_type.replace('_', ' ').title()
            activities_breakdown[activity_type] = activities_breakdown.get(activity_type, 0) + 1
        
        # Process YTD activities
        for activity in ytd_activities:
            # Extract YTD steps
            if activity.processed_metrics and 'steps' in activity.processed_metrics:
                ytd_total_steps += activity.processed_metrics.get('steps', 0)
            elif activity.raw_data and isinstance(activity.raw_data, dict):
                steps = activity.raw_data.get('steps', 0) or activity.raw_data.get('totalSteps', 0)
                ytd_total_steps += steps
            
            # Calculate YTD running distance
            if activity.activity_type.lower() in ['running', 'run', 'jogging']:
                ytd_running_distance += activity.distance_km if activity.distance_km else 0.0
            
            # YTD Active calories
            if activity.calories:
                ytd_active_calories += activity.calories
            elif activity.processed_metrics and 'active_calories' in activity.processed_metrics:
                ytd_active_calories += activity.processed_metrics.get('active_calories', 0)
            elif activity.raw_data and isinstance(activity.raw_data, dict):
                cal = activity.raw_data.get('calories', 0) or activity.raw_data.get('activeCalories', 0)
                ytd_active_calories += cal
        
        # If no weekly activities, still create user stat with YTD data
        if not activities:
            user_stat = UserWeeklyStats(
                name=user.full_name,
                email=user.email,
                total_steps=0,
                running_distance_km=0.0,
                active_calories=0,
                total_activities=0,
                activities_breakdown={},
                ytd_total_steps=int(ytd_total_steps),
                ytd_running_distance_km=round(ytd_running_distance, 2),
                ytd_active_calories=int(ytd_active_calories),
                ytd_total_activities=len(ytd_activities)
            )
        else:
            user_stat = UserWeeklyStats(
                name=user.full_name,
                email=user.email,
                total_steps=int(total_steps),
                running_distance_km=round(running_distance, 2),
                active_calories=int(active_calories),
                total_activities=len(activities),
                activities_breakdown=activities_breakdown,
                ytd_total_steps=int(ytd_total_steps),
                ytd_running_distance_km=round(ytd_running_distance, 2),
                ytd_active_calories=int(ytd_active_calories),
                ytd_total_activities=len(ytd_activities)
            )
        
        user_stats.append(user_stat)
        
        # Add to totals
        totals["total_steps"] += user_stat.total_steps
        totals["total_running_distance"] += user_stat.running_distance_km
        totals["total_active_calories"] += user_stat.active_calories
        totals["total_activities"] += user_stat.total_activities
        if user_stat.total_activities > 0:
            totals["active_users"] += 1
    
    # Sort users by total activity (most active first)
    user_stats.sort(key=lambda x: (x.total_activities, x.total_steps, x.active_calories), reverse=True)
    
    # Calculate comparisons
    previous_week_comparison = await _get_week_comparison(db, users, week_start - timedelta(days=7), week_start, totals)
    monthly_comparison = await _get_monthly_comparison(db, users, week_start, totals)
    ytd_comparison = await _get_ytd_comparison(db, users, week_start, totals)
    
    return WeeklyDashboard(
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        week_number=week_start.isocalendar()[1],
        year=week_start.year,
        users=user_stats,
        totals=totals,
        previous_week_comparison=previous_week_comparison,
        monthly_comparison=monthly_comparison,
        year_to_date_comparison=ytd_comparison
    )


@router.get("/digest/latest", response_model=WeeklyDigestSummary)
async def get_latest_digest(
    db: Session = Depends(get_db)
):
    """Get the latest weekly digest for WhatsApp sharing"""
    
    # For now, create a digest for all users as a single group
    # In a real scenario, you'd have proper group management
    
    digest_service = DigestService(db)
    
    # Create a mock group with all active users
    users = db.query(User).filter(User.is_active == True).all()
    
    if not users:
        return WeeklyDigestSummary(
            digest_id="none",
            week_start="",
            week_end="",
            group_name="Garmin Sporters",
            summary={},
            formatted_message="No active users found."
        )
    
    # Calculate current week
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    
    # Generate digest-like data manually since we don't have a real group
    digest_data = {
        "group": {
            "name": "Garmin Sporters",
            "member_count": len(users)
        },
        "period": {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "week_number": week_start.isocalendar()[1]
        },
        "summary": await _generate_group_summary_for_digest(db, users, week_start, week_end),
        "leaderboard": await _generate_leaderboard_for_digest(db, users, week_start, week_end),
        "achievements": []
    }
    
    # Format the message
    formatted_message = _format_digest_message(digest_data)
    
    return WeeklyDigestSummary(
        digest_id=f"weekly_{week_start.strftime('%Y%m%d')}",
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        group_name="Garmin Sporters",
        summary=digest_data["summary"],
        formatted_message=formatted_message
    )


async def _get_week_comparison(db: Session, users: List[User], prev_week_start: datetime, prev_week_end: datetime, current_totals: Dict) -> Dict[str, Any]:
    """Get comparison with previous week"""
    
    prev_activities = (
        db.query(Activity)
        .filter(Activity.user_id.in_([user.id for user in users]))
        .filter(Activity.start_time >= prev_week_start)
        .filter(Activity.start_time < prev_week_end)
        .all()
    )
    
    prev_totals = {
        "total_steps": 0,
        "total_running_distance": 0.0,
        "total_active_calories": 0,
        "total_activities": len(prev_activities)
    }
    
    for activity in prev_activities:
        # Steps
        if activity.processed_metrics and 'steps' in activity.processed_metrics:
            prev_totals["total_steps"] += activity.processed_metrics.get('steps', 0)
        elif activity.raw_data and isinstance(activity.raw_data, dict):
            steps = activity.raw_data.get('steps', 0) or activity.raw_data.get('totalSteps', 0)
            prev_totals["total_steps"] += steps
        
        # Running distance
        if activity.activity_type.lower() in ['running', 'run', 'jogging']:
            prev_totals["total_running_distance"] += activity.distance_km if activity.distance_km else 0.0
        
        # Active calories
        if activity.calories:
            prev_totals["total_active_calories"] += activity.calories
        elif activity.processed_metrics and 'active_calories' in activity.processed_metrics:
            prev_totals["total_active_calories"] += activity.processed_metrics.get('active_calories', 0)
        elif activity.raw_data and isinstance(activity.raw_data, dict):
            cal = activity.raw_data.get('calories', 0) or activity.raw_data.get('activeCalories', 0)
            prev_totals["total_active_calories"] += cal
    
    # Calculate changes
    return {
        "steps_change": current_totals["total_steps"] - prev_totals["total_steps"],
        "running_change_km": round(current_totals["total_running_distance"] - prev_totals["total_running_distance"], 2),
        "calories_change": current_totals["total_active_calories"] - prev_totals["total_active_calories"],
        "activities_change": current_totals["total_activities"] - prev_totals["total_activities"],
        "steps_percent": round(((current_totals["total_steps"] - prev_totals["total_steps"]) / max(prev_totals["total_steps"], 1)) * 100, 1),
        "running_percent": round(((current_totals["total_running_distance"] - prev_totals["total_running_distance"]) / max(prev_totals["total_running_distance"], 1)) * 100, 1),
        "calories_percent": round(((current_totals["total_active_calories"] - prev_totals["total_active_calories"]) / max(prev_totals["total_active_calories"], 1)) * 100, 1)
    }


async def _get_monthly_comparison(db: Session, users: List[User], current_week_start: datetime, current_totals: Dict) -> Dict[str, Any]:
    """Get comparison with monthly average"""
    
    # Get last 4 weeks of data
    month_start = current_week_start - timedelta(days=28)
    
    month_activities = (
        db.query(Activity)
        .filter(Activity.user_id.in_([user.id for user in users]))
        .filter(Activity.start_time >= month_start)
        .filter(Activity.start_time < current_week_start + timedelta(days=7))
        .all()
    )
    
    # Calculate weekly averages for the month
    monthly_avg = {
        "avg_steps_per_week": 0,
        "avg_running_per_week": 0.0,
        "avg_calories_per_week": 0,
        "avg_activities_per_week": 0
    }
    
    if month_activities:
        total_steps = sum(
            activity.processed_metrics.get('steps', 0) if activity.processed_metrics and 'steps' in activity.processed_metrics
            else (activity.raw_data.get('steps', 0) or activity.raw_data.get('totalSteps', 0)) if activity.raw_data and isinstance(activity.raw_data, dict)
            else 0
            for activity in month_activities
        )
        
        total_running = sum(
            activity.distance_km if activity.distance_km and activity.activity_type.lower() in ['running', 'run', 'jogging'] else 0.0
            for activity in month_activities
        )
        
        total_calories = sum(
            activity.calories if activity.calories
            else activity.processed_metrics.get('active_calories', 0) if activity.processed_metrics and 'active_calories' in activity.processed_metrics
            else (activity.raw_data.get('calories', 0) or activity.raw_data.get('activeCalories', 0)) if activity.raw_data and isinstance(activity.raw_data, dict)
            else 0
            for activity in month_activities
        )
        
        monthly_avg = {
            "avg_steps_per_week": int(total_steps / 4),
            "avg_running_per_week": round(total_running / 4, 2),
            "avg_calories_per_week": int(total_calories / 4),
            "avg_activities_per_week": round(len(month_activities) / 4, 1)
        }
    
    return {
        "monthly_avg": monthly_avg,
        "vs_monthly_avg": {
            "steps_vs_avg": current_totals["total_steps"] - monthly_avg["avg_steps_per_week"],
            "running_vs_avg_km": round(current_totals["total_running_distance"] - monthly_avg["avg_running_per_week"], 2),
            "calories_vs_avg": current_totals["total_active_calories"] - monthly_avg["avg_calories_per_week"],
            "activities_vs_avg": round(current_totals["total_activities"] - monthly_avg["avg_activities_per_week"], 1)
        }
    }


async def _get_ytd_comparison(db: Session, users: List[User], current_week_start: datetime, current_totals: Dict) -> Dict[str, Any]:
    """Get year-to-date comparison"""
    
    year_start = datetime(current_week_start.year, 1, 1)
    weeks_in_year = ((current_week_start - year_start).days // 7) + 1
    
    ytd_activities = (
        db.query(Activity)
        .filter(Activity.user_id.in_([user.id for user in users]))
        .filter(Activity.start_time >= year_start)
        .filter(Activity.start_time < current_week_start + timedelta(days=7))
        .all()
    )
    
    ytd_totals = {
        "total_steps": 0,
        "total_running_distance": 0.0,
        "total_active_calories": 0,
        "total_activities": len(ytd_activities)
    }
    
    for activity in ytd_activities:
        # Steps
        if activity.processed_metrics and 'steps' in activity.processed_metrics:
            ytd_totals["total_steps"] += activity.processed_metrics.get('steps', 0)
        elif activity.raw_data and isinstance(activity.raw_data, dict):
            steps = activity.raw_data.get('steps', 0) or activity.raw_data.get('totalSteps', 0)
            ytd_totals["total_steps"] += steps
        
        # Running distance
        if activity.activity_type.lower() in ['running', 'run', 'jogging']:
            ytd_totals["total_running_distance"] += activity.distance_km if activity.distance_km else 0.0
        
        # Active calories
        if activity.calories:
            ytd_totals["total_active_calories"] += activity.calories
        elif activity.processed_metrics and 'active_calories' in activity.processed_metrics:
            ytd_totals["total_active_calories"] += activity.processed_metrics.get('active_calories', 0)
        elif activity.raw_data and isinstance(activity.raw_data, dict):
            cal = activity.raw_data.get('calories', 0) or activity.raw_data.get('activeCalories', 0)
            ytd_totals["total_active_calories"] += cal
    
    # Calculate weekly averages for the year
    ytd_avg = {
        "avg_steps_per_week": int(ytd_totals["total_steps"] / max(weeks_in_year, 1)),
        "avg_running_per_week": round(ytd_totals["total_running_distance"] / max(weeks_in_year, 1), 2),
        "avg_calories_per_week": int(ytd_totals["total_active_calories"] / max(weeks_in_year, 1)),
        "avg_activities_per_week": round(ytd_totals["total_activities"] / max(weeks_in_year, 1), 1)
    }
    
    return {
        "ytd_totals": ytd_totals,
        "ytd_averages": ytd_avg,
        "current_vs_ytd_avg": {
            "steps_vs_avg": current_totals["total_steps"] - ytd_avg["avg_steps_per_week"],
            "running_vs_avg_km": round(current_totals["total_running_distance"] - ytd_avg["avg_running_per_week"], 2),
            "calories_vs_avg": current_totals["total_active_calories"] - ytd_avg["avg_calories_per_week"],
            "activities_vs_avg": round(current_totals["total_activities"] - ytd_avg["avg_activities_per_week"], 1)
        }
    }


async def _generate_group_summary_for_digest(db: Session, users: List[User], week_start: datetime, week_end: datetime) -> Dict[str, Any]:
    """Generate group summary for digest"""
    
    activities = (
        db.query(Activity)
        .filter(Activity.user_id.in_([user.id for user in users]))
        .filter(Activity.start_time >= week_start)
        .filter(Activity.start_time < week_end)
        .all()
    )
    
    if not activities:
        return {
            "total_activities": 0,
            "total_distance_km": 0,
            "total_steps": 0,
            "total_calories": 0,
            "most_popular_activity": "None"
        }
    
    total_distance = sum(a.distance_km for a in activities if a.distance_km)
    total_calories = sum(a.calories for a in activities if a.calories)
    total_steps = 0
    
    for activity in activities:
        if activity.processed_metrics and 'steps' in activity.processed_metrics:
            total_steps += activity.processed_metrics.get('steps', 0)
        elif activity.raw_data and isinstance(activity.raw_data, dict):
            steps = activity.raw_data.get('steps', 0) or activity.raw_data.get('totalSteps', 0)
            total_steps += steps
    
    activity_types = {}
    for activity in activities:
        activity_type = activity.activity_type
        activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
    
    most_popular = max(activity_types.items(), key=lambda x: x[1])[0] if activity_types else "None"
    
    return {
        "total_activities": len(activities),
        "total_distance_km": round(total_distance, 2),
        "total_steps": int(total_steps),
        "total_calories": int(total_calories),
        "most_popular_activity": most_popular.replace("_", " ").title()
    }


async def _generate_leaderboard_for_digest(db: Session, users: List[User], week_start: datetime, week_end: datetime) -> Dict[str, Any]:
    """Generate leaderboard for digest"""
    
    member_metrics = {}
    
    for user in users:
        activities = (
            db.query(Activity)
            .filter(Activity.user_id == user.id)
            .filter(Activity.start_time >= week_start)
            .filter(Activity.start_time < week_end)
            .all()
        )
        
        total_distance = sum(a.distance_km for a in activities if a.distance_km)
        total_calories = sum(a.calories for a in activities if a.calories)
        total_steps = 0
        
        for activity in activities:
            if activity.processed_metrics and 'steps' in activity.processed_metrics:
                total_steps += activity.processed_metrics.get('steps', 0)
            elif activity.raw_data and isinstance(activity.raw_data, dict):
                steps = activity.raw_data.get('steps', 0) or activity.raw_data.get('totalSteps', 0)
                total_steps += steps
        
        member_metrics[user.id] = {
            "name": user.full_name,
            "activities": len(activities),
            "distance_km": round(total_distance, 2),
            "calories": int(total_calories),
            "steps": int(total_steps)
        }
    
    return {
        "most_active": sorted(member_metrics.values(), key=lambda x: x["activities"], reverse=True)[:3],
        "most_steps": sorted(member_metrics.values(), key=lambda x: x["steps"], reverse=True)[:3],
        "longest_distance": sorted(member_metrics.values(), key=lambda x: x["distance_km"], reverse=True)[:3],
        "most_calories": sorted(member_metrics.values(), key=lambda x: x["calories"], reverse=True)[:3]
    }


def _format_digest_message(digest_data: Dict[str, Any]) -> str:
    """Format digest data into a WhatsApp-friendly message"""
    group = digest_data["group"]
    period = digest_data["period"]
    summary = digest_data["summary"]
    leaderboard = digest_data["leaderboard"]
    
    message_parts = []
    
    # Header
    message_parts.append(f"🏃‍♂️ *{group['name']} Weekly Digest*")
    message_parts.append(f"📅 Week {period['week_number']} Summary")
    message_parts.append("")
    
    # Group Summary
    message_parts.append("📊 *GROUP SUMMARY*")
    message_parts.append(f"• Total Activities: {summary['total_activities']}")
    message_parts.append(f"• Total Steps: {summary['total_steps']:,}")
    message_parts.append(f"• Total Distance: {summary['total_distance_km']}km")
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
        
        # Most Steps
        if leaderboard["most_steps"]:
            top_steps = leaderboard["most_steps"][0]
            message_parts.append(f"👟 Most Steps: {top_steps['name']} ({top_steps['steps']:,} steps)")
        
        # Longest Distance
        if leaderboard["longest_distance"]:
            top_distance = leaderboard["longest_distance"][0]
            message_parts.append(f"🏃 Longest Distance: {top_distance['name']} ({top_distance['distance_km']}km)")
        
        message_parts.append("")
    
    # Footer
    message_parts.append("Keep up the great work, everyone! 💪")
    message_parts.append("Generated by Garmin Companion System")
    
    return "\n".join(message_parts)