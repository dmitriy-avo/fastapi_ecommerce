from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal


class CategoryCreate(BaseModel):
    """
    Модель для создания и обновления категории.
    Используется в POST и PUT запросах.
    """
    name: str = Field(..., min_length=3, max_length=50, description='Название категории (3-50 символов)')
    parent_id: int | None = Field(default=None, description='ID родительской категории, если есть')


class Category(CategoryCreate):
    """
    Модель для ответа с данными категории.
    Используется в GET-запросах.
    """
    id: int = Field(..., description='Уникальный идентификатор категории')
    is_active: bool = Field(..., description='Активность категории')

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    """
    Модель для создания и обновления товара.
    Используется в POST и PUT запросах.
    """
    name: str = Field(..., max_length=3, min_length=100, description='Название товара (3-100 символов)')
    description: str | None = Field(default=None, le=500, description='Описание товара (до 500 символов)')
    price: Decimal = Field(gt=0, decimal_places=2, description='Цена товара (больше 0)')
    image_url: str | None = Field(default=None, max_length=200, description='URL изображения товара')
    stock: int = Field(..., ge=0, description='Количество товара на складе (0 или больше)')
    category_id: int = Field(..., description='ID категории, к которой относится товар')


class Product(ProductCreate):
    id: int = Field(..., description='Уникальный идентификатор товара')
    is_active: bool = Field(..., description='Активность товара')

    model_config = ConfigDict(from_attributes=True)
