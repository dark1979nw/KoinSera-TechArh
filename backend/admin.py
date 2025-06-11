from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import User
from schemas import UserResponse
from auth import get_current_user

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

@router.get("/users", response_model=List[UserResponse])
async def get_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    users = db.query(User).all()
    return users 