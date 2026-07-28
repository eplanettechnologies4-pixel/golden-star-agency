from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fast_api.database import get_db

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.post("/")
def create_booking(db: Session = Depends(get_db)):
    return {"message": "Booking created successfully"}

@router.get("/{booking_id}")
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    return {"booking_id": booking_id, "status": "pending"}
