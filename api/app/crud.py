# This file separates the database query logic from the API endpoint logic.

from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas


# ============================= FAN & COMPONENT CRUD =============================

def get_fan_configurations(db: Session) -> List[models.FanConfiguration]:
    """
    Retrieve all fan configurations from the database.
    """
    return db.query(models.FanConfiguration).order_by(models.FanConfiguration.fan_size_mm).all()

def get_fan_configuration(db: Session, fan_config_id: int) -> Optional[models.FanConfiguration]:
    """
    Retrieve a single fan configuration by its primary key ID.
    """
    return db.query(models.FanConfiguration).filter(models.FanConfiguration.id == fan_config_id).first()

def get_available_components(db: Session, fan_config_id: int) -> List[models.Component]:
    """
    Retrieve the components available for a specific fan configuration,
    ordered by the 'order_by' column.
    """
    fan_config = db.query(models.FanConfiguration).filter(models.FanConfiguration.id == fan_config_id).first()

    if not fan_config or not fan_config.available_components:
        return []

    available_ids = fan_config.available_components
    
    return db.query(models.Component).filter(models.Component.id.in_(available_ids)).order_by(models.Component.order_by).all()


# ============================= MOTOR CRUD =============================

def get_motors(db: Session, available_kw: Optional[List[int]] = None, poles: Optional[int] = None, supplier: Optional[str] = None) -> List[schemas.MotorWithLatestPrice]:
    """
    Retrieve motors from the database, with optional filtering.
    Each motor is returned with its most recent price.
    """
    latest_price_subquery = db.query(
        models.MotorPrice.motor_id,
        func.max(models.MotorPrice.date_effective).label('latest_date')
    ).group_by(models.MotorPrice.motor_id).subquery('latest_price_subquery')

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

    if available_kw:
        decimal_kws = [Decimal(kw) for kw in available_kw]
        query = query.filter(models.Motor.rated_output.in_(decimal_kws))

    if poles:
        query = query.filter(models.Motor.poles == poles)

    if supplier:
        query = query.filter(models.Motor.supplier_name.ilike(f"%{supplier}%"))

    results = query.order_by(models.Motor.supplier_name, models.Motor.rated_output).all()

    motors_with_prices = []
    for motor, price in results:
        motor_data = motor.__dict__
        motor_data.update(price.__dict__)
        motor_data['latest_price_date'] = price.date_effective
        motors_with_prices.append(schemas.MotorWithLatestPrice.model_validate(motor_data))

    return motors_with_prices


# ======================= CALCULATION DATA CRUD ========================

def get_materials(db: Session) -> List[models.Material]:
    """
    Fetches all materials from the database.
    """
    return db.query(models.Material).all()

def get_labour_rates(db: Session) -> List[models.LabourRate]:
    """
    Fetches all labour rates from the database.
    """
    return db.query(models.LabourRate).all()

def get_global_settings(db: Session) -> List[models.GlobalSetting]:
    """
    Fetches all global settings from the database.
    """
    return db.query(models.GlobalSetting).all()

def get_rates_and_settings(db: Session) -> dict:
    """
    Fetches all global settings, material costs, and labor rates from the
    database and consolidates them into a single flat dictionary for the
    calculation engine.
    """
    rates = {}

    # 1. Fetch Global Settings
    try:
        global_settings = get_global_settings(db)
        for setting in global_settings:
            value = setting.setting_value
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except (ValueError, TypeError):
                pass
            rates[setting.setting_name] = value
    except Exception:
        pass

    # 2. Fetch Material Costs
    try:
        materials = get_materials(db)
        for material in materials:
            key = f"{material.name.lower().replace(' ', '_').replace('-', '_')}_cost_per_{material.cost_unit}"
            rates[key] = float(material.cost_per_unit)
    except Exception:
        pass

    # 3. Fetch Labour Rates and Calculate Per-KG Rates
    try:
        labour_rates = get_labour_rates(db)
        workday_hours = rates.get('working_hours_per_day', 8) # Default to 8 if not in settings

        for rate in labour_rates:
            # Add the hourly rate
            key_hourly = f"{rate.rate_name.lower().replace('/', '_').replace(' ', '_').replace('-', '_')}_per_hour"
            rates[key_hourly] = float(rate.rate_per_hour)

            # If productivity is available, calculate and add the per-kg rate
            if rate.productivity_kg_per_day and rate.productivity_kg_per_day > 0:
                key_per_kg = f"{rate.rate_name.lower().replace('/', '_').replace(' ', '_').replace('-', '_')}_rate_per_kg"
                rates[key_per_kg] = (float(rate.rate_per_hour) * workday_hours) / float(rate.productivity_kg_per_day)

    except Exception as e:
        print(f"Error processing labour rates: {e}")
        pass

    return rates

def get_parameters_for_calculation(db: Session, fan_config_id: int, component_ids: List[int]) -> List[dict]:
    """
    Retrieves consolidated parameters for a list of components for a specific fan.
    """
    try:
        Comp = models.Component
        CompParam = models.ComponentParameter
        FanCompParam = models.FanComponentParameter
        
        query = db.query(
            Comp.id.label("component_id"),
            Comp.name,
            CompParam.mass_formula_type,
            CompParam.diameter_formula_type,
            CompParam.length_formula_type,
            CompParam.stiffening_formula_type,
            CompParam.default_thickness_mm,
            CompParam.default_fabrication_waste_factor,
            CompParam.length_multiplier,
            FanCompParam.length_mm,
            FanCompParam.stiffening_factor
        ).join(
            CompParam, Comp.id == CompParam.component_id
        ).outerjoin(
            FanCompParam,
            (FanCompParam.component_id == Comp.id) &
            (FanCompParam.fan_configuration_id == fan_config_id)
        ).filter(
            Comp.id.in_(component_ids)
        )
        results = query.all()
        return [dict(row._mapping) for row in results]
    except Exception as e:
        print(f"An error occurred while fetching component parameters: {e}")
        return []
