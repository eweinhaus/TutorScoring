"""
Authentication middleware for API endpoints.
"""
import os
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(request: Request, api_key: str = Depends(API_KEY_HEADER)) -> bool:
    """
    Verify API key from request header.
    
    Args:
        request: FastAPI request object
        api_key: API key from X-API-Key header
        
    Returns:
        True if API key is valid
        
    Raises:
        HTTPException: 401 Unauthorized if API key is missing or invalid
    """
    expected_api_key = os.getenv("API_KEY")
    
    if not expected_api_key:
        logger.warning("API_KEY environment variable is not set - authentication disabled")
        return True  # Allow if API_KEY not configured (for development)
    
    if not api_key:
        logger.warning("API key missing from request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required. Provide X-API-Key header."
        )
    
    if api_key != expected_api_key:
        logger.warning(f"Invalid API key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return True


def get_api_key(api_key: str = Depends(API_KEY_HEADER)) -> str:
    """
    FastAPI dependency function for API key authentication.
    
    Can be used as: @router.post("/endpoint", dependencies=[Depends(get_api_key)])
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        API key string if valid
        
    Raises:
        HTTPException: 401 Unauthorized if API key is invalid
    """
    expected_api_key = os.getenv("API_KEY")
    
    if not expected_api_key:
        logger.debug("API_KEY not configured - allowing request without authentication")
        return "no-auth"  # Allow if API_KEY not configured
    
    if not api_key:
        logger.warning("API key missing from request headers")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required. Provide X-API-Key header with your API key."
        )
    
    if api_key != expected_api_key:
        logger.warning(f"Invalid API key provided (first 4 chars: {api_key[:4] if len(api_key) > 4 else 'N/A'}...)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    logger.debug("API key validated successfully")
    return api_key

