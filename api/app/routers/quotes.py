from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..logic import calculation_engine

router = APIRouter(
    prefix="/quotes",
    tags=["Quotes"]
)

@router.post("/calculate", response_model=schemas.QuoteResponse)
def calculate_quote(request: schemas.QuoteRequest, db: Session = Depends(get_db)):
    """
    Calculates a full quote based on a fan configuration and selected components.

    This endpoint orchestrates the entire calculation process:
    - Fetches all necessary parameters and rates from the database.
    - Resolves formula-based component geometries.
    - Dispatches to the correct calculation logic for each component.
    - Aggregates costs and mass.
    - Applies final markup to produce a final price.
    """
    try:
        quote_response = calculation_engine.calculate_full_quote(db=db, request=request)
        return quote_response
    except ValueError as e:
        # Catch specific, known errors from the engine (e.g., fan not found)
        # and convert them to a user-friendly HTTP error.
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Catch any other unexpected errors during calculation.
        raise HTTPException(status_code=500, detail=f"An internal error occurred during quote calculation: {e}")