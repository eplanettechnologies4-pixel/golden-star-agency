from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fast_api.database import get_db

router = APIRouter(prefix="/visa", tags=["Visa Applications"])

@router.get("/countries")
def list_countries(db: Session = Depends(get_db)):
    # In a real app, you would query a VisaType model here
    return {
        "countries": [
            {
                "code": "KSA",
                "name": "Saudi Arabia",
                "flag": "🇸🇦",
                "duration": "90 Days",
                "price": "15,000", # Example
                "img_url": "/static/images/saudi_visa.png"
            },
            {
                "code": "TUR",
                "name": "Turkey",
                "flag": "🇹🇷",
                "duration": "30 Days",
                "price": "12,000",
                "img_url": "/static/images/turkey_visa.png"
            },
            {
                "code": "MAL",
                "name": "Malaysia",
                "flag": "🇲🇾",
                "duration": "90 Days",
                "price": "18,000",
                "img_url": "/static/images/malaysia_visa.png"
            },
            {
                "code": "UAE",
                "name": "UAE",
                "flag": "🇦🇪",
                "duration": "30 Days",
                "price": "20,000",
                "img_url": "/static/images/uae_visa.png"
            }
        ]
    }

@router.post("/apply")
def submit_visa_application(db: Session = Depends(get_db)):
    return {"status": "submitted", "application_id": 987}
