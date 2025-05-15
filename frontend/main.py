from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import aiohttp
import os
from typing import List
import json

app = FastAPI(title="KoinSera Frontend")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="static")

# Backend API URLs (will be load balanced by Nginx)
BACKEND_URLS = [
    "http://backend-1:8001",
    "http://backend-2:8002"
]

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Главная страница"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/data")
async def get_data():
    """Получить данные через бэкенд API"""
    # Try each backend server until one responds
    for backend_url in BACKEND_URLS:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{backend_url}/api/data") as response:
                    if response.status == 200:
                        return await response.json()
        except:
            continue
    raise HTTPException(status_code=503, detail="No backend servers available")

@app.get("/health")
async def health_check():
    """Проверка работоспособности сервера"""
    return {"status": "healthy"} 