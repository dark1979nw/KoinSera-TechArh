import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")  # В продакшене использовать безопасный ключ
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

# CORS settings
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
] 