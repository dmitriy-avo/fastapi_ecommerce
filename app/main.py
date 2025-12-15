from fastapi import FastAPI
from app.routers import categories


app = FastAPI(title="FastAPI Интернет-магазин",
              version="0.1.0")

app.include_router(categories.router)

@app.get("/")
async def root():
    '''
    тест работоспособности API
    '''
    return {"message": "Добро пожаловать в API интернет-магазина!"}

