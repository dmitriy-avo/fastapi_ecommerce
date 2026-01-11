from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.schemas import Product as ProductSchema, ProductCreate
from app.models.products import Product as ProductModel
from app.models.categories import Category as CategoryModel
from app.db_depends import get_db

router = APIRouter(prefix='/products',
                   tags=['products'], )


@router.get("/", response_model=list[ProductSchema])
async def get_all_products(db: Session = Depends(get_db)):
    """
    Возвращает список всех активных (is_active == True) товаров .
    """
    stmt = select(ProductModel).where(ProductModel.is_active == True)
    all_active_products = db.scalars(stmt).all()
    return all_active_products


@router.post('/', response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Создаёт новый товар.
    """
    # Проверка существования category_id
    category_stmt = select(CategoryModel).where(CategoryModel.id == product.category_id,
                                                CategoryModel.is_active == True)
    category = db.scalars(category_stmt).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Category not found or inactive")

    # создание нового продукта
    db_product = ProductModel(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get('/category/{category_id}', response_model=list[ProductSchema], status_code=status.HTTP_200_OK)
async def get_products_by_category(category_id: int, db: Session = Depends(get_db)):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    # проверка существования и активности category_id
    category_stmt = select(CategoryModel).where(CategoryModel.id == category_id,
                                                CategoryModel.is_active == True)
    category = db.scalars(category_stmt).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Category not found or inactive')
    # Получаем активные товары в категории
    stmt = select(ProductModel).where(ProductModel.category_id == category_id,
                                      ProductModel.is_active == True)
    all_active_products_by_category = db.scalars(stmt).all()
    return all_active_products_by_category


@router.get('/{product_id}')
async def get_product(product_id: int):
    """
    Возвращает детальную информацию о товаре по его ID.
    """
    return {"message": f"Детали товара {product_id} (заглушка)"}


@router.put('/{product_id}')
async def update_product(product_id: int):
    """
    Обновляет товар по его ID.
    """
    return {"message": f"Товар {product_id} обновлён (заглушка)"}


@router.delete('/{product_id}')
async def delete_product(product_id: int):
    """
    Удаляет товар по его ID.
    """
    return {"message": f"Товар {product_id} удалён (заглушка)"}
