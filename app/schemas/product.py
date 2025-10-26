from pydantic import BaseModel, Field, HttpUrl

class ProductCreate(BaseModel):
    name_uz: str = Field(min_length=1, max_length=150)
    name_ru: str = Field(min_length=1, max_length=150)
    description_uz: str | None = None
    description_ru: str | None = None
    price: float = Field(ge=0)
    image_url: str | None = None
    category_id: int

class ProductUpdate(BaseModel):
    name_uz: str | None = None
    name_ru: str | None = None
    description_uz: str | None = None
    description_ru: str | None = None
    price: float | None = None
    image_url: str | None = None
    category_id: int | None = None

class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: float
    image_url: str | None = None
    category_id: int
