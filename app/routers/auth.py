from fastapi import APIRouter, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.schemas.auth import RegisterRequest, AdminRegisterRequest, LoginRequest, ForgotPasswordRequest
from app.core.deps import get_db, get_current_user, admin_required
from app.core.response import base_success, BaseHTTPException, ErrorCodes
from app.core.i18n import get_lang
from app.services.auth_service import register_user, register_admin, login, reset_password
from app.db.models.user import User
from app.utils.emailer import send_email_sync, build_welcome_email

router = APIRouter()

@router.post("/register")
def register(req: RegisterRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), request: Request = None):
    user, plain_password = register_user(db, req.customer_name, req.phone_number, req.email)
    subject, html_body = build_welcome_email(user.customer_name, user.phone_number, user.email, plain_password)
    background_tasks.add_task(send_email_sync, user.email, subject, html_body)

    return base_success({"message": "User created. Password sent to email.", "role": "user"}, lang=get_lang(request))

@router.post("/admin-register")
def admin_register(req: AdminRegisterRequest, db: Session = Depends(get_db), admin=Depends(admin_required), request: Request = None):
    user = register_admin(db, req.customer_name, req.phone_number, req.email, req.password)
    return base_success({"user_id": user.id, "role": "admin"}, lang=get_lang(request))

@router.post("/login")
def do_login(req: LoginRequest, db: Session = Depends(get_db), request: Request = None):
    tokens = login(db, req.phone_number, req.password)
    return base_success({"access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"], "token_type": "bearer", "expires_in": tokens["expires_in"]}, lang=get_lang(request))

@router.get("/check-phone-number")
def check_phone(phone_number: str, db: Session = Depends(get_db), request: Request = None):
    exists = db.execute(select(User).where(User.phone_number == phone_number)).scalar_one_or_none() is not None
    return base_success({"exists": exists}, lang=get_lang(request))

@router.get("/get-me")
def get_me(current: User = Depends(get_current_user), request: Request = None):
    data = {
        "id": current.id,
        "customer_name": current.customer_name,
        "phone_number": current.phone_number,
        "email": current.email,
        "role": current.role.value,
        "created_at": str(current.created_at)
    }
    return base_success(data, lang=get_lang(request))

@router.post("/forgot-password")
def forgot_password_endpoint(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required),
):
    """
    Foydalanuvchi parolini unutganda:
    - email bo'yicha user topiladi
    - yangi parol generatsiya qilinadi
    - emailga yuboriladi
    """
    reset_password(db, data.email)
    return base_success(data)

@router.post("/refresh-token")
def refresh_token(refresh_token: str, request: Request = None):
    from app.core.security import decode_token, create_token
    from app.core.config import settings
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise BaseHTTPException(401, ErrorCodes.TOKEN_EXPIRED, "Token expired or invalid.")
    new_access = create_token(payload["sub"], payload.get("role", "user"), settings.ACCESS_TTL_SECONDS)
    return base_success({"access_token": new_access, "token_type": "bearer", "expires_in": settings.ACCESS_TTL_SECONDS}, lang=get_lang(request))
