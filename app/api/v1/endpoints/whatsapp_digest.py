"""
WhatsApp digest endpoints for generating and sharing weekly activity summaries
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.models.activity import Activity

router = APIRouter()


class WhatsAppDigest(BaseModel):
    """WhatsApp formatted digest"""
    week_start: str
    week_end: str
    week_number: int
    year: int
    message: str
    summary_stats: Dict[str, Any]


@router.get("/weekly", response_model=WhatsAppDigest)
async def get_whatsapp_digest(
    week_offset: int = Query(0, description="Weeks back from current week (0 = current week)"),
    db: Session = Depends(get_db)
):
    """Generate WhatsApp-formatted weekly digest for sharing"""
    
    # Calculate week period
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday() + (week_offset * 7))
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    
    # Get all active users
    users = db.query(User).filter(User.is_active == True).all()
    
    if not users:
        raise HTTPException(status_code=404, detail="No active users found")
    
    # Get all activities for the week
    activities = (
        db.query(Activity)
        .filter(Activity.user_id.in_([user.id for user in users]))
        .filter(Activity.start_time >= week_start)
        .filter(Activity.start_time < week_end)
        .all()
    )
    
    # Generate statistics
    user_stats = {}
    totals = {
        "total_steps": 0,
        "total_running_distance": 0.0,
        "total_active_calories": 0,
        "total_activities": len(activities),
        "active_users": 0
    }
    
    # Process each user's data
    for user in users:
        user_activities = [a for a in activities if a.user_id == user.id]
        
        if not user_activities:
            continue
        
        user_total_steps = 0
        user_running_distance = 0.0
        user_active_calories = 0
        user_activities_breakdown = {}
        
        for activity in user_activities:
            # Extract steps
            if activity.processed_metrics and 'steps' in activity.processed_metrics:
                steps = activity.processed_metrics.get('steps', 0)
            elif activity.raw_data and isinstance(activity.raw_data, dict):
                steps = activity.raw_data.get('steps', 0) or activity.raw_data.get('totalSteps', 0)
            else:
                steps = 0
            user_total_steps += steps
            
            # Calculate running distance
            if activity.activity_type.lower() in ['running', 'run', 'jogging']:
                user_running_distance += activity.distance_km if activity.distance_km else 0.0
            
            # Active calories
            if activity.calories:
                calories = activity.calories
            elif activity.processed_metrics and 'active_calories' in activity.processed_metrics:
                calories = activity.processed_metrics.get('active_calories', 0)
            elif activity.raw_data and isinstance(activity.raw_data, dict):
                calories = activity.raw_data.get('calories', 0) or activity.raw_data.get('activeCalories', 0)
            else:
                calories = 0
            user_active_calories += calories
            
            # Activity breakdown
            activity_type = activity.activity_type.replace('_', ' ').title()
            user_activities_breakdown[activity_type] = user_activities_breakdown.get(activity_type, 0) + 1
        
        user_stats[user.id] = {
            "name": user.full_name,
            "steps": int(user_total_steps),
            "running_km": round(user_running_distance, 2),
            "calories": int(user_active_calories),
            "activities": len(user_activities),
            "activities_breakdown": user_activities_breakdown
        }
        
        # Add to totals
        totals["total_steps"] += user_total_steps
        totals["total_running_distance"] += user_running_distance
        totals["total_active_calories"] += user_active_calories
        totals["active_users"] += 1
    
    # Create leaderboards
    top_performers = _create_leaderboards(user_stats)
    
    # Format WhatsApp message
    message = _format_whatsapp_message(
        week_start, week_end, totals, top_performers, user_stats
    )
    
    return WhatsAppDigest(
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        week_number=week_start.isocalendar()[1],
        year=week_start.year,
        message=message,
        summary_stats={
            "totals": totals,
            "top_performers": top_performers,
            "user_count": len([u for u in user_stats.values() if u["activities"] > 0])
        }
    )


@router.get("/previous-week", response_model=WhatsAppDigest)
async def get_previous_week_digest(
    db: Session = Depends(get_db)
):
    """Get previous week's digest (commonly used for Monday sharing)"""
    return await get_whatsapp_digest(week_offset=1, db=db)


def _create_leaderboards(user_stats: Dict) -> Dict[str, List]:
    """Create leaderboards for different metrics"""
    
    active_users = [stats for stats in user_stats.values() if stats["activities"] > 0]
    
    return {
        "most_active": sorted(active_users, key=lambda x: x["activities"], reverse=True)[:3],
        "most_steps": sorted(active_users, key=lambda x: x["steps"], reverse=True)[:3],
        "longest_running": sorted(active_users, key=lambda x: x["running_km"], reverse=True)[:3],
        "most_calories": sorted(active_users, key=lambda x: x["calories"], reverse=True)[:3]
    }


def _format_whatsapp_message(
    week_start: datetime, 
    week_end: datetime, 
    totals: Dict, 
    top_performers: Dict, 
    user_stats: Dict
) -> str:
    """Format the digest into a WhatsApp-friendly message"""
    
    message_parts = []
    
    # Header with emojis
    message_parts.append("🏃‍♂️ *FAKE SPORTERS WEEKLY DIGEST* 🏃‍♀️")
    message_parts.append(f"📅 Week {week_start.isocalendar()[1]}, {week_start.year}")
    message_parts.append(f"📆 {_format_date_range(week_start, week_end)}")
    message_parts.append("")
    
    # Group Summary
    message_parts.append("📊 *GROUP TOTALS*")
    message_parts.append(f"👟 Total Steps: *{totals['total_steps']:,}*")
    message_parts.append(f"🏃‍♂️ Running Distance: *{totals['total_running_distance']:.1f} km*")
    message_parts.append(f"🔥 Active Calories: *{totals['total_active_calories']:,}*")
    message_parts.append(f"⚡ Total Activities: *{totals['total_activities']}*")
    message_parts.append(f"👥 Active Members: *{totals['active_users']}*")
    message_parts.append("")
    
    # Top Performers
    if top_performers["most_active"]:
        message_parts.append("🏆 *TOP PERFORMERS*")
        
        # Most Active
        if top_performers["most_active"]:
            top = top_performers["most_active"][0]
            message_parts.append(f"🥇 Most Active: *{top['name']}* ({top['activities']} activities)")
        
        # Most Steps  
        if top_performers["most_steps"]:
            top = top_performers["most_steps"][0]
            message_parts.append(f"👟 Most Steps: *{top['name']}* ({top['steps']:,} steps)")
        
        # Longest Running
        if top_performers["longest_running"] and top_performers["longest_running"][0]["running_km"] > 0:
            top = top_performers["longest_running"][0]
            message_parts.append(f"🏃‍♂️ Longest Running: *{top['name']}* ({top['running_km']:.1f} km)")
        
        # Most Calories
        if top_performers["most_calories"]:
            top = top_performers["most_calories"][0]
            message_parts.append(f"🔥 Most Calories: *{top['name']}* ({top['calories']:,} cal)")
        
        message_parts.append("")
    
    # Individual Performance Summary
    active_members = [stats for stats in user_stats.values() if stats["activities"] > 0]
    if active_members:
        message_parts.append("👥 *INDIVIDUAL SUMMARY*")
        
        # Sort by total activities
        sorted_members = sorted(active_members, key=lambda x: x["activities"], reverse=True)
        
        for i, member in enumerate(sorted_members):
            rank_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
            
            # Create activity summary
            activity_summary = []
            if member["steps"] > 0:
                activity_summary.append(f"{member['steps']:,} steps")
            if member["running_km"] > 0:
                activity_summary.append(f"{member['running_km']:.1f}km run")
            if member["calories"] > 0:
                activity_summary.append(f"{member['calories']:,} cal")
            
            summary_text = " • ".join(activity_summary) if activity_summary else "No data"
            
            message_parts.append(f"{rank_emoji} *{member['name']}*: {member['activities']} activities")
            message_parts.append(f"    {summary_text}")
        
        message_parts.append("")
    
    # Motivational footer
    if totals['active_users'] > 0:
        message_parts.append("💪 *Keep up the great work, everyone!*")
    else:
        message_parts.append("💪 *Let's get moving this week!*")
    
    message_parts.append("")
    message_parts.append("📱 View dashboard: nebluda.com/fake-sporters")
    message_parts.append("🤖 Generated by Garmin Companion System")
    
    return "\n".join(message_parts)


def _format_date_range(start: datetime, end: datetime) -> str:
    """Format date range for display"""
    if start.month == end.month:
        return f"{start.strftime('%b %d')} - {end.strftime('%d, %Y')}"
    else:
        return f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"