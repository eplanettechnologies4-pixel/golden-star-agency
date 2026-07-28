from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fast_api.database import get_db

router = APIRouter(prefix="/packages", tags=["Packages"])

@router.get("/")
def list_packages(db: Session = Depends(get_db)):
    return {"message": "List of packages (Hajj, Umrah, Family)"}

@router.get("/{package_id}")
def get_package(package_id: int, db: Session = Depends(get_db)):
    return {"package_id": package_id, "name": "Hajj Special Package"}
