from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from database import get_db
from models import User
from schemas import UserResponse
from routers.auth import get_current_user
from security import get_password_hash
from pydantic import BaseModel
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

class UserResponse(BaseModel):
    user_id: int
    login: str
    email: str
    first_name: str
    last_name: str
    company: Optional[str] = None
    language_code: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    language_code: Optional[str] = None

async def get_admin_user(current_user: User = Depends(get_current_user)):
    logger.info(f"Checking admin access for user: {current_user.login}")
    if not current_user.is_admin:
        logger.warning(f"User {current_user.login} is not an admin")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    logger.info(f"Admin access granted for user: {current_user.login}")
    return current_user

@router.get("/users", response_model=List[UserResponse])
async def get_users(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Получить список всех пользователей.
    Требуются права администратора.
    """
    logger.info(f"Admin {current_user.login} requested users list")
    users = db.query(User).all()
    logger.info(f"Found {len(users)} users")
    return users

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Обновляем пароль, если он предоставлен
    if user_data.password is not None:
        user.password_hash = get_password_hash(user_data.password)
    
    # Обновляем статус администратора, если он предоставлен
    if user_data.is_admin is not None:
        user.is_admin = user_data.is_admin
    
    # Обновляем статус активности, если он предоставлен
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    db.commit()
    return {"message": "User updated successfully"}

@router.put("/me")
async def update_me(
    user_data: UserUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Валидация пароля
    if user_data.password is not None:
        pwd = user_data.password
        if len(pwd) < 8 or not any(c.isalpha() for c in pwd) or not any(c.isdigit() for c in pwd):
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters and contain both letters and numbers.")
        user.password_hash = get_password_hash(pwd)

    if user_data.email is not None:
        user.email = user_data.email
    if user_data.first_name is not None:
        user.first_name = user_data.first_name
    if user_data.last_name is not None:
        user.last_name = user_data.last_name
    if user_data.company is not None:
        user.company = user_data.company
    if user_data.language_code is not None:
        user.language_code = user_data.language_code

    db.commit()
    db.refresh(user)
    return {"message": "Profile updated successfully"} 