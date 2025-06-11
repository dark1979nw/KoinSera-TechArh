from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserResponse(BaseModel):
    id: int
    login: str
    email: str
    first_name: str
    last_name: str
    company: Optional[str]
    language_code: Optional[str]
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True 