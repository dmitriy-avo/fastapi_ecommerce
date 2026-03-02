from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.db_depends import get_async_db
from app.models.cart_items import CartItem as CartItemModel
from app.models.products import Product as ProductModel
from app.models.users import User as UserModel
from app.schemas import (
    Cart as CartSchema,
    CartItem as CartItemSchema,
    CartItemCreate,
    CartItemUpdate,
)


router = APIRouter(prefix="/cart", tags=["cart"])

async def _ensure_product_available(db: AsyncSession, product_id: int) -> None:
    """
    Эта функция проверяет, что товар с указанным product_id существует в базе данных,
    активен (is_active == True) и доступен для добавления в корзину.
    """
    result = await db.scalars(
        select(ProductModel).where(
            ProductModel.id == product_id,
            ProductModel.is_active == True,
        )
    )
    product = result.first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or inactive",
        )


async def _get_cart_item(
    db: AsyncSession, user_id: int, product_id: int
) -> CartItemModel | None:
    """
    Функция ищет товар в корзине текущего пользователя по product_id.
    В результате работы возвращает объект CartItemModel или None,
    если товар в корзине не найден
    """
    result = await db.scalars(
        select(CartItemModel)
        .options(selectinload(CartItemModel.product))
        .where(
            CartItemModel.user_id == user_id,
            CartItemModel.product_id == product_id,
        )
    )
    return result.first()

@router.get("/", response_model=CartSchema)
async def get_cart(
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Возвращает корзину текущего пользователя,
    загружая все элементы CartItemModel и все товары из корзины пользователя
    одним асинхронным запросом с фильтрацией по user_id и сортировкой по id.
    """
    result = await db.scalars(
        select(CartItemModel)
        .options(selectinload(CartItemModel.product))
        .where(CartItemModel.user_id == current_user.id)
        .order_by(CartItemModel.id)
    )
    items = result.all()

    total_quantity = sum(item.quantity for item in items)
    price_items = (
        Decimal(item.quantity) *
        (item.product.price if item.product.price is not None else Decimal("0"))
        for item in items
    )
    total_price_decimal = sum(price_items, Decimal("0.00"))

    return CartSchema(
        user_id=current_user.id,
        items=items,
        total_quantity=total_quantity,
        total_price=total_price_decimal
    )


@router.post("/items", response_model=CartItemSchema, status_code=status.HTTP_201_CREATED)
async def add_item_to_cart(
    payload: CartItemCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Добавляет товар в корзину пользователя или увеличивает его количество, если он уже есть.
    Сначала через _ensure_product_available мы проверяем существование и доступность товара по product_id.
    Затем через _get_cart_item ищем существующую запись в корзине по user_id и product_id.
    Если запись найдена, то количество товара увеличивается на значение из payload.quantity,
    иначе создаётся новый объект CartItemModel и добавляется через db.add().
    После commit() и повторного получения обновлённой записи (чтобы вернуть актуальные данные),
    возвращается CartItemSchema с кодом 201 Created
    """
    await _ensure_product_available(db, payload.product_id)

    cart_item = await _get_cart_item(db, current_user.id, payload.product_id)
    if cart_item:
        cart_item.quantity += payload.quantity
    else:
        cart_item = CartItemModel(
            user_id=current_user.id,
            product_id=payload.product_id,
            quantity=payload.quantity,
        )
        db.add(cart_item)

    await db.commit()
    updated_item = await _get_cart_item(db, current_user.id, payload.product_id)
    return updated_item

@router.put("/items/{product_id}", response_model=CartItemSchema)
async def update_cart_item(
    product_id: int,
    payload: CartItemUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Обновляет количество товара в корзине пользователя.
    Сначала _ensure_product_available проверяет, что товар с указанным product_id существует и доступен.
    Затем _get_cart_item ищет запись в корзине по user_id и product_id, если её нет,
    то выбрасывается ошибка с кодом ответа 404.
    При наличии записи поле quantity обновляется значением из payload.quantity.
    """
    await _ensure_product_available(db, product_id)

    cart_item = await _get_cart_item(db, current_user.id, product_id)
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    cart_item.quantity = payload.quantity
    await db.commit()
    updated_item = await _get_cart_item(db, current_user.id, product_id)
    return updated_item


@router.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_cart(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Удаляет указанный товар из корзины пользователя.
    Сначала _get_cart_item ищет запись по user_id и product_id, если её нет,
    выбрасывается исключение HTTPException 404.
    При наличии элемента он удаляется через db.delete(cart_item),
    после чего изменения фиксируются вызовом db.commit().
    """
    cart_item = await _get_cart_item(db, current_user.id, product_id)
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    await db.delete(cart_item)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Отвечает за полную очистку корзины.
    С помощью одного SQL-запроса delete(CartItemModel) удаляются все записи,
    где user_id соответствует авторизованному пользователю приславшему запрос.
    """
    await db.execute(delete(CartItemModel).where(CartItemModel.user_id == current_user.id))
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
