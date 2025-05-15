from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models
import database
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="KoinSera Backend API")

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

@app.get("/api/data", response_model=List[DataRecordResponse])
def get_data(db: Session = Depends(database.get_db)):
    """Получить все записи из базы данных"""
    records = db.query(models.DataRecord).all()
    return records

@app.post("/api/data", response_model=DataRecordResponse)
def create_data(record: DataRecordCreate, db: Session = Depends(database.get_db)):
    """Создать новую запись в базе данных"""
    db_record = models.DataRecord(string_data=record.string_data)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@app.get("/health")
def health_check():
    """Проверка работоспособности сервера"""
    return {"status": "healthy"} 