from __future__ import annotations
from typing import Generator
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.models.user import User, RoleEnum
from app.core.response import BaseHTTPException, ErrorCodes
from app.core.security import decode_token, hash_password
from app.core.config import settings


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization:
        raise BaseHTTPException(401, ErrorCodes.AUTH_FAILED, "Authorization header required.")

    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise BaseHTTPException(401, ErrorCodes.AUTH_FAILED, "Invalid token format. Must start with 'Bearer'.")

    token = parts[1]

    try:
        # Faqat security.py dagi decode_token funksiyasidan foydalanamiz
        payload = decode_token(token)
    except Exception:
        raise BaseHTTPException(401, ErrorCodes.TOKEN_EXPIRED, "Token expired or invalid.")

    user_id = payload.get("sub")
    if not user_id:
        raise BaseHTTPException(401, ErrorCodes.AUTH_FAILED, "Invalid token payload.")

    user = db.get(User, int(user_id))
    if not user:
        raise BaseHTTPException(401, ErrorCodes.AUTH_FAILED, "User not found.")

    return user


def admin_required(user: User = Depends(get_current_user)) -> User:
    if user.role != RoleEnum.admin:
        raise BaseHTTPException(403, ErrorCodes.FORBIDDEN, "Admin privileges required.")
    return user


async def create_db_and_init_admin():
    from app.db.base import Base
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        exists = db.execute(
            select(User).where(User.email == (settings.INIT_ADMIN_EMAIL or ""))
        ).scalar_one_or_none()

        if not exists and settings.INIT_ADMIN_EMAIL and settings.INIT_ADMIN_PHONE and settings.INIT_ADMIN_PASSWORD:
            admin = User(
                customer_name=settings.INIT_ADMIN_NAME or "Admin",
                phone_number=settings.INIT_ADMIN_PHONE,
                email=(settings.INIT_ADMIN_EMAIL or "").lower(),
                password_hash=hash_password(settings.INIT_ADMIN_PASSWORD),
                role=RoleEnum.admin,
            )
            db.add(admin)
            db.commit()