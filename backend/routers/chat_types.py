from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import ChatType
from schemas import ChatTypeResponse

router = APIRouter(prefix="/chat_types", tags=["chat_types"])

@router.get("/", response_model=List[ChatTypeResponse])
async def get_chat_types(db: Session = Depends(get_db)):
    return db.query(ChatType).all() 