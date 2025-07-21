from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from typing import List
from database import get_db
from models import Chat, User, ChatEmployee, Employee
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

@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_chat = db.query(Chat).filter(Chat.chat_id == chat_id, Chat.user_id == current_user.user_id).first()
    if not db_chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    db.delete(db_chat)
    db.commit()
    return {"ok": True}

@router.get("/{chat_id}/participants")
async def get_chat_participants(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверяем, что чат принадлежит пользователю
    chat = db.query(Chat).filter(Chat.chat_id == chat_id, Chat.user_id == current_user.user_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    # Получаем участников через join
    participants = (
        db.query(ChatEmployee, Employee)
        .join(Employee, ChatEmployee.employee_id == Employee.employee_id)
        .filter(ChatEmployee.chat_id == chat_id)
        .all()
    )
    # Формируем ответ
    result = []
    for ce, emp in participants:
        result.append({
            "employee_id": emp.employee_id,
            "full_name": emp.full_name,
            "telegram_username": emp.telegram_username,
            "created_at": emp.created_at,
            "updated_at": emp.updated_at,
            "is_active": emp.is_active,
            "is_external": emp.is_external,
            # из chat_employees
            "is_admin": ce.is_admin,
            "ce_is_active": ce.is_active,
            "ce_updated_at": ce.updated_at,
        })
    return {
        "chat_id": chat.chat_id,
        "chat_title": chat.title[0] if chat.title and isinstance(chat.title, list) else chat.title,
        "participants": result
    }

@router.delete("/{chat_id}/participants/{employee_id}")
async def delete_chat_participant(
    chat_id: int,
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверяем, что чат принадлежит пользователю
    chat = db.query(Chat).filter(Chat.chat_id == chat_id, Chat.user_id == current_user.user_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    ce = db.query(ChatEmployee).filter(ChatEmployee.chat_id == chat_id, ChatEmployee.employee_id == employee_id).first()
    if not ce:
        raise HTTPException(status_code=404, detail="Link not found")
    db.delete(ce)
    db.commit()
    return {"ok": True}

@router.put("/{chat_id}/participants/{employee_id}")
async def update_chat_participant(
    chat_id: int,
    employee_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверяем, что чат принадлежит пользователю
    chat = db.query(Chat).filter(Chat.chat_id == chat_id, Chat.user_id == current_user.user_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    ce = db.query(ChatEmployee).filter(ChatEmployee.chat_id == chat_id, ChatEmployee.employee_id == employee_id).first()
    emp = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not ce or not emp:
        raise HTTPException(status_code=404, detail="Link or employee not found")
    # Обновляем поля связи
    if 'is_admin' in data:
        ce.is_admin = data['is_admin']
    if 'ce_is_active' in data:
        ce.is_active = data['ce_is_active']
    # Обновляем поля сотрудника
    if 'is_active' in data:
        emp.is_active = data['is_active']
    if 'is_external' in data:
        emp.is_external = data['is_external']
    db.commit()
    return {"ok": True} 