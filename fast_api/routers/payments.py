from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fast_api.database import get_db

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/pay")
def process_payment(db: Session = Depends(get_db)):
    return {"status": "success", "transaction_id": "TXN123456"}
