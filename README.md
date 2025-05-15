# KoinSera Web Application

Веб-приложение с высокой доступностью и отказоустойчивостью.

## Архитектура

Приложение состоит из следующих компонентов:

- 2 Frontend сервера (FastAPI)
- 2 Backend сервера (FastAPI)
- PostgreSQL Master-Slave репликация (2 инстанса)
- Nginx для балансировки нагрузки

## Требования

- Docker
- Docker Compose
- Python 3.9+

## Запуск приложения

1. Клонировать репозиторий:
```bash
git clone <repository-url>
cd KoinSera-TechArh
```

2. Запустить все сервисы:
```bash
docker-compose up -d
```

Приложение будет доступно по адресу: http://localhost:80

## Структура базы данных

Таблица `data_records`:
- id: SERIAL PRIMARY KEY
- timestamp: TIMESTAMP
- string_data: VARCHAR(255)

## API Endpoints

- GET /api/data - получение всех записей из базы данных
- POST /api/data - добавление новой записи (для тестирования)

## Мониторинг

- Frontend серверы: http://localhost:8081, http://localhost:8082
- Backend серверы: http://localhost:8001, http://localhost:8002
- PostgreSQL Master: localhost:5432
- PostgreSQL Slave: localhost:5433 