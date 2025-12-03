import secrets
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.user import User, RoleEnum
from app.core.response import BaseHTTPException, ErrorCodes


def register_user(db: Session, customer_name: str, phone_number: str) -> User:
    """
    Oddiy userni ro‘yxatdan o‘tkazish.
    Faqat customer_name + phone_number kerak.
    """
    exists = db.execute(
        select(User).where(User.phone_number == phone_number)
    ).scalar_one_or_none()
    if exists:
        raise BaseHTTPException(
            409,
            ErrorCodes.USER_EXISTS,
            "Phone number already exists."
        )

    user = User(
        customer_name=customer_name,
        phone_number=phone_number,
        role=RoleEnum.user,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def register_admin(db: Session, customer_name: str, phone_number: str) -> User:
    """
    Adminni ro‘yxatdan o‘tkazish.
    Faqat customer_name + phone_number.
    """
    exists = db.execute(
        select(User).where(User.phone_number == phone_number)
    ).scalar_one_or_none()
    if exists:
        raise BaseHTTPException(
            409,
            ErrorCodes.DUPLICATE,
            "Phone number already exists."
        )

    user = User(
        customer_name=customer_name,
        phone_number=phone_number,
        role=RoleEnum.admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, phone_number: str) -> User:
    """
    Mini-app login:
    - faqat phone_number bo‘yicha user topiladi
    """
    user = db.execute(
        select(User).where(User.phone_number == phone_number)
    ).scalar_one_or_none()

    if not user:
        raise BaseHTTPException(
            401,
            ErrorCodes.AUTH_FAILED,
            "Phone number is not registered."
        )

    return user