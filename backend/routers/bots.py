from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from models import Bot, User
from routers.auth import get_current_user
from schemas import BotCreate, BotUpdate, BotResponse

router = APIRouter(
    prefix="/bots",
    tags=["bots"]
)

@router.get("/", response_model=List[BotResponse])
async def get_bots(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.is_admin:
        return db.query(Bot).all()
    return db.query(Bot).filter(Bot.user_id == current_user.user_id).all()

@router.post("/", response_model=BotResponse)
async def create_bot(
    bot_data: BotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bot = Bot(
        user_id=current_user.user_id,
        bot_name=bot_data.bot_name,
        bot_token=bot_data.bot_token,
        is_active=bot_data.is_active
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot

@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: int,
    bot_data: BotUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bot = db.query(Bot).filter(Bot.bot_id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    if not current_user.is_admin and bot.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if bot_data.bot_name is not None:
        bot.bot_name = bot_data.bot_name
    if bot_data.bot_token is not None:
        bot.bot_token = bot_data.bot_token
    if bot_data.is_active is not None:
        bot.is_active = bot_data.is_active
    
    bot.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(bot)
    return bot

@router.delete("/{bot_id}")
async def delete_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bot = db.query(Bot).filter(Bot.bot_id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    if not current_user.is_admin and bot.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db.delete(bot)
    db.commit()
    return {"message": "Bot deleted successfully"} 