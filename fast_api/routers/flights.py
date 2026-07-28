from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fast_api.database import get_db

router = APIRouter(prefix="/flights", tags=["Flight Quotes"])

@router.post("/quote")
def request_flight_quote(db: Session = Depends(get_db)):
    return {"status": "quote_requested", "quote_id": 456}
