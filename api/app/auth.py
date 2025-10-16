"""
API Authentication Module
Provides API key authentication for FastAPI endpoints
"""

import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional

# API Key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key() -> str:
    """Get API key from environment or Secret Manager"""
    # In production (Cloud Run), this comes from Secret Manager
    api_key = os.getenv("API_KEY")
    
    if not api_key:
        raise RuntimeError("API_KEY environment variable not set")
    
    return api_key


async def verify_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)):
    """
    Verify API key from request header
    
    Usage in routes:
        @app.get("/protected", dependencies=[Depends(verify_api_key)])
        def protected_endpoint():
            ...
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing. Include 'X-API-Key' header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    expected_key = get_api_key()
    
    if api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key


# Optional: Create a dependency that makes API key optional
async def verify_api_key_optional(api_key: Optional[str] = Security(API_KEY_HEADER)):
    """
    Optional API key verification
    Returns True if valid, False if missing/invalid
    """
    if api_key is None:
        return False
    
    try:
        expected_key = get_api_key()
        return api_key == expected_key
    except:
        return False
