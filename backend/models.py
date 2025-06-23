from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from security import get_password_hash, verify_password
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import BigInteger

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    login = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(60), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    company = Column(String(100))
    language_code = Column(String(2), ForeignKey('languages.code'))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)

    bots = relationship("Bot", back_populates="user")

    def check_password(self, password: str) -> bool:
        return verify_password(password, self.password_hash)

    def set_password(self, password: str):
        self.password_hash = get_password_hash(password)

    def increment_failed_login(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)

    def reset_failed_login(self):
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = datetime.utcnow()

    def is_locked(self) -> bool:
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False

class Language(Base):
    __tablename__ = "languages"

    code = Column(String(2), primary_key=True)
    name = Column(String(50), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Bot(Base):
    __tablename__ = "bots"

    bot_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    bot_name = Column(String(100), nullable=False)
    bot_token = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="bots")

class Chat(Base):
    __tablename__ = "chats"

    chat_id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey('bots.bot_id'), nullable=False)
    telegram_chat_id = Column(BigInteger, nullable=False, index=True)
    type_id = Column(Integer, nullable=False)
    status_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    title = Column(ARRAY(String(255)), nullable=True)
    user_num = Column(Integer, default=0)
    unknown_user = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)

    bot = relationship("Bot")
    user = relationship("User")

class ChatType(Base):
    __tablename__ = "chat_types"
    type_id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String(50), unique=True, nullable=False)

class ChatStatus(Base):
    __tablename__ = "chat_statuses"
    status_id = Column(Integer, primary_key=True, index=True)
    status_name = Column(String(50), unique=True, nullable=False)

class Employee(Base):
    __tablename__ = "employees"
    employee_id = Column(BigInteger, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    telegram_username = Column(String(255))
    telegram_user_id = Column(BigInteger)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=False)
    is_external = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    is_bot = Column(Boolean, default=False)
