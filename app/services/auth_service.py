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

from sqlalchemy.orm import Session
from sqlalchemy import select
import secrets

from app.db.models.user import User
from app.core.security import hash_password
from app.core.response import BaseHTTPException, ErrorCodes
from app.utils.emailer import send_email_sync


def admin_change_password(db: Session, user_id: int, new_password: str) -> None:
    """
    Admin tomonidan user parolini to'g'ridan-to'g'ri almashtirish.
    Eski parol bekor qilinadi.
    """
    user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if not user:
        raise BaseHTTPException(
            status_code=404,
            error_code=ErrorCodes.NOT_FOUND,
            message="Foydalanuvchi topilmadi."
        )

    user.password_hash = hash_password(new_password)
    db.add(user)
    db.commit()


def reset_password(db: Session, email: str) -> None:
    """
    Forgot password uchun: email bo'yicha user topiladi,
    unga yangi random parol generatsiya qilinadi va emailga yuboriladi.
    """
    user = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()

    if not user:
        # Sen aniq tekshirilsin deding — shuning uchun 404 qaytaramiz.
        raise BaseHTTPException(
            status_code=404,
            error_code=ErrorCodes.NOT_FOUND,
            message="Ushbu email bilan foydalanuvchi topilmadi."
        )

    # Yangi parol generatsiya
    new_password = secrets.token_urlsafe(8)

    # Parolni yangilash
    user.password_hash = hash_password(new_password)
    db.add(user)
    db.commit()
    db.refresh(user)

    # Email yuborish (SMTP sozlanmagan bo'lsa, util o'zi shovqin qilmaydi)
    try:
        subject = "Obidov Toys — yangi parolingiz"
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
          <h2>Salom, {user.customer_name or user.email}!</h2>
          <p>Siz uchun yangi parol yaratildi:</p>
          <p style="font-size:18px;"><b>{new_password}</b></p>
          <p>Tizimga kirgach, uni xavfsizroq parolga almashtirishingizni tavsiya qilamiz.</p>
          <hr>
          <p style="font-size:12px;color:#888;">
            Agar ushbu so'rovni siz qilmagan bo'lsangiz, darhol administrator bilan bog'laning.
          </p>
        </div>
        """
        if user.email:
            send_email_sync(user.email, subject, html)
    except Exception:
        # Emailda xato bo'lsa ham, parol allaqachon yangilangan — qo'shimcha log yozib qo'ysang ham bo'ladi.
        pass