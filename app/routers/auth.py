from app.schemas.auth import RegisterRequest, LoginRequest, SetTelegramIdRequest, AuthResponse, UserResponse, UserListResponse
from app.schemas.base import BaseResponse
from app.core.deps import get_db, admin_required, get_current_user
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models.user import User
from app.core.response import base_success, BaseHTTPException, ErrorCodes
from app.core.i18n import get_lang

router = APIRouter()


@router.post("/register", response_model=BaseResponse[AuthResponse])
def register(
    req: RegisterRequest,
    db: Session = Depends(get_db),
    request: Request = None,
):
    # Check if user exists
    existing_user = db.execute(
        select(User).where(User.phone_number == req.phone_number)
    ).scalar_one_or_none()

    if existing_user:
        raise BaseHTTPException(409, ErrorCodes.USER_EXISTS, "User with this phone number already exists")

    user = User(
        customer_name=req.customer_name,
        phone_number=req.phone_number,
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return base_success(
        AuthResponse(user_id=user.id, role=user.role.value, customer_name=user.customer_name),
        lang=get_lang(request),
    )


@router.post("/login", response_model=BaseResponse[AuthResponse])
def login(
    req: LoginRequest,
    db: Session = Depends(get_db),
    request: Request = None,
):
    user = db.execute(select(User).where(User.phone_number == req.phone_number)).scalar_one_or_none()
    
    if not user:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "User not found")

    return base_success(
        AuthResponse(
            user_id=user.id,
            customer_name=user.customer_name,
            role=user.role.value,
            telegram_id=user.telegram_id
        ),
        lang=get_lang(request),
    )


@router.patch("/set-telegram-id", response_model=BaseResponse[AuthResponse])
def set_telegram_id(
    req: SetTelegramIdRequest,
    db: Session = Depends(get_db),
    request: Request = None,
):
    # Find user by phone number
    user = db.execute(select(User).where(User.phone_number == req.phone_number)).scalar_one_or_none()
    
    if not user:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "User not found")

    # Check uniqueness if telegram_id is changing
    if user.telegram_id != req.telegram_id:
        existing = db.execute(select(User).where(User.telegram_id == req.telegram_id)).scalar_one_or_none()
        if existing:
            raise BaseHTTPException(409, ErrorCodes.USER_EXISTS, "Telegram ID already in use")
        user.telegram_id = req.telegram_id

    db.commit()
    db.refresh(user)

    return base_success(
        AuthResponse(
            user_id=user.id,
            customer_name=user.customer_name,
            role=user.role.value,
            telegram_id=user.telegram_id
        ),
        lang=get_lang(request),
    )


@router.post("/register-admin", response_model=BaseResponse[AuthResponse])
def register_admin(
    req: RegisterRequest,
    db: Session = Depends(get_db),
    request: Request = None,
):
    # Check if user exists
    existing_user = db.execute(
        select(User).where(User.phone_number == req.phone_number)
    ).scalar_one_or_none()

    if existing_user:
        raise BaseHTTPException(409, ErrorCodes.USER_EXISTS, "User with this phone number already exists")

    user = User(
        customer_name=req.customer_name,
        phone_number=req.phone_number,
        role="admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return base_success(
        AuthResponse(user_id=user.id, role=user.role.value, customer_name=user.customer_name),
        lang=get_lang(request),
    )


@router.get("/get-me", response_model=BaseResponse[UserResponse])
def get_me(
    user: User = Depends(get_current_user),
    request: Request = None,
):
    data = UserResponse(
        id=user.id,
        customer_name=user.customer_name,
        phone_number=user.phone_number,
        role=user.role.value,
        telegram_id=user.telegram_id,
        created_at=str(user.created_at)
    )

    return base_success(data, lang=get_lang(request))


@router.get("/get-all-users", response_model=BaseResponse[UserListResponse])
def get_all_users(
    db: Session = Depends(get_db),
    _: User = Depends(admin_required),
    request: Request = None,
):
    users = db.execute(select(User)).scalars().all()

    data = [
        UserResponse(
            id=u.id,
            customer_name=u.customer_name,
            phone_number=u.phone_number,
            role=u.role.value,
            telegram_id=u.telegram_id,
            created_at=str(u.created_at)
        )
        for u in users
    ]

    return base_success(
        UserListResponse(users=data, count=len(data)),
        lang=get_lang(request)
    )