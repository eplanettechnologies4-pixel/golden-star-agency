from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fast_api.database import get_db
from ai_chatbot.chain import TravelChatChain

router = APIRouter(prefix="/chatbot", tags=["AI Chatbot"])

@router.post("/message")
def chat_with_bot(message: str, session_id: str, db: Session = Depends(get_db)):
    # Initialize LangChain conversation pipeline
    chain = TravelChatChain(db)
    reply = chain.generate_response(message)
    return {
        "reply": reply,
        "session_id": session_id
    }

