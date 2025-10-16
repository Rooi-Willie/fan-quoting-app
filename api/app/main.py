# We simplify main.py to be the central point that ties everything together.

from fastapi import FastAPI, Depends
from .routers import fans, motors, quotes, settings, saved_quotes
from .middleware import add_security_middleware
from .auth import verify_api_key
from .config import settings as app_settings

app = FastAPI(
    title=app_settings.api_title,
    description=app_settings.api_description,
    version=app_settings.api_version
)

# Add security middleware (CORS, security headers)
app = add_security_middleware(app)

# Include the routers (all protected by API key)
app.include_router(fans.router, dependencies=[Depends(verify_api_key)])
app.include_router(motors.router, dependencies=[Depends(verify_api_key)])
app.include_router(quotes.router, dependencies=[Depends(verify_api_key)])
app.include_router(saved_quotes.router, dependencies=[Depends(verify_api_key)])
app.include_router(settings.router, dependencies=[Depends(verify_api_key)])

@app.get("/", tags=["Root"])
def read_root():
    """A simple health check endpoint (public)"""
    return {"message": "Welcome to the Fan Quoting API!", "version": app_settings.api_version}

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for monitoring (public)"""
    return {
        "status": "healthy",
        "environment": app_settings.environment,
        "version": app_settings.api_version
    }

@app.get("/api/test-db", tags=["Health"], dependencies=[Depends(verify_api_key)])
def test_database():
    """Test database connection (protected)"""
    from .database import SessionLocal
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"database": "connected", "status": "ok"}
    except Exception as e:
        return {"database": "error", "status": "failed", "message": str(e)}