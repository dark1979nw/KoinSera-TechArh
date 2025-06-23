from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import ChatStatus
from schemas import ChatStatusResponse

router = APIRouter(prefix="/chat_statuses", tags=["chat_statuses"])

@router.get("/", response_model=List[ChatStatusResponse])
async def get_chat_statuses(db: Session = Depends(get_db)):
    return db.query(ChatStatus).all() 