from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/saved-quotes",
    tags=["saved_quotes"]
)

@router.get("/next-reference")
def get_next_quote_reference(user_initials: Optional[str] = None, db: Session = Depends(get_db)):
    """Get the next available quote reference number.
    
    Args:
        user_initials: Optional initials to use (e.g., 'BV' for Bernard Viviers).
                      If not provided, returns generic pattern.
    
    Returns:
        dict with next_ref and pattern information
    """
    try:
        next_ref = crud.generate_next_quote_ref(db, user_initials)
        return {
            "next_ref": next_ref,
            "pattern": "Q[INITIALS][NUMBER]",
            "example": "QBV0001"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating quote reference: {str(e)}"
        )

@router.get("/validate-reference/{quote_ref}")
def validate_quote_reference(quote_ref: str, db: Session = Depends(get_db)):
    """Check if a quote reference is available (not used by any original quote).
    
    Args:
        quote_ref: The quote reference to validate
    
    Returns:
        dict with is_available flag and suggestion if not available
    """
    try:
        is_available = crud.is_quote_ref_available(db, quote_ref)
        result = {"is_available": is_available, "quote_ref": quote_ref}
        
        if not is_available:
            # Extract initials from the quote_ref to suggest next available
            import re
            match = re.match(r'Q([A-Z]+)', quote_ref)
            initials = match.group(1) if match else None
            suggestion = crud.generate_next_quote_ref(db, initials)
            result["suggestion"] = suggestion
            
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating quote reference: {str(e)}"
        )

@router.post("/", response_model=schemas.Quote)
def create_quote(quote: schemas.QuoteCreate, db: Session = Depends(get_db)):
    """Create a new quote"""
    try:
        return crud.create_quote(db=db, quote=quote)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating quote: {str(e)}"
        )

@router.post("/v3", response_model=schemas.Quote)
def create_v3_quote(quote: schemas.QuoteCreate, db: Session = Depends(get_db)):
    """Create a new quote using v3 schema structure"""
    try:
        return crud.create_v3_quote(db=db, quote=quote)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating v3 quote: {str(e)}"
        )

@router.get("/", response_model=List[schemas.QuoteSummary])
def read_quotes(
    skip: int = 0, 
    limit: int = 100, 
    user_id: Optional[int] = None,
    client_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get a list of quotes with optional filtering"""
    query = db.query(models.Quote)
    
    if user_id:
        query = query.filter(models.Quote.user_id == user_id)
        
    if client_name:
        query = query.filter(models.Quote.client_name.ilike(f"%{client_name}%"))
    
    return query.order_by(models.Quote.creation_date.desc()).offset(skip).limit(limit).all()

@router.get("/{quote_id}", response_model=schemas.Quote)
def read_quote(quote_id: int, db: Session = Depends(get_db)):
    """Get a specific quote by ID"""
    db_quote = crud.get_quote(db, quote_id)
    if db_quote is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    return db_quote

@router.put("/{quote_id}", response_model=schemas.Quote)
def update_quote(quote_id: int, quote_update: schemas.QuoteUpdate, db: Session = Depends(get_db)):
    """Update an existing quote"""
    try:
        updated_quote = crud.update_quote(
            db=db, 
            quote_id=quote_id, 
            quote_data=quote_update.quote_data,
            user_id=quote_update.user_id
        )
        if not updated_quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        return updated_quote
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating quote: {str(e)}"
        )

@router.get("/{quote_ref}/revisions", response_model=List[schemas.QuoteSummary])
def read_quote_revisions(quote_ref: str, db: Session = Depends(get_db)):
    """Get all revisions of a quote by reference"""
    # Get all quotes with this reference
    quotes = db.query(models.Quote).filter(models.Quote.quote_ref == quote_ref).order_by(models.Quote.revision_number).all()
    
    if not quotes:
        raise HTTPException(status_code=404, detail="Quote not found")
        
    return quotes

@router.post("/{quote_id}/revise", response_model=schemas.Quote)
def create_revision(quote_id: int, revision_request: schemas.QuoteRevisionRequest, db: Session = Depends(get_db)):
    """Create a new revision of an existing quote"""
    original_quote = crud.get_quote(db, quote_id)
    if not original_quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Get original parent quote ID
    parent_id = original_quote.original_quote_id or original_quote.id
    
    # Create revision with current quote data
    new_revision = crud.create_quote_revision(
        db=db,
        original_quote_id=parent_id,
        user_id=revision_request.user_id,
        quote_data=original_quote.quote_data
    )
    
    return new_revision

@router.patch("/{quote_id}/status", response_model=schemas.Quote)
def update_status(quote_id: int, status_update: schemas.QuoteStatusUpdate, db: Session = Depends(get_db)):
    """Update the status of a quote"""
    updated_quote = crud.update_quote_status(db, quote_id, status_update.status.value)
    if not updated_quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return updated_quote