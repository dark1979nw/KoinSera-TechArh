from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import database
from security import verify_password
from pydantic import BaseModel, EmailStr, validator

# Security configuration
SECRET_KEY = "your-secret-key-here"  # TODO: Move to environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    login: str
    password: str
    first_name: str
    last_name: str
    email: EmailStr
    company: Optional[str] = None
    language_code: Optional[str] = None

    @validator('login')
    def validate_login(cls, v):
        if len(v.strip()) < 3 or len(v.strip()) > 50:
            raise ValueError('Login must be between 3 and 50 characters')
        if not v.strip().isalnum():
            raise ValueError('Login must contain only letters and numbers')
        return v.strip()

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        if len(v.strip()) < 1 or len(v.strip()) > 50:
            raise ValueError('Name must be between 1 and 50 characters')
        return v.strip()

    @validator('company')
    def validate_company(cls, v):
        if v and len(v.strip()) > 100:
            raise ValueError('Company name must not exceed 100 characters')
        return v.strip() if v else None

class UserResponse(BaseModel):
    id: int
    login: str
    first_name: str
    last_name: str
    email: str
    company: Optional[str]
    language_code: Optional[str]
    is_admin: bool

    class Config:
        from_attributes = True

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    from models import User  # Import here to avoid circular dependency
    user = db.query(User).filter(User.login == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user = Depends(get_current_user)):
    if current_user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked. Please try again later."
        )
    return current_user

def authenticate_user(db: Session, login: str, password: str):
    from models import User  # Import here to avoid circular dependency
    user = db.query(User).filter(User.login == login).first()
    if not user:
        return None
    if not user.check_password(password):
        user.increment_failed_login()
        db.commit()
        return None
    user.reset_failed_login()
    db.commit()
    return user 