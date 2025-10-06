# This is where you define the API paths for motors.

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/motors",
    tags=["Motors"]
)

@router.get("/", response_model=List[schemas.MotorWithLatestPrice])
def read_motors(
    db: Session = Depends(get_db),
    available_kw: Optional[List[int]] = Query(None, description="A list of kilowatt ratings to filter by (e.g., ?available_kw=22&available_kw=30)."),
    poles: Optional[int] = Query(None, description="The number of motor poles to filter by (e.g., ?poles=2)."),
    supplier: Optional[str] = Query(None, description="The supplier name to filter by (case-insensitive search).")
):
    """
    Retrieve a list of motors with their latest prices, with optional filtering.

    - **available_kw**: Filter motors by a list of specific kilowatt ratings. This is useful for matching motors to a fan configuration's `available_motor_kw`.
    - **poles**: Filter motors by the number of poles (e.g., 2, 4).
    - **supplier**: Filter motors by the supplier's name.
    """
    motors = crud.get_motors(db=db, available_kw=available_kw, poles=poles, supplier=supplier)
    return motors


@router.get("/supplier-discount/{supplier_name}", response_model=Optional[schemas.MotorSupplierDiscount])
def read_motor_supplier_discount(
    supplier_name: str,
    db: Session = Depends(get_db),
    effective_date: Optional[str] = Query(None, description="Optional effective date in ISO format (YYYY-MM-DD)")
):
    """
    Retrieve the most recent active discount for a motor supplier.
    
    - **supplier_name**: The name of the motor supplier
    - **effective_date**: Optional date to query historical discounts (defaults to current date)
    
    Returns the discount percentage and details, or null if no discount exists.
    """
    discount = crud.get_motor_supplier_discount(db=db, supplier_name=supplier_name, effective_date=effective_date)
    return discount