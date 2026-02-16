# This file separates the database query logic from the API endpoint logic.

from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas
from fastapi import HTTPException
from .validation import validate_quote_data


# ===================== QUOTEDATA SUMMARY EXTRACTION ====================
def _extract_summary_from_quote_data(qd: Dict[str, Any]) -> Dict[str, Any]:
    """Extract summary fields from quote_data structure for database storage."""
    if not isinstance(qd, dict):
        return {"fan_uid": None, "fan_size_mm": None, "blade_sets": None, "component_list": [],
                "component_markup": None, "motor_markup": None, "total_price": None, "motor_supplier": None, 
                "motor_rated_output": None, "created_by_user_name": None, "last_modified_by_user_name": None}

    # Extract from structure
    meta = qd.get("meta", {}) or {}
    quote = qd.get("quote", {}) or {}
    spec = qd.get("specification", {}) or {}
    pricing = qd.get("pricing", {}) or {}
    calculations = qd.get("calculations", {}) or {}

    # Fan info from specification
    fan_section = spec.get("fan", {}) or {}
    fan_config = fan_section.get("fan_configuration", {}) or {}
    fan_uid = fan_config.get("uid")
    fan_size_mm = fan_config.get("fan_size_mm")
    blade_sets = fan_section.get("blade_sets")

    # Components list - extract name field from component objects
    component_list = [comp.get("name") for comp in spec.get("components", []) if comp.get("name")]

    # Pricing info - extract both component and motor markup
    component_markup = pricing.get("component_markup")
    motor_markup = pricing.get("motor_markup")
    
    # Motor info from specification
    motor_section = spec.get("motor", {}) or {}
    motor_details = motor_section.get("motor_details", {}) or {}
    motor_supplier = motor_details.get("supplier_name")
    motor_rated_output = str(motor_details.get("rated_output")) if motor_details.get("rated_output") else None

    # User info from meta
    created_by_user = meta.get("created_by_user", {}) or {}
    last_modified_by_user = meta.get("last_modified_by_user", {}) or {}
    
    created_by_user_name = created_by_user.get("full_name") or created_by_user.get("username")
    last_modified_by_user_name = last_modified_by_user.get("full_name") or last_modified_by_user.get("username")

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
        "component_markup": component_markup,
        "motor_markup": motor_markup,
        "motor_supplier": motor_supplier,
        "motor_rated_output": motor_rated_output,
        "total_price": total_price,
        "created_by_user_name": created_by_user_name,
        "last_modified_by_user_name": last_modified_by_user_name,
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


def get_motor_supplier_discount(db: Session, supplier_name: str, effective_date: Optional[str] = None) -> Optional[schemas.MotorSupplierDiscount]:
    """
    Retrieve the most recent active discount for a motor supplier.
    
    Args:
        db: Database session
        supplier_name: Name of the motor supplier
        effective_date: Optional date string (ISO format) to query historical discounts.
                       If None, uses current date.
    
    Returns:
        MotorSupplierDiscount schema or None if no discount found
    """
    from datetime import datetime
    
    if effective_date:
        query_date = datetime.fromisoformat(effective_date).date()
    else:
        query_date = datetime.now().date()
    
    # Query for the most recent discount that:
    # 1. Matches the supplier name (case-insensitive)
    # 2. Is active
    # 3. Has an effective date on or before the query date
    discount = db.query(models.MotorSupplierDiscount)\
        .filter(models.MotorSupplierDiscount.supplier_name.ilike(supplier_name))\
        .filter(models.MotorSupplierDiscount.is_active == True)\
        .filter(models.MotorSupplierDiscount.date_effective <= query_date)\
        .order_by(models.MotorSupplierDiscount.date_effective.desc())\
        .first()
    
    if discount:
        return schemas.MotorSupplierDiscount.model_validate(discount)
    return None


# ======================= CALCULATION DATA CRUD ========================

def get_materials(db: Session) -> List[models.Material]:
    """
    Fetches all materials from the database, ordered by id.
    """
    return db.query(models.Material).order_by(models.Material.id).all()

def get_labour_rates(db: Session) -> List[models.LabourRate]:
    """
    Fetches all labour rates from the database, ordered by id.
    """
    return db.query(models.LabourRate).order_by(models.LabourRate.id).all()

def get_global_settings(db: Session) -> List[models.GlobalSetting]:
    """
    Fetches all global settings from the database.
    """
    return db.query(models.GlobalSetting).all()

def get_motor_supplier_discounts(db: Session) -> List[models.MotorSupplierDiscount]:
    """Fetches all motor supplier discount records, ordered by id."""
    return db.query(models.MotorSupplierDiscount).order_by(
        models.MotorSupplierDiscount.id
    ).all()


def _log_audit(db: Session, table_name: str, record_id: str, field_name: str,
               old_value, new_value, user_id: Optional[int], username: Optional[str]):
    """Helper to create an audit log entry for a settings change."""
    audit = models.SettingsAuditLog(
        table_name=table_name,
        record_id=str(record_id),
        field_name=field_name,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        changed_by_user_id=user_id,
        changed_by_username=username
    )
    db.add(audit)


