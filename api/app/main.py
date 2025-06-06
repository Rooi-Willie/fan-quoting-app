from fastapi import FastAPI
import os
from dotenv import load_dotenv
from models import FanConfiguration # Import your Pydantic model
from fan_config_data import FAN_CONFIGS, FAN_ID_MAP # Import your fan configuration data

load_dotenv() # To load .env if running locally outside Docker for some reason

# app = FastAPI()
app = FastAPI(
    title="Fan Quoting App API",
    description="API for calculation and retrieval of fan data for the fan quoting app.",
    version="1.0.0",
)

@app.get("/")
async def root():
    db_url = os.getenv("DATABASE_URL", "not_set")
    return {"message": "Hello from Quoting API", "db_url_preview": db_url[:25] + "..." if db_url else "not_set"}

# Add more endpoints later

# --- FastAPI Endpoints ---
# This section defines the API endpoints for retrieving fan configurations.
@app.get("/fan_ids", response_model=List[str], summary="Get all available Fan IDs")
async def get_fan_ids():
    """
    Returns a list of all unique Fan IDs (e.g., 'Ø762-Ø472') available in the configuration.
    This endpoint is ideal for populating the initial dropdown in your Streamlit app,
    allowing the user to choose a fan configuration.
    """
    return list(FAN_ID_MAP.keys())

@app.get("/fan_config/{fan_id}", response_model=FanConfiguration, summary="Get configuration for a specific Fan ID")
async def get_fan_config(fan_id: str):
    """
    Returns the full configuration details for a given Fan ID.
    Once the user selects a Fan ID in Streamlit, your app can call this endpoint
    to retrieve all associated data (blade quantities, motor kW range, diameters, etc.).
    """
    config = FAN_ID_MAP.get(fan_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Fan ID '{fan_id}' not found.")
    return config

# Optional: Endpoints to filter by pole first, then fan ID
@app.get("/poles", response_model=List[str], summary="Get all available Pole types")
async def get_poles():
    """
    Returns a list of all unique Pole types (e.g., '2 Pole', '4 Pole').
    This can be used if you first want the user to select the Pole type.
    """
    # Use a set to get unique values, then convert to list and sort for consistency
    return sorted(list(set(config.pole for config in FAN_CONFIGS)))

@app.get("/fan_ids_by_pole/{pole_type}", response_model=List[str], summary="Get Fan IDs by Pole type")
async def get_fan_ids_by_pole(pole_type: Literal["2 Pole", "4 Pole"]):
    """
    Returns a list of Fan IDs associated with a specific Pole type.
    This is useful if your Streamlit app has a two-step selection process:
    1. User selects Pole type.
    2. Then, the Fan ID dropdown is filtered based on the selected Pole type.
    """
    return [config.fan_id for config in FAN_CONFIGS if config.pole == pole_type]