# This is where you define the actual API paths (/fans, etc.).

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/fans",
    tags=["Fans and Components"]
)

@router.get("/", response_model=List[schemas.FanConfiguration])
def read_fan_configurations(db: Session = Depends(get_db)):
    """
    Retrieve a list of all available fan configurations.
    """
    fan_configs = crud.get_fan_configurations(db)
    return fan_configs

@router.get("/{fan_config_id}", response_model=schemas.FanConfiguration)
def read_fan_configuration(fan_config_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single fan configuration by its integer ID.
    """
    db_fan_config = crud.get_fan_configuration(db, fan_config_id=fan_config_id)
    if db_fan_config is None:
        raise HTTPException(status_code=404, detail="Fan configuration not found")
    return db_fan_config

@router.get("/{fan_config_id}/components", response_model=List[schemas.Component])
def read_available_components(fan_config_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a list of components available for a specific fan configuration.
    The list is sorted according to the 'order_by' key.
    """
    components = crud.get_available_components(db, fan_config_id=fan_config_id)
    if not components:
        # This is a bit lenient, you could also raise an HTTPException if the fan_config_id is invalid
        return []
    return components