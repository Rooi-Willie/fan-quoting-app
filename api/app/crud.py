# This file separates the database query logic from the API endpoint logic.

from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas
from fastapi import HTTPException
from .validation import validate_quote_data, validate_v3_quote_data


# ===================== NESTED QUOTEDATA SUMMARY EXTRACTION ====================
def _extract_summary_from_quote_data(qd: Dict[str, Any]) -> Dict[str, Any]:
    """Derive summary columns and ensure calculation.derived_totals (nested-only).

    Assumes UI has already migrated/pruned legacy keys. No legacy fallbacks remain.
    Mutates qd in-place to refresh derived_totals.
    """
    if not isinstance(qd, dict):
        return {"fan_uid": None, "fan_size_mm": None, "blade_sets": None, "component_list": [],
                "markup": None, "total_price": None, "motor_supplier": None, "motor_rated_output": None}

    fan = qd.get("fan", {}) or {}
    comps = qd.get("components", {}) or {}
    calc = qd.get("calculation", {}) or {}
    motor = qd.get("motor", {}) or {}
    buyouts = qd.get("buy_out_items", []) or []

    fan_uid = fan.get("uid")
    blade_sets = fan.get("blade_sets")
    component_list = comps.get("selected", []) or []
    markup = calc.get("markup_override")

    motor_selection = motor.get("selection") or {}
    motor_supplier = motor_selection.get("supplier_name") if isinstance(motor_selection, dict) else None
    motor_rated_output = None
    if isinstance(motor_selection, dict) and motor_selection.get("rated_output") is not None:
        motor_rated_output = str(motor_selection.get("rated_output"))

    server_summary = calc.get("server_summary") or {}
    components_final_price = None
    if isinstance(server_summary, dict):
        components_final_price = server_summary.get("final_price") or server_summary.get("total_cost_after_markup")

    motor_final_price = motor.get("final_price")

    buyout_total = 0.0
    if isinstance(buyouts, list):
        for item in buyouts:
            if not isinstance(item, dict):
                continue
            subtotal = item.get("subtotal")
            if subtotal is None:
                unit_cost = item.get("unit_cost") or 0
                qty = item.get("qty") or 0
                subtotal = float(unit_cost) * float(qty)
            buyout_total += float(subtotal or 0)

    total_price = 0.0
    if components_final_price:
        total_price += float(components_final_price)
    if motor_final_price:
        total_price += float(motor_final_price)
    total_price += buyout_total

    derived = {
        "components_final_price": float(components_final_price or 0),
        "motor_final_price": float(motor_final_price or 0),
        "buyout_total": float(buyout_total),
        "grand_total": float(total_price),
    }
    calc.setdefault("derived_totals", {})
    calc["derived_totals"].update(derived)
    qd["calculation"] = calc

    return {
        "fan_uid": fan_uid,
        "fan_size_mm": fan.get("config_size_mm"),
        "blade_sets": blade_sets,
        "component_list": component_list,
        "markup": markup,
        "motor_supplier": motor_supplier,
        "motor_rated_output": motor_rated_output,
        "total_price": float(total_price),
    }

def _extract_summary_from_v3_quote_data(qd: Dict[str, Any]) -> Dict[str, Any]:
    """Extract summary fields from v3 quote_data structure for database storage."""
    if not isinstance(qd, dict):
        return {"fan_uid": None, "fan_size_mm": None, "blade_sets": None, "component_list": [],
                "markup": None, "total_price": None, "motor_supplier": None, "motor_rated_output": None}

    # Extract from v3 structure
    meta = qd.get("meta", {}) or {}
    quote = qd.get("quote", {}) or {}
    spec = qd.get("specification", {}) or {}
    pricing = qd.get("pricing", {}) or {}
    calculations = qd.get("calculations", {}) or {}

    # Fan info from specification (new v3 structure)
    fan_section = spec.get("fan", {}) or {}
    fan_config = fan_section.get("fan_configuration", {}) or {}
    fan_uid = fan_config.get("uid")
    fan_size_mm = fan_config.get("fan_size_mm")
    blade_sets = fan_section.get("blade_sets")

    # Components list
    component_list = [comp.get("component_id") for comp in spec.get("components", []) if comp.get("component_id")]

    # Pricing info
    markup = pricing.get("markup_override")
    
    # Motor info from specification (new v3 structure)
    motor_section = spec.get("motor", {}) or {}
    motor_details = motor_section.get("motor_details", {}) or {}
    motor_supplier = motor_details.get("supplier_name")
    motor_rated_output = str(motor_details.get("rated_output")) if motor_details.get("rated_output") else None

    # Calculate total price from calculations
    component_totals = calculations.get("component_totals", {}) or {}
    motor_calculations = calculations.get("motor", {}) or {}
    buyout_total = sum(item.get("subtotal", 0) for item in pricing.get("buy_out_items", []))

    components_final_price = component_totals.get("final_price", 0)
    motor_final_price = motor_calculations.get("final_price", 0)
    total_price = float(components_final_price) + float(motor_final_price) + float(buyout_total)

    return {
        "fan_uid": fan_uid,
        "fan_size_mm": fan_size_mm,
        "blade_sets": blade_sets,
        "component_list": component_list,
        "markup": markup,
        "motor_supplier": motor_supplier,
        "motor_rated_output": motor_rated_output,
        "total_price": total_price,
    }


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


