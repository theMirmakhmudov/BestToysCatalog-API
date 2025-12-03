from pydantic import BaseModel, Field

class CategoryCreate(BaseModel):
    name_uz: str = Field(min_length=1, max_length=100)
    name_ru: str = Field(min_length=1, max_length=100)
    name_en: str = Field(min_length=1, max_length=100)

class CategoryUpdate(BaseModel):
    name_uz: str | None = Field(default=None, min_length=1, max_length=100)
    name_ru: str | None = Field(default=None, min_length=1, max_length=100)
    name_en: str | None = Field(default=None, min_length=1, max_length=100)

class CategoryOut(BaseModel):
    id: int
    name: str
    name_uz: str
    name_ru: str
    name_en: str

class CategoryListResponse(BaseModel):
    categories: list[CategoryOut]
    count: int
