from fastapi import FastAPI
from app.routers import categories, products, users, reviews, cart, orders
from fastapi.staticfiles import StaticFiles


# Создаём приложение FastAPI
app = FastAPI(title="FastAPI Интернет-магазин",
              version="0.1.0")

app.mount("/media", StaticFiles(directory="media"), name="media")

# Подключаем маршруты категорий и товаров
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(users.router)
app.include_router(reviews.router)
app.include_router(cart.router)
app.include_router(orders.router)


@app.get("/")
async def root():
    '''
    тест работоспособности API
    '''
    return {"message": "Добро пожаловать в API интернет-магазина!"}
