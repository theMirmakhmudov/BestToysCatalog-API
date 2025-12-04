from __future__ import annotations
from typing import Generator
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.models.user import User, RoleEnum
from app.core.response import BaseHTTPException, ErrorCodes
from app.core.config import settings


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    telegram_id: int | None = Header(None, alias="X-Telegram-Id"),
    db: Session = Depends(get_db)
) -> User:
    if not telegram_id:
        raise BaseHTTPException(401, ErrorCodes.AUTH_FAILED, "Authentication required (X-Telegram-Id missing)")

    user = db.execute(select(User).where(User.telegram_id == telegram_id)).scalar_one_or_none()

    if not user:
        raise BaseHTTPException(401, ErrorCodes.AUTH_FAILED, "User not found or Telegram ID not set.")

    return user


def admin_required(user: User = Depends(get_current_user)) -> User:
    if user.role != RoleEnum.admin:
        raise BaseHTTPException(403, ErrorCodes.FORBIDDEN, "Admin privileges required.")
    return user


async def create_db_and_init_admin():
    from app.db.base import Base
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        # Check if any admin exists
        exists = db.execute(
            select(User).where(User.role == RoleEnum.admin)
        ).first()

        if not exists and settings.INIT_ADMIN_PHONE:
            new_admin = User(
                customer_name=settings.INIT_ADMIN_NAME,
                phone_number=settings.INIT_ADMIN_PHONE,
                telegram_id=settings.INIT_ADMIN_TELEGRAM_ID,
                role=RoleEnum.admin
            )
            db.add(new_admin)
            db.commit()