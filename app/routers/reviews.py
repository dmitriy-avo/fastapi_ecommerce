from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from app.schemas import User as UserSchema
from app.schemas import ReviewResponse as ReviewSchema, ReviewCreate
from app.models.products import Product as ProductModel

from app.models.reviews import Review as ReviewModel

from sqlalchemy.ext.asyncio import AsyncSession
from app.db_depends import get_async_db
from app.auth import require_roles

router = APIRouter(prefix="/reviews", tags=["Reviews"])

async def update_product_rating(db: AsyncSession, product_id: int):
    """
    Пересчитывает средний рейтинг товара на основе активных отзывов.
    """
    result = await db.execute(
        select(func.avg(ReviewModel.grade)).where(
            ReviewModel.product_id == product_id,
            ReviewModel.is_active == True
        )
    )
    avg_rating = result.scalar() or 0.0
    product = await db.get(ProductModel, product_id)
    product.rating = avg_rating
    await db.commit()


@router.get("/", response_model=list[ReviewSchema])
async def get_all_reviews(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех активных отзывов.

    Доступ: публичный.
    Учитываются только отзывы с флагом is_active=True.
    """
    result = await db.scalars(select(ReviewModel).where(ReviewModel.is_active == True))
    reviews = result.all()
    return reviews

@router.get("/products/{product_id}/reviews", response_model=list[ReviewSchema])
async def get_product_reviews(product_id: int,
                              db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список активных отзывов для конкретного товара.

    Параметры:
    - product_id: ID товара
    """
    product_stmt = await db.scalars(select(ProductModel).where(ProductModel.id == product_id,
                                                               ProductModel.is_active == True))
    product_db = product_stmt.first()
    if not product_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    result = await db.scalars(select(ReviewModel).where(ReviewModel.is_active == True,
                                                        ReviewModel.product_id == product_id))
    reviews = result.all()
    return reviews


@router.post("/", response_model=ReviewSchema)
async def create_review(
        review: ReviewCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserSchema = Depends(require_roles("buyer", "admin"))
):
    """
    Создает новый отзыв на товар.

    Доступ: только для пользователей с ролью buyer.

    Ограничения:
    - Пользователь может оставить только один активный отзыв на товар.
    - Товар должен существовать и быть активным.

    После создания автоматически пересчитывается средний рейтинг товара.
    """
    # Проверка товара
    product = await db.get(ProductModel, review.product_id)

    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or inactive"
        )

    # Проверяем что этот пользователь еще не создавал отзыв на этот товар:

    existing_review = await db.scalars(
        select(ReviewModel).where(ReviewModel.is_active == True,
                                  ReviewModel.product_id == product.id,
                                  ReviewModel.user_id == current_user.id))
    if existing_review.one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="You have already reviewed this product")


    # Создание отзыва
    new_review = ReviewModel(**review.model_dump(), user_id=current_user.id)

    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)

    # Пересчёт рейтинга
    await update_product_rating(db, review.product_id)

    return new_review


@router.delete("/{review_id}", response_model=ReviewSchema)
async def delete_review(review_id: int,
                        db: AsyncSession = Depends(get_async_db),
                        current_user: UserSchema = Depends(require_roles("buyer", "admin"))):
    """
    Выполняет мягкое удаление отзыва.
    Доступ: только автор отзыва.
    Логика:
    - Устанавливает is_active=False
    - Пересчитывает рейтинг связанного товара

    Параметры:
    - review_id: ID отзыва
    """
    # 1. Найти отзыв
    review = await db.get(ReviewModel, review_id)

    # 2. Проверка, существует ли отзыв и активен ли (404 если нет)
    if not review or not review.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Review not found or inactive")

    # 3. Проверка прав: current_user.id == review.user_id (автор)
    #    ⚠️ Позже добавить: or current_user.role == "admin"
    if current_user.id != review.user_id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='Not allowed')

    # 5.  Мягкое удаление
    review.is_active = False

    # 6. Сохранить в БД
    await db.commit()

    # 6. Пересчитать рейтинг
    await update_product_rating(db, review.product_id)

    #7. Обновить объект перед возвращением
    await db.refresh(review)

    return review