def update_global_setting(db: Session, setting_name: str, update: schemas.GlobalSettingUpdate,
                          user_id: Optional[int] = None, username: Optional[str] = None) -> Optional[models.GlobalSetting]:
    """Update a global setting value. Validates that the value is a positive number."""
    setting = db.query(models.GlobalSetting).filter(
        models.GlobalSetting.setting_name == setting_name
    ).first()
    if not setting:
        return None

    # Validate: must be a positive number
    try:
        numeric_val = float(update.setting_value)
        if numeric_val <= 0:
            raise ValueError(f"Value must be positive, got {numeric_val}")
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid setting value '{update.setting_value}': must be a positive number. {e}")

    old_value = setting.setting_value
    setting.setting_value = update.setting_value
    _log_audit(db, "global_settings", setting_name, "setting_value", old_value, update.setting_value, user_id, username)
    db.commit()
    db.refresh(setting)
    return setting


def update_labour_rate(db: Session, rate_id: int, update: schemas.LabourRateUpdate,
                       user_id: Optional[int] = None, username: Optional[str] = None) -> Optional[models.LabourRate]:
    """Update rate_per_hour and productivity_kg_per_day for a labour rate."""
    rate = db.query(models.LabourRate).filter(models.LabourRate.id == rate_id).first()
    if not rate:
        return None

    if update.rate_per_hour <= 0:
        raise ValueError(f"rate_per_hour must be positive, got {update.rate_per_hour}")
    if update.productivity_kg_per_day is not None and update.productivity_kg_per_day <= 0:
        raise ValueError(f"productivity_kg_per_day must be positive or null, got {update.productivity_kg_per_day}")

    # Log each changed field (use rate_name for readable audit trail)
    if rate.rate_per_hour != update.rate_per_hour:
        _log_audit(db, "labour_rates", rate.rate_name, "rate_per_hour",
                   rate.rate_per_hour, update.rate_per_hour, user_id, username)
    if rate.productivity_kg_per_day != update.productivity_kg_per_day:
        _log_audit(db, "labour_rates", rate.rate_name, "productivity_kg_per_day",
                   rate.productivity_kg_per_day, update.productivity_kg_per_day, user_id, username)

    rate.rate_per_hour = update.rate_per_hour
    rate.productivity_kg_per_day = update.productivity_kg_per_day
    db.commit()
    db.refresh(rate)
    return rate


def update_material(db: Session, material_id: int, update: schemas.MaterialUpdate,
                    user_id: Optional[int] = None, username: Optional[str] = None) -> Optional[models.Material]:
    """Update cost_per_unit for a material. Validates positive value."""
    material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not material:
        return None

    if update.cost_per_unit <= 0:
        raise ValueError(f"cost_per_unit must be positive, got {update.cost_per_unit}")

    if material.cost_per_unit != update.cost_per_unit:
        _log_audit(db, "materials", material.name, "cost_per_unit",
                   material.cost_per_unit, update.cost_per_unit, user_id, username)

    material.cost_per_unit = update.cost_per_unit
    db.commit()
    db.refresh(material)
    return material


def update_motor_supplier_discount(db: Session, discount_id: int, update: schemas.MotorSupplierDiscountUpdate,
                                   user_id: Optional[int] = None, username: Optional[str] = None) -> Optional[models.MotorSupplierDiscount]:
    """Update discount_percentage for a motor supplier discount. Validates 0-100 range."""
    discount = db.query(models.MotorSupplierDiscount).filter(
        models.MotorSupplierDiscount.id == discount_id
    ).first()
    if not discount:
        return None

    if update.discount_percentage < 0 or update.discount_percentage > 100:
        raise ValueError(f"discount_percentage must be 0-100, got {update.discount_percentage}")

    if float(discount.discount_percentage) != update.discount_percentage:
        _log_audit(db, "motor_supplier_discounts", discount.supplier_name, "discount_percentage",
                   discount.discount_percentage, update.discount_percentage, user_id, username)

    discount.discount_percentage = update.discount_percentage
    db.commit()
    db.refresh(discount)
    return discount


def get_settings_audit_log(db: Session, table_name: Optional[str] = None, limit: int = 50) -> List[models.SettingsAuditLog]:
    """Fetch recent audit log entries, optionally filtered by table name."""
    query = db.query(models.SettingsAuditLog).order_by(models.SettingsAuditLog.changed_at.desc())
    if table_name:
        query = query.filter(models.SettingsAuditLog.table_name == table_name)
    return query.limit(limit).all()


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
            CompParam.cost_formula_type,
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

def is_quote_ref_available(db: Session, quote_ref: str) -> bool:
    """Check if a quote reference is available (not used by any original quote).
    
    Args:
        db: Database session
        quote_ref: The quote reference to check
        
    Returns:
        bool: True if available, False if already exists
    """
    existing = db.query(models.Quote).filter(
        models.Quote.quote_ref == quote_ref,
        models.Quote.original_quote_id == None  # Only check original quotes
    ).first()
    return existing is None

def generate_next_quote_ref(db: Session, user_initials: Optional[str] = None) -> str:
    """Generate the next available quote reference.
    
    Pattern: Q[INITIALS][NUMBER] (e.g., QBV0001)
    
    Args:
        db: Database session
        user_initials: Optional user initials (e.g., 'BV' for Bernard Viviers)
        
    Returns:
        str: Next available quote reference
    """
    import re
    
    # Default to 'Q' if no initials provided
    prefix = f"Q{user_initials}" if user_initials else "Q"
    
    # Query all original quotes (not revisions) with this prefix pattern
    # Use LIKE for pattern matching
    pattern = f"{prefix}%"
    existing_quotes = db.query(models.Quote.quote_ref).filter(
        models.Quote.quote_ref.like(pattern),
        models.Quote.original_quote_id == None  # Only original quotes
    ).all()
    
    # Extract numbers from existing quote refs
    max_number = 0
    for (quote_ref,) in existing_quotes:
        # Extract number from pattern like QBV0001, QBV0002, QBV0001-A, etc.
        match = re.search(r'(\d+)', quote_ref)
        if match:
            number = int(match.group(1))
            max_number = max(max_number, number)
    
    # Generate next number with leading zeros (4 digits)
    next_number = max_number + 1
    next_ref = f"{prefix}{next_number:04d}"
    
    return next_ref

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
    """Create quote using current schema structure."""
    # Process quote_data
    quote_data = quote.quote_data if isinstance(quote.quote_data, dict) else {}
    
    # Validate quote data
    _validation_issues = validate_quote_data(quote_data)
    if _validation_issues:
        raise HTTPException(status_code=422, detail={"errors": _validation_issues})
    
    # Extract summary fields
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

def create_quote_revision(db: Session, original_quote_id: int, user_id: int, quote_data: Dict[str, Any]):
    # Get original quote to copy basic fields
    original_quote = get_quote(db, original_quote_id)
    if not original_quote:
        return None
        
    # Get highest revision number from ALL quotes in this revision chain
    # This includes the original quote AND all its revisions
    max_revision = db.query(func.max(models.Quote.revision_number))\
        .filter(
            (models.Quote.id == original_quote_id) | 
            (models.Quote.original_quote_id == original_quote_id)
        ).scalar()
    
    next_revision = (max_revision or 0) + 1
    
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

def update_quote(
    db: Session,
    quote_id: int,
    quote_data: dict,
    user_id: int
):
    """
    Update an existing quote with new quote data.
    Extracts summary fields from the updated quote_data.
    Note: quote_ref is intentionally NOT updated to maintain revision chain integrity.
    """
    # Get the existing quote
    db_quote = get_quote(db, quote_id)
    if not db_quote:
        return None
    
    # Update the quote_data
    db_quote.quote_data = quote_data
    
    # Extract project information from quote_data
    quote_section = quote_data.get("quote", {}) or {}
    
    # Update project information fields (but NOT quote_ref to preserve revision chain)
    db_quote.client_name = quote_section.get("client")
    db_quote.project_name = quote_section.get("project")
    db_quote.project_location = quote_section.get("location")
    
    # Re-extract summary fields from the updated quote_data
    summary = _extract_summary_from_quote_data(quote_data)
    db_quote.fan_uid = summary.get("fan_uid")
    db_quote.fan_size_mm = summary.get("fan_size_mm")
    db_quote.blade_sets = summary.get("blade_sets")
    db_quote.component_list = summary.get("component_list")
    db_quote.component_markup = summary.get("component_markup")
    db_quote.motor_markup = summary.get("motor_markup")
    db_quote.motor_supplier = summary.get("motor_supplier")
    db_quote.motor_rated_output = summary.get("motor_rated_output")
    db_quote.total_price = summary.get("total_price")
    db_quote.created_by_user_name = summary.get("created_by_user_name")
    db_quote.last_modified_by_user_name = summary.get("last_modified_by_user_name")
    
    # Update the last_modified_by_user_id
    db_quote.last_modified_by_user_id = user_id
    
    # Commit the changes
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


# ============================= USER CRUD OPERATIONS =============================

import bcrypt

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Create a new user with hashed password"""
    hashed_password = hash_password(user.password)
    
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        full_name=user.full_name,
        phone=user.phone,
        department=user.department,
        job_title=user.job_title,
        role=user.role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Get user by username"""
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Get user by email"""
    return db.query(models.User).filter(models.User.email == email).first()


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def list_users(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[models.User]:
    """List all users with pagination"""
    query = db.query(models.User)
    if active_only:
        query = query.filter(models.User.is_active == True)
    return query.offset(skip).limit(limit).all()
