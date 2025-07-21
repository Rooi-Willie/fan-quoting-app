# This file separates the database query logic from the API endpoint logic.

from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
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

def get_motors(db: Session, available_kw: Optional[List[int]] = None, poles: Optional[int] = None, supplier: Optional[str] = None) -> List[schemas.MotorWithLatestPrice]:
    """
    Retrieve motors from the database, with optional filtering.
    Each motor is returned with its most recent price.

    Args:
        db: The database session.
        available_kw: A list of kilowatt ratings to filter by.
        poles: The number of motor poles to filter by.
        supplier: The supplier name to filter by.

    Returns:
        A list of motor objects with their latest prices.
    """
    # Subquery to find the latest effective date for each motor's price
    latest_price_subquery = db.query(
        models.MotorPrice.motor_id,
        func.max(models.MotorPrice.date_effective).label('latest_date')
    ).group_by(models.MotorPrice.motor_id).subquery('latest_price_subquery')

    # Main query to get motors and join their latest price
    query = db.query(
        models.Motor,
        models.MotorPrice
    ).join(
        latest_price_subquery,
        models.Motor.id == latest_price_subquery.c.motor_id
    ).join(
        models.MotorPrice,
        (models.Motor.id == models.MotorPrice.motor_id) &
        (models.MotorPrice.date_effective == latest_price_subquery.c.latest_date)
    )

    # Apply filters
    if available_kw:
        # Convert integer kW values to Decimal for accurate comparison with the NUMERIC column
        decimal_kws = [Decimal(kw) for kw in available_kw]
        query = query.filter(models.Motor.rated_output.in_(decimal_kws))

    if poles:
        query = query.filter(models.Motor.poles == poles)

    if supplier:
        query = query.filter(models.Motor.supplier_name.ilike(f"%{supplier}%")) # Case-insensitive search

    results = query.order_by(models.Motor.supplier_name, models.Motor.rated_output).all()

    # The result is a list of tuples (Motor, MotorPrice). We combine them into our response schema.
    motors_with_prices = []
    for motor, price in results:
        motor_data = motor.__dict__
        motor_data.update(price.__dict__)
        motor_data['latest_price_date'] = price.date_effective # Ensure correct field name mapping
        motors_with_prices.append(schemas.MotorWithLatestPrice.model_validate(motor_data))

    return motors_with_prices