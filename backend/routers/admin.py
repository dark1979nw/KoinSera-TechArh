from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging
from database import get_db
from models import User
from schemas import UserResponse
from routers.auth import get_current_user

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

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