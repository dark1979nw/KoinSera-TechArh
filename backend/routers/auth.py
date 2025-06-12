from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
import logging

from database import get_db
from models import User
from schemas import UserResponse
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        logger.warning("No token provided")
        raise credentials_exception
    
    try:
        # Убираем префикс "Bearer " если он есть
        if token.startswith("Bearer "):
            token = token[7:]
            logger.info("Removed 'Bearer ' prefix from token")
            
        logger.info(f"Decoding token with SECRET_KEY: {SECRET_KEY[:10]}...")
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            logger.info(f"Token payload: {payload}")
        except JWTError as e:
            logger.error(f"JWT decode error: {str(e)}")
            raise credentials_exception
            
        username: str = payload.get("sub")
        if username is None:
            logger.warning("No username in token payload")
            raise credentials_exception
            
        logger.info(f"Looking for user with login: {username}")
        user = db.query(User).filter(User.login == username).first()
        if user is None:
            logger.warning(f"User not found: {username}")
            raise credentials_exception
            
        if not user.is_active:
            logger.warning(f"Inactive user attempted to access: {username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        logger.info(f"User found: {user.login}, is_admin: {user.is_admin}")
        return user
        
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {str(e)}")
        raise credentials_exception

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    logger.info(f"GET /me request from user: {current_user.login}")
    return current_user

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"Login attempt for user: {form_data.username}")
    user = db.query(User).filter(User.login == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        logger.warning(f"Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.login}, expires_delta=access_token_expires
    )
    logger.info(f"Login successful for user: {user.login}")
    return {"access_token": access_token, "token_type": "bearer"} 