from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/buyout-catalog",
    tags=["Buyout Catalog"],
)


@router.get("", response_model=List[schemas.BuyoutCatalogItemResponse])
def get_buyout_catalog(
    manufacturer: Optional[str] = None,
    voltage_v: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Return active buyout catalog items.

    Optionally filter by ``manufacturer`` and/or ``voltage_v`` query parameters.
    Items are ordered by manufacturer, category, voltage, then insertion order.
    """
    return crud.get_buyout_catalog(db, manufacturer=manufacturer, voltage_v=voltage_v)
