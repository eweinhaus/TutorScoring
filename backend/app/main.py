"""
FastAPI application entry point
"""
import logging
import os
from typing import List

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from app.api.routes import router
from app.utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Tutor Quality Scoring API",
    description="API for tutor performance evaluation",
    version="1.0.0"
)

# CORS configuration
# Get allowed origins from environment or use defaults
def get_allowed_origins() -> List[str]:
    """Get allowed CORS origins from environment or defaults."""
    origins_str = os.getenv("CORS_ORIGINS", "")
    if origins_str:
        # Split by comma and strip whitespace
        origins = [origin.strip() for origin in origins_str.split(",")]
    else:
        # Default origins for development and production
        origins = [
            "http://localhost:3000",
            "http://localhost:5173",  # Vite default port
            "https://tutor-scoring-frontend.onrender.com",
        ]
    return origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router, prefix="/api")


# Customize OpenAPI schema to include API key security
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security scheme for API key
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication. Get your API key from environment variables."
        }
    }
    
    # Add security requirement to endpoints that require authentication
    # Check all paths and operations
    for path, path_item in openapi_schema.get("paths", {}).items():
        for method, operation in path_item.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                # Mark endpoints that require auth (sessions, tutors)
                # Skip health endpoint
                if ("/sessions" in path or "/tutors" in path) and "/health" not in path:
                    operation["security"] = [{"ApiKeyAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP {exc.status_code}: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.exception(f"Unhandled exception: {str(exc)} - Path: {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "path": str(request.url.path)
        }
    )


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Tutor Quality Scoring API starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Tutor Quality Scoring API shutting down...")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Tutor Quality Scoring API", "version": "1.0.0"}

