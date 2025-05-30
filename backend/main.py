from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import models
import database
import auth
from datetime import timedelta, datetime
from pydantic import BaseModel, EmailStr
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="KoinSera Backend API")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

class DataRecordCreate(BaseModel):
    string_data: str

class DataRecordResponse(BaseModel):
    id: int
    timestamp: datetime
    string_data: str

    class Config:
        from_attributes = True

# Auth endpoints
@app.post("/auth/register", response_model=auth.UserResponse)
def register(user: auth.UserCreate, db: Session = Depends(database.get_db)):
    logger.info(f"Attempting to register user with email: {user.email}")
    
    # Check if user with this email or login already exists
    if db.query(models.User).filter(models.User.email == user.email).first():
        logger.warning(f"Registration failed: Email {user.email} already registered")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    if db.query(models.User).filter(models.User.login == user.login).first():
        logger.warning(f"Registration failed: Login {user.login} already taken")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login already taken"
        )
    
    try:
        # Create new user
        db_user = models.User(
            login=user.login,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            company=user.company,
            language_code=user.language_code or "en"
        )
        db_user.set_password(user.password)
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Successfully registered user: {user.email}")
        return db_user
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to server error"
        )

@app.post("/auth/token", response_model=auth.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    logger.info(f"Login attempt for user: {form_data.username}")
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.login}, expires_delta=access_token_expires
    )
    logger.info(f"Login successful for user: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/health")
def health_check():
    """Проверка работоспособности сервера"""
    return {"status": "healthy"}

@app.get("/auth/me", response_model=auth.UserResponse)
async def get_current_user_info(current_user = Depends(auth.get_current_active_user)):
    """Get current user information"""
    return current_user
