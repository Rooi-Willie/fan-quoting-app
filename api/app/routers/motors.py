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