# ===================== QUOTE & USER CRUD ==========================

# User CRUD operations
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_or_create_user(db: Session, email: str, name: Optional[str] = None):
    user = get_user_by_email(db, email)
    if not user:
        user = create_user(db, schemas.UserCreate(email=email, name=name))
    return user

# Quote CRUD operations
def get_quote(db: Session, quote_id: int):
    return db.query(models.Quote).filter(models.Quote.id == quote_id).first()

def get_quotes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Quote).order_by(models.Quote.creation_date.desc()).offset(skip).limit(limit).all()

def get_quotes_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Quote).filter(models.Quote.user_id == user_id).order_by(models.Quote.creation_date.desc()).offset(skip).limit(limit).all()

def get_quote_revisions(db: Session, original_quote_id: int):
    return db.query(models.Quote).filter(models.Quote.original_quote_id == original_quote_id).order_by(models.Quote.revision_number).all()

def create_quote(db: Session, quote: schemas.QuoteCreate):
    # Mutably enrich quote_data with derived totals & extract summaries
    quote_data = quote.quote_data if isinstance(quote.quote_data, dict) else {}
    # Stage 5: validation (non-blocking for now). Future: raise HTTPException(422,...)
    _validation_issues = validate_quote_data(quote_data)
    if _validation_issues:
        raise HTTPException(status_code=422, detail={"errors": _validation_issues})
    summary_fields = _extract_summary_from_quote_data(quote_data)

    db_quote = models.Quote(
        **quote.dict(exclude={"quote_data"}),
        **summary_fields,
        quote_data=quote_data
    )
    db.add(db_quote)
    db.commit()
    db.refresh(db_quote)
    return db_quote

def create_v3_quote(db: Session, quote: schemas.QuoteCreate):
    """Create quote using v3 schema structure."""
    # Process quote_data for v3 structure
    quote_data = quote.quote_data if isinstance(quote.quote_data, dict) else {}
    
    # Stage 5: validation using v3 validator
    _validation_issues = validate_v3_quote_data(quote_data)
    if _validation_issues:
        raise HTTPException(status_code=422, detail={"errors": _validation_issues})
    
    # Extract summary fields using v3 structure
    summary_fields = _extract_summary_from_v3_quote_data(quote_data)

    db_quote = models.Quote(
        **quote.dict(exclude={"quote_data"}),
        **summary_fields,
        quote_data=quote_data
    )
    db.add(db_quote)
    db.commit()
    db.refresh(db_quote)
    return db_quote

def create_quote_revision(db: Session, original_quote_id: int, user_id: int, quote_data: Dict[str, Any]):
    # Get original quote to copy basic fields
    original_quote = get_quote(db, original_quote_id)
    if not original_quote:
        return None
        
    # Get highest revision number
    existing_revisions = get_quote_revisions(db, original_quote_id)
    next_revision = len(existing_revisions) + 1
    
    # Create revision using the same schema as create_quote but with revision info
    quote_create = schemas.QuoteCreate(
        quote_ref=original_quote.quote_ref,
        client_name=original_quote.client_name,
        project_name=original_quote.project_name,
        project_location=original_quote.project_location,
        quote_data=quote_data,
        user_id=user_id
    )
    
    # Create new quote record with revision information
    # Update quote_data & derive new summary (with validation placeholder)
    quote_data = quote_data if isinstance(quote_data, dict) else {}
    _validation_issues = validate_quote_data(quote_data)
    if _validation_issues:
        raise HTTPException(status_code=422, detail={"errors": _validation_issues})
    summary_fields = _extract_summary_from_quote_data(quote_data)

    db_quote = models.Quote(
        **quote_create.dict(exclude={"quote_data"}),
        original_quote_id=original_quote_id,
        revision_number=next_revision,
        **summary_fields,
        quote_data=quote_data
    )
    
    db.add(db_quote)
    db.commit()
    db.refresh(db_quote)
    return db_quote

def update_quote_status(db: Session, quote_id: int, status: str):
    db_quote = get_quote(db, quote_id)
    if not db_quote:
        return None
    
    db_quote.status = status
    db.commit()
    db.refresh(db_quote)
    return db_quote
