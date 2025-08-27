from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/saved-quotes",
    tags=["saved_quotes"]
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

@router.get("/{quote_ref}/revisions", response_model=List[schemas.QuoteSummary])
def read_quote_revisions(quote_ref: str, db: Session = Depends(get_db)):
    """Get all revisions of a quote by reference"""
    # Get all quotes with this reference
    quotes = db.query(models.Quote).filter(models.Quote.quote_ref == quote_ref).order_by(models.Quote.revision_number).all()
    
    if not quotes:
        raise HTTPException(status_code=404, detail="Quote not found")
        
    return quotes

@router.post("/{quote_id}/revise", response_model=schemas.Quote)
def create_revision(quote_id: int, user_id: int, db: Session = Depends(get_db)):
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
        user_id=user_id,
        quote_data=original_quote.quote_data
    )
    
    return new_revision

@router.patch("/{quote_id}/status", response_model=schemas.Quote)
def update_status(quote_id: int, status: schemas.QuoteStatus, db: Session = Depends(get_db)):
    """Update the status of a quote"""
    updated_quote = crud.update_quote_status(db, quote_id, status)
    if not updated_quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return updated_quote