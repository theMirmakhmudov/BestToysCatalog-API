import secrets
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models.user import User, RoleEnum
from app.core.response import BaseHTTPException, ErrorCodes
from app.core.security import hash_password, verify_password, create_token
from app.core.config import settings

def _gen_password() -> str:
    return secrets.token_urlsafe(12)

def register_user(db: Session, customer_name: str, phone_number: str, email: str) -> tuple[User, str]:
    exists = db.execute(
        select(User).where((User.email == email.lower()) | (User.phone_number == phone_number))
    ).scalar_one_or_none()
    if exists:
        raise BaseHTTPException(409, ErrorCodes.USER_EXISTS, "Phone or email already exists.")

    plain = _gen_password()
    u = User(
        customer_name=customer_name,
        phone_number=phone_number,
        email=email.lower(),
        password_hash=hash_password(plain),
        role=RoleEnum.user,
    )
    db.add(u); db.commit(); db.refresh(u)
    return u, plain

def register_admin(db: Session, customer_name: str, phone_number: str, email: str, password: str | None) -> User:
    exists = db.execute(
        select(User).where((User.email == email.lower()) | (User.phone_number == phone_number))
    ).scalar_one_or_none()
    if exists:
        raise BaseHTTPException(409, ErrorCodes.DUPLICATE, "Phone or email already exists.")

    plain = password or _gen_password()
    u = User(
        customer_name=customer_name,
        phone_number=phone_number,
        email=email.lower(),
        password_hash=hash_password(plain),
        role=RoleEnum.admin,
    )
    db.add(u); db.commit(); db.refresh(u)
    return u

def login(db: Session, phone_number: str, password: str):
    from app.db.models.user import User
    user = db.execute(select(User).where(User.phone_number == phone_number)).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise BaseHTTPException(401, ErrorCodes.AUTH_FAILED, "Phone or password is incorrect.")

    access = create_token(str(user.id), user.role.value, settings.ACCESS_TTL_SECONDS)
    refresh = create_token(str(user.id), user.role.value, settings.REFRESH_TTL_SECONDS)
    return {"access_token": access, "refresh_token": refresh, "expires_in": settings.ACCESS_TTL_SECONDS}