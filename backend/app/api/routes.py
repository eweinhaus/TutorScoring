"""
Main API router that aggregates all sub-routers.
"""
from fastapi import APIRouter

from app.api import health, sessions, tutors, matching, upcoming_sessions

# Create main router
router = APIRouter()

# Include sub-routers
router.include_router(health.router, tags=["health"])
router.include_router(sessions.router, tags=["sessions"])
router.include_router(tutors.router, tags=["tutors"])
router.include_router(matching.router, tags=["matching"])
router.include_router(upcoming_sessions.router, tags=["upcoming-sessions"])

