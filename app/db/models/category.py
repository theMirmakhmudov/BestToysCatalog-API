from __future__ import annotations
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name_uz: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name_ru: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name_en: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    products = relationship("Product", back_populates="category")
