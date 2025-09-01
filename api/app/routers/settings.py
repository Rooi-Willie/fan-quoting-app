from fastapi import APIRouter, Depends
from typing import List, Dict
from sqlalchemy.orm import Session

from .. import schemas, crud
from ..database import get_db

router = APIRouter(
    prefix="/settings",
    tags=["Settings"]
)

@router.get("/global", response_model=Dict[str, str])
def get_global_settings(db: Session = Depends(get_db)):
    """
    Retrieves all global settings as a dictionary.
    
    Returns:
        Dict[str, str]: A dictionary with setting_name: setting_value pairs
    """
    settings = crud.get_global_settings(db)
    
    # Convert to a simple key-value dictionary
    settings_dict = {setting.setting_name: setting.setting_value for setting in settings}
    
    return settings_dict

@router.get("/rates-and-settings", response_model=Dict[str, str])
def get_rates_and_settings(db: Session = Depends(get_db)):
    """
    Retrieves rates and settings as a dictionary.

    Returns:
        Dict[str, str]: A dictionary with key-value pairs for rates and settings
    """
    rates_and_settings = crud.get_rates_and_settings(db)
    return rates_and_settings