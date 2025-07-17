# This file separates the database query logic from the API endpoint logic.

from sqlalchemy.orm import Session
from . import models, schemas

def get_fan_configurations(db: Session):
    """
    Retrieve all fan configurations from the database.
    """
    return db.query(models.FanConfiguration).order_by(models.FanConfiguration.fan_size_mm).all()

def get_available_components(db: Session, fan_config_id: int):
    """
    Retrieve the components available for a specific fan configuration,
    ordered by the 'order_by' column.
    """
    # First, get the specific fan configuration to find its available component IDs
    fan_config = db.query(models.FanConfiguration).filter(models.FanConfiguration.id == fan_config_id).first()

    if not fan_config or not fan_config.available_components:
        return []

    # Now, query the components table for those IDs
    available_ids = fan_config.available_components
    
    return db.query(models.Component).filter(models.Component.id.in_(available_ids)).order_by(models.Component.order_by).all()