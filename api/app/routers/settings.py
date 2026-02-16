from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Optional
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

@router.get("/rates-and-settings")
def get_rates_and_settings(db: Session = Depends(get_db)):
    """
    Retrieves rates and settings as a dictionary.

    Returns:
        Dict: A dictionary with key-value pairs for rates and settings (mixed types)
    """
    rates_and_settings = crud.get_rates_and_settings(db)
    return rates_and_settings


# ===================== LIST ENDPOINTS =====================

@router.get("/labour-rates", response_model=List[schemas.LabourRate])
def get_labour_rates(db: Session = Depends(get_db)):
    """Return all labour rate records."""
    return crud.get_labour_rates(db)


@router.get("/materials", response_model=List[schemas.Material])
def get_materials(db: Session = Depends(get_db)):
    """Return all material cost records."""
    return crud.get_materials(db)


@router.get("/motor-supplier-discounts", response_model=List[schemas.MotorSupplierDiscount])
def get_motor_supplier_discounts(db: Session = Depends(get_db)):
    """Return all motor supplier discount records."""
    return crud.get_motor_supplier_discounts(db)


@router.get("/audit-log", response_model=List[schemas.SettingsAuditLogEntry])
def get_audit_log(
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    limit: int = Query(50, ge=1, le=200, description="Max entries to return"),
    db: Session = Depends(get_db)
):
    """Return recent settings change history."""
    return crud.get_settings_audit_log(db, table_name=table_name, limit=limit)


# ===================== UPDATE ENDPOINTS =====================

@router.patch("/global/{setting_name}", response_model=schemas.GlobalSetting)
def update_global_setting(
    setting_name: str,
    update: schemas.GlobalSettingUpdate,
    user_id: Optional[int] = Query(None, description="ID of the user making the change"),
    username: Optional[str] = Query(None, description="Username of the user making the change"),
    db: Session = Depends(get_db)
):
    """Update a global setting value. Validates that the value is a positive number."""
    try:
        updated = crud.update_global_setting(db, setting_name, update, user_id, username)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Global setting '{setting_name}' not found")
    return updated


@router.patch("/labour-rates/{rate_id}", response_model=schemas.LabourRate)
def update_labour_rate(
    rate_id: int,
    update: schemas.LabourRateUpdate,
    user_id: Optional[int] = Query(None, description="ID of the user making the change"),
    username: Optional[str] = Query(None, description="Username of the user making the change"),
    db: Session = Depends(get_db)
):
    """Update rate_per_hour and productivity_kg_per_day for a labour rate."""
    try:
        updated = crud.update_labour_rate(db, rate_id, update, user_id, username)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Labour rate {rate_id} not found")
    return updated


@router.patch("/materials/{material_id}", response_model=schemas.Material)
def update_material(
    material_id: int,
    update: schemas.MaterialUpdate,
    user_id: Optional[int] = Query(None, description="ID of the user making the change"),
    username: Optional[str] = Query(None, description="Username of the user making the change"),
    db: Session = Depends(get_db)
):
    """Update cost_per_unit for a material. Validates positive value."""
    try:
        updated = crud.update_material(db, material_id, update, user_id, username)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Material {material_id} not found")
    return updated


@router.patch("/motor-supplier-discounts/{discount_id}", response_model=schemas.MotorSupplierDiscount)
def update_motor_supplier_discount(
    discount_id: int,
    update: schemas.MotorSupplierDiscountUpdate,
    user_id: Optional[int] = Query(None, description="ID of the user making the change"),
    username: Optional[str] = Query(None, description="Username of the user making the change"),
    db: Session = Depends(get_db)
):
    """Update discount_percentage for a motor supplier discount. Validates 0-100 range."""
    try:
        updated = crud.update_motor_supplier_discount(db, discount_id, update, user_id, username)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Motor supplier discount {discount_id} not found")
    return updated
