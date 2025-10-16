"""
Security Middleware
Adds security headers and CORS configuration
"""

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import os


def add_security_middleware(app: FastAPI):
    """
    Add security middleware to FastAPI app
    Includes CORS, security headers, etc.
    """
    
    # Determine environment
    environment = os.getenv("ENVIRONMENT", "development")
    
    # CORS Configuration
    if environment == "production":
        # Production: Only allow Streamlit Cloud
        allowed_origins = [
            "https://*.streamlit.app",
            "https://*.airblowfans.co.za",
        ]
    else:
        # Development: Allow localhost
        allowed_origins = [
            "http://localhost:8501",
            "http://localhost:3000",
            "http://127.0.0.1:8501",
        ]
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        """Add security headers to all responses"""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
    
    return app
