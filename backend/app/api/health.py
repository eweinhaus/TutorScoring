"""
Health check endpoint.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
import redis
import os
from dotenv import load_dotenv

from app.utils.database import get_db

load_dotenv()

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint that verifies database and Redis connections.
    
    Returns:
        dict: Health status with database and Redis connection status
    """
    status = {
        "status": "healthy",
        "version": "1.0.0",
        "database": "unknown",
        "redis": "unknown"
    }
    
    # Check database connection
    try:
        db.execute(text("SELECT 1"))
        status["database"] = "connected"
    except Exception as e:
        status["database"] = "disconnected"
        status["database_error"] = str(e)
        status["status"] = "unhealthy"
    
    # Check Redis connection
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url, socket_connect_timeout=2)
        redis_client.ping()
        status["redis"] = "connected"
        redis_client.close()
    except Exception as e:
        status["redis"] = "disconnected"
        status["redis_error"] = str(e)
        # Don't mark as unhealthy if only Redis is down (for MVP)
    
    # Return appropriate status code
    if status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=status)
    
    return status

