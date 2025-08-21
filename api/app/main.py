# We simplify main.py to be the central point that ties everything together.

from fastapi import FastAPI
from .routers import fans, motors, quotes, settings

app = FastAPI(
    title="Fan Quoting API",
    description="API for calculating fan quotes and managing configurations.",
    version="1.0.0"
)

# Include the routers
app.include_router(fans.router)
app.include_router(motors.router)
app.include_router(quotes.router)
app.include_router(settings.router)

@app.get("/", tags=["Root"])
def read_root():
    """A simple health check endpoint."""
    return {"message": "Welcome to the Fan Quoting API!"}