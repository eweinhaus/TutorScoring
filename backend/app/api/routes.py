"""
Main API router that aggregates all sub-routers.
"""
from fastapi import APIRouter

from app.api import health, sessions, tutors

# Create main router
router = APIRouter()

# Include sub-routers
router.include_router(health.router, tags=["health"])
router.include_router(sessions.router, tags=["sessions"])
router.include_router(tutors.router, tags=["tutors"])

