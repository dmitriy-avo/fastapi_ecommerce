from fastapi import FastAPI
from app.routers import categories, products


# Создаём приложение FastAPI
app = FastAPI(title="FastAPI Интернет-магазин",
              version="0.1.0")

# Подключаем маршруты категорий и товаров
app.include_router(categories.router)
app.include_router(products.router)


@app.get("/")
async def root():
    '''
    тест работоспособности API
    '''
    return {"message": "Добро пожаловать в API интернет-магазина!"}
