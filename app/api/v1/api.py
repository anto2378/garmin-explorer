"""
API v1 router configuration
"""

from fastapi import APIRouter

from .endpoints import auth, users, groups, activities, digest, simple_auth, dashboard, whatsapp_digest

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(simple_auth.router, prefix="/simple-auth", tags=["simple-authentication"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(groups.router, prefix="/groups", tags=["groups"])
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])
api_router.include_router(digest.router, prefix="/digest", tags=["digest"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(whatsapp_digest.router, prefix="/whatsapp", tags=["whatsapp"])