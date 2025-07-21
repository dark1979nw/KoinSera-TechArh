from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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

class BotBase(BaseModel):
    bot_name: str
    bot_token: str
    is_active: bool = True

class BotCreate(BotBase):
    pass

class BotUpdate(BaseModel):
    bot_name: Optional[str] = None
    bot_token: Optional[str] = None
    is_active: Optional[bool] = None

class BotResponse(BotBase):
    bot_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    chat_id: int
    bot_id: int
    bot_name: Optional[str] = None
    user_id: Optional[int] = None
    telegram_chat_id: int
    title: Optional[List[str]] = None
    type_id: int
    status_id: int
    user_num: int
    unknown_user: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatTypeResponse(BaseModel):
    type_id: int
    type_name: str
    class Config:
        from_attributes = True

class ChatStatusResponse(BaseModel):
    status_id: int
    status_name: str
    class Config:
        from_attributes = True

class EmployeeResponse(BaseModel):
    employee_id: int
    full_name: str
    telegram_username: Optional[str] = None
    telegram_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    is_external: bool
    user_id: Optional[int] = None
    is_bot: bool

    class Config:
        from_attributes = True

class EmployeeCreate(BaseModel):
    full_name: str
    telegram_username: Optional[str] = None
    telegram_user_id: Optional[int] = None
    is_active: bool = True
    is_external: bool = True
    is_bot: bool = False

class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    telegram_username: Optional[str] = None
    telegram_user_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_external: Optional[bool] = None
    is_bot: Optional[bool] = None

class ChatCreate(BaseModel):
    bot_id: int
    telegram_chat_id: int
    title: Optional[List[str]] = None
    type_id: int
    status_id: int
    user_num: Optional[int] = 0
    unknown_user: Optional[int] = 0

class ChatUpdate(BaseModel):
    bot_id: Optional[int] = None
    telegram_chat_id: Optional[int] = None
    title: Optional[List[str]] = None
    type_id: Optional[int] = None
    status_id: Optional[int] = None
    user_num: Optional[int] = None
    unknown_user: Optional[int] = None

class UserUpdate(BaseModel):
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    language_code: Optional[str] = None 