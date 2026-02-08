#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "fastapi>=0.104.1",
#     "uvicorn[standard]>=0.24.0",
#     "garminconnect>=0.2.19",
# ]
# ///
"""
Simple FastAPI server for testing Garmin authentication via web UI.

Usage:
    uv run server.py
    
Then open: http://localhost:8000
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from garminconnect import Garmin
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Garmin Auth Tester",
    description="Test Garmin Connect credentials and view activities",
    version="1.0.0"
)


class AuthTestRequest(BaseModel):
    """Request model for testing authentication"""
    email: str
    password: str
    days: int = 30


class AuthTestResponse(BaseModel):
    """Response model for authentication test"""
    success: bool
    user_name: str = None
    activities: List[Dict[str, Any]] = []
    summary: Dict[str, Any] = None
    error: str = None


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the test UI"""
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        with open(html_path, 'r') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>index.html not found</h1>", status_code=404)


@app.post("/test-auth", response_model=AuthTestResponse)
async def test_garmin_authentication(request: AuthTestRequest):
    """
    Test Garmin Connect authentication and fetch recent activities.
    
    This endpoint does NOT store credentials - it's only for testing.
    """
    
    logger.info(f"Testing authentication for {request.email}")
    
    try:
        # Step 1: Initialize and authenticate
        client = Garmin(request.email, request.password)
        client.login()
        logger.info(f"Authentication successful for {request.email}")
        
        # Step 2: Get user info
        user_name = "User"
        try:
            user_summary = client.get_user_summary(datetime.now().strftime('%Y-%m-%d'))
            user_name = user_summary.get('displayName', 'User')
        except Exception as e:
            logger.warning(f"Could not fetch user summary: {e}")
        
        # Step 3: Fetch activities
        start_date = datetime.now() - timedelta(days=request.days)
        all_activities = client.get_activities(0, 100)
        
        # Filter and format activities
        filtered_activities = []
        total_distance = 0
        total_calories = 0
        total_duration = 0
        
        for activity in all_activities:
            activity_date_str = activity.get("startTimeLocal", "")
            if not activity_date_str:
                continue
                
            try:
                activity_date = datetime.fromisoformat(activity_date_str.replace("Z", "+00:00"))
                activity_date = activity_date.replace(tzinfo=None)
                
                if activity_date >= start_date:
                    # Extract activity details
                    distance_m = activity.get("distance", 0)
                    distance_km = distance_m / 1000 if distance_m else 0
                    duration_s = activity.get("duration", 0)
                    calories = activity.get("calories", 0)
                    
                    # Format for display
                    hours = int(duration_s // 3600)
                    minutes = int((duration_s % 3600) // 60)
                    seconds = int(duration_s % 60)
                    duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if duration_s else "-"
                    
                    filtered_activities.append({
                        "date": activity_date_str[:10],
                        "name": f"{activity.get('activityName', 'Unnamed')} ({activity.get('activityType', {}).get('typeKey', '')})",
                        "distance": f"{distance_km:.2f} km" if distance_km else "-",
                        "duration": duration_str,
                        "calories": f"{calories:,}" if calories else "-"
                    })
                    
                    # Accumulate totals
                    total_distance += distance_km
                    total_calories += calories
                    total_duration += duration_s
                    
            except (ValueError, AttributeError) as e:
                logger.warning(f"Error parsing activity: {e}")
                continue
        
        # Calculate summary
        summary = {
            "total_activities": len(filtered_activities),
            "total_distance_km": round(total_distance, 2),
            "total_calories": total_calories,
            "total_hours": round(total_duration / 3600, 2)
        }
        
        logger.info(f"Successfully fetched {len(filtered_activities)} activities")
        
        return AuthTestResponse(
            success=True,
            user_name=user_name,
            activities=filtered_activities,
            summary=summary
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Authentication failed: {error_msg}")
        
        # Provide helpful error messages
        if "authentication" in error_msg.lower() or "login" in error_msg.lower():
            error_msg = "Invalid email or password. Please verify your Garmin Connect credentials."
        elif "2fa" in error_msg.lower() or "two-factor" in error_msg.lower():
            error_msg = "Two-factor authentication is not supported. Please use an app-specific password."
        
        return AuthTestResponse(
            success=False,
            error=error_msg
        )


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Garmin Auth Tester...")
    print("📱 Open http://localhost:8000 in your browser")
    print("⏹️  Press CTRL+C to stop\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
