# This file separates the database query logic from the API endpoint logic.

from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, select
from . import models, schemas

def get_fan_configurations(db: Session):
    """
    Retrieve all fan configurations from the database.
    """
    return db.query(models.FanConfiguration).order_by(models.FanConfiguration.fan_size_mm).all()

def get_fan_configuration(db: Session, fan_config_id: int):
    """
    Retrieve a single fan configuration by its primary key ID.
    """
    return db.query(models.FanConfiguration).filter(models.FanConfiguration.id == fan_config_id).first()


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


def get_rates_and_settings(db: Session) -> dict:
    """
    Fetches all global settings, material costs, and labor rates from the
    database and consolidates them into a single flat dictionary for the
    calculation engine.

    NOTE: This function assumes the existence of `GlobalSetting`, `Material`,
    and `LabourRate` models that are not defined in the provided context.
    """
    rates = {}

    # 1. Fetch Global Settings (e.g., steel density, default markup)
    # Handling both the case with and without value_type column
    try:
        global_settings = db.query(models.GlobalSetting).all()
        for setting in global_settings:
            value = setting.setting_value
            # Attempt to convert values to appropriate types based on common settings
            try:
                # For settings known to be numeric, attempt to convert to float
                if setting.setting_name in ['steel_density_kg_m3', 'default_markup']:
                    value = float(value)
                # Add other known numeric settings here as needed
                
                # If model has value_type field, use it (backwards compatibility)
                if hasattr(setting, 'value_type'):
                    if setting.value_type == 'float':
                        value = float(value)
                    elif setting.value_type == 'int':
                        value = int(value)
            except (ValueError, TypeError):
                # Keep as string if conversion fails
                pass
                
            rates[setting.setting_name] = value
    except Exception:
        # Table might not exist yet, proceed without global settings
        pass

    # 2. Fetch Material Costs
    # Assumes a `Material` model with columns: `name` (str, e.g., "Steel S355JR"),
    # `cost_per_unit` (Numeric), and `unit` (str, e.g., "kg").
    try:
        materials = db.query(models.Material).all()
        for material in materials:
            # Creates a key like 'steel_s355jr_cost_per_kg'
            key = f"{material.name.lower().replace(' ', '_').replace('-', '_')}_cost_per_{material.unit}"
            rates[key] = float(material.cost_per_unit)
    except Exception:
        pass # Table might not exist yet

    # 3. Fetch Labour Rates
    # Assumes a `LabourRate` model with `rate_name` (str) and `rate_per_hour` (Numeric).
    # The calculation engine specifically needs a 'labour_per_kg' key.
    try:
        # Fetch the specific rate needed by the calculation engine.
        labour_rate = db.query(models.LabourRate).filter(models.LabourRate.rate_name == "Default Labour Per Kg").first()
        if labour_rate:
            rates['labour_per_kg'] = float(labour_rate.rate_per_hour)
    except Exception:
        pass # Table might not exist yet

    return rates


def get_parameters_for_calculation(db: Session, fan_config_id: int, component_ids: List[int]) -> List[dict]:
    """
    Retrieves consolidated parameters for a list of components for a specific fan.
    It joins `components`, `component_parameters` (for default values), and
    `fan_component_parameters` (for fan-specific overrides). It returns a list
    of flat dictionaries ready for the calculation engine.
    NOTE: This function assumes the existence of `ComponentParameter` and
    `FanComponentParameter` models that are not defined in the provided context.
    """
    try:
        # Define shortcuts for the models for readability
        Comp = models.Component
        CompParam = models.ComponentParameter
        FanCompParam = models.FanComponentParameter
        
        # Construct the query to join the three tables
        query = db.query(
            Comp.id.label("component_id"),
            Comp.name,
            # --- Default parameters from component_parameters ---
            CompParam.mass_formula_type,
            CompParam.diameter_formula_type,
            CompParam.length_formula_type,
            CompParam.stiffening_formula_type,
            CompParam.default_thickness_mm,
            CompParam.default_fabrication_waste_factor,
            CompParam.length_multiplier,
            # --- Fan-specific overrides from fan_component_parameters (can be NULL) ---
            models.FanComponentParameter.length_mm,
            models.FanComponentParameter.stiffening_factor
        ).join(
            CompParam, Comp.id == CompParam.component_id
        ).outerjoin(
            models.FanComponentParameter,
            (models.FanComponentParameter.component_id == Comp.id) &
            (models.FanComponentParameter.fan_configuration_id == fan_config_id)
        ).filter(
            Comp.id.in_(component_ids)
        )
        results = query.all()
        # The query returns a list of Row objects. We convert them to a list of dictionaries.
        # The `_mapping` attribute provides a dict-like view of the row's data.
        return [dict(row._mapping) for row in results]
    except Exception as e:
        # This will likely fail until the ComponentParameter and FanComponentParameter models are defined.
        # In a real application, you would want to log this error.
        print(f"An error occurred while fetching component parameters: {e}")
        return []