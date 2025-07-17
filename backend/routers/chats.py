from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from typing import List
from database import get_db
from models import Chat, User
from routers.auth import get_current_user
from schemas import ChatResponse, ChatCreate, ChatUpdate

router = APIRouter(
    prefix="/chats",
    tags=["chats"]
)

@router.get("/", response_model=List[ChatResponse])
async def get_chats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chats = db.query(Chat).options(joinedload(Chat.bot)).filter(Chat.user_id == current_user.user_id).all()
    result = []
    for chat in chats:
        result.append(ChatResponse(
            chat_id=chat.chat_id,
            bot_id=chat.bot_id,
            bot_name=chat.bot.bot_name if chat.bot else None,
            user_id=chat.user_id,
            telegram_chat_id=chat.telegram_chat_id,
            title=chat.title,
            type_id=chat.type_id,
            status_id=chat.status_id,
            user_num=chat.user_num,
            unknown_user=chat.unknown_user,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
        ))
    return result

@router.post("/", response_model=ChatResponse)
async def create_chat(
    chat: ChatCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_chat = Chat(
        bot_id=chat.bot_id,
        telegram_chat_id=chat.telegram_chat_id,
        title=chat.title,
        type_id=chat.type_id,
        status_id=chat.status_id,
        user_num=chat.user_num or 0,
        unknown_user=chat.unknown_user or 0,
        user_id=current_user.user_id
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

@router.put("/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: int,
    chat: ChatUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_chat = db.query(Chat).filter(Chat.chat_id == chat_id, Chat.user_id == current_user.user_id).first()
    if not db_chat:
        return {"error": "Chat not found"}
    for field, value in chat.dict(exclude_unset=True).items():
        setattr(db_chat, field, value)
    db.commit()
    db.refresh(db_chat)
    return db_chat 