from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth as auth_router, admin as admin_router
import models
import database
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

app.include_router(auth_router.router, prefix="/api")
app.include_router(admin_router.router, prefix="/api")

@app.get("/health")
def health_check():
    """Проверка работоспособности сервера"""
    return {"status": "healthy"} 
