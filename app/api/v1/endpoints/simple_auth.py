"""
Simple Authentication Endpoints - No JWT, just session-based auth
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.services.simple_auth_service import auth_service

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    user: dict
    message: str


@router.post("/login", response_model=LoginResponse)
async def simple_login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Simple login - stores user email in session"""
    
    # Authenticate with .env credentials
    user_creds = auth_service.authenticate(request.email, request.password)
    if not user_creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Get user from database
    db_user = db.query(User).filter(User.email == user_creds.email).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in database"
        )
    
    # Set simple session cookie
    response.set_cookie(
        key="user_email", 
        value=user_creds.email,
        httponly=True,
        max_age=86400 * 7  # 7 days
    )
    
    return LoginResponse(
        success=True,
        user={
            "id": str(db_user.id),
            "email": db_user.email,
            "name": db_user.full_name,
            "role": user_creds.role
        },
        message=f"Welcome {user_creds.name}!"
    )


@router.post("/logout")
async def simple_logout(response: Response):
    """Simple logout - clear session cookie"""
    response.delete_cookie("user_email")
    return {"message": "Logged out successfully"}


@router.get("/status")
async def auth_status(request: Request, db: Session = Depends(get_db)):
    """Check authentication status"""
    user_email = request.cookies.get("user_email")
    
    if not user_email:
        return {"authenticated": False, "user": None}
    
    # Verify user still exists and is valid
    user_creds = auth_service.users.get(user_email.lower())
    if not user_creds:
        return {"authenticated": False, "user": None}
    
    db_user = db.query(User).filter(User.email == user_email).first()
    if not db_user:
        return {"authenticated": False, "user": None}
    
    return {
        "authenticated": True,
        "user": {
            "id": str(db_user.id),
            "email": db_user.email,
            "name": db_user.full_name,
            "role": user_creds.role
        }
    }


def get_current_user_simple(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency to get current user from session cookie"""
    user_email = request.cookies.get("user_email")
    
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Verify credentials
    user_creds = auth_service.users.get(user_email.lower())
    if not user_creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )
    
    # Get from database
    db_user = db.query(User).filter(User.email == user_email).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return db_user