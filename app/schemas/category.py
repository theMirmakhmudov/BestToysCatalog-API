from pydantic import BaseModel, Field

class CategoryCreate(BaseModel):
    name_uz: str = Field(min_length=1, max_length=100)
    name_ru: str = Field(min_length=1, max_length=100)

class CategoryUpdate(BaseModel):
    name_uz: str | None = Field(default=None, min_length=1, max_length=100)
    name_ru: str | None = Field(default=None, min_length=1, max_length=100)

class CategoryOut(BaseModel):
    id: int
    name: str
