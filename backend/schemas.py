from pydantic import BaseModel
from typing import Optional
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