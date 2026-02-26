# 🛒 FastAPI E-commerce API (MVP)

Backend API для  e-commerce проекта на **FastAPI**: JWT-авторизация, роли пользователей, товары, категории, отзывы и миграции Alembic.

## Stack
- FastAPI
- SQLAlchemy 2.0 (async)
- PostgreSQL + asyncpg
- Alembic
- Pydantic
- JWT (OAuth2 Password Flow)

## Features (MVP)
- Auth: регистрация/логин, JWT токены
- Роли: `buyer` / `seller` / `admin`
- Products: CRUD (создание, изменение, удаление только для `seller` и `admin`)
- Categories: CRUD (создание, изменение, удаление только для `admin`)
- Reviews: создание/получение, пересчёт рейтинга товара (создание, изменение, удаление только для `buyer` и `admin`)

## Project structure
```text
fastapi_ecommerce/
│
├── alembic.ini
├── requirements.txt
│
└── app/
    │
    ├── main.py
    ├── auth.py
    ├── config.py
    ├── database.py
    ├── db_depends.py
    ├── schemas.py
    │
    ├── models/
    │   ├── __init__.py
    │   ├── users.py
    │   ├── products.py
    │   ├── categories.py
    │   └── reviews.py
    │
    ├── routers/
    │   ├── users.py
    │   ├── products.py
    │   ├── categories.py
    │   └── reviews.py
    │
    └── migrations/
```
## Run locally
### 1) Install
```text
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
### 2) Environment

Create .env (do not commit it):
```
SECRET_KEY=change_me
```

### 3) Database

Проект настроен на PostgreSQL (см. app/database.py и alembic.ini).

Подними Postgres и создай БД/пользователя (пример):
```
user: ecommerce_user

password: postgres

db: ecommerce_db

Connection string:

postgresql+asyncpg://ecommerce_user:postgres@localhost:5432/ecommerce_db
```
### 4) Migrations
```
alembic upgrade head
```
### 5) Start API
```
uvicorn app.main:app --reload
```

Swagger:
```
http://127.0.0.1:8000/docs
```
