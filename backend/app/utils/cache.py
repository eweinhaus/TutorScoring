"""
Redis caching utilities for performance optimization.
"""
import os
import json
import logging
from typing import Optional, Any
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

# Redis client (lazy initialization)
_redis_client = None


def get_redis_client():
    """Get or create Redis client."""
    global _redis_client
    
    if _redis_client is None:
        try:
            import redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            _redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            _redis_client.ping()
            logger.info("Redis cache client initialized")
        except Exception as e:
            logger.warning(f"Redis cache not available: {str(e)}")
            return None
    
    return _redis_client


def get_tutor_score(tutor_id: str) -> Optional[dict]:
    """
    Get cached tutor score.
    
    Args:
        tutor_id: UUID string of the tutor
        
    Returns:
        Cached score dictionary or None if not found
    """
    client = get_redis_client()
    if not client:
        return None
    
    try:
        key = f"tutor_score:{tutor_id}"
        cached = client.get(key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Error getting cached tutor score: {str(e)}")
    
    return None


def set_tutor_score(tutor_id: str, score: dict, ttl: int = 300) -> bool:
    """
    Cache tutor score.
    
    Args:
        tutor_id: UUID string of the tutor
        score: Score dictionary to cache
        ttl: Time to live in seconds (default 5 minutes)
        
    Returns:
        True if cached successfully, False otherwise
    """
    client = get_redis_client()
    if not client:
        return False
    
    try:
        key = f"tutor_score:{tutor_id}"
        client.setex(key, ttl, json.dumps(score, default=str))
        return True
    except Exception as e:
        logger.warning(f"Error caching tutor score: {str(e)}")
    
    return False


def invalidate_tutor_score(tutor_id: str) -> bool:
    """
    Invalidate cached tutor score.
    
    Args:
        tutor_id: UUID string of the tutor
        
    Returns:
        True if invalidated successfully, False otherwise
    """
    client = get_redis_client()
    if not client:
        return False
    
    try:
        key = f"tutor_score:{tutor_id}"
        client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Error invalidating tutor score: {str(e)}")
    
    return False


def invalidate_all_tutor_scores() -> bool:
    """
    Invalidate all cached tutor scores.
    
    Returns:
        True if invalidated successfully, False otherwise
    """
    client = get_redis_client()
    if not client:
        return False
    
    try:
        # Get all keys matching pattern
        keys = client.keys("tutor_score:*")
        if keys:
            client.delete(*keys)
        return True
    except Exception as e:
        logger.warning(f"Error invalidating all tutor scores: {str(e)}")
    
    return False

