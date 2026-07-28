from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fast_api.database import get_db

router = APIRouter(prefix="/n8n", tags=["n8n Webhook Endpoint"])

@router.get("/sync-data")
def read_only_sync(db: Session = Depends(get_db)):
    return {"status": "ok", "message": "Ready to sync with n8n"}
