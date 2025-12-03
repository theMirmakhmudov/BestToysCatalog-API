from pydantic import BaseModel


class RegisterRequest(BaseModel):
    customer_name: str
    phone_number: str


class AdminRegisterRequest(BaseModel):
    customer_name: str
    phone_number: str


class LoginRequest(BaseModel):
    phone_number: str


class SetTelegramIdRequest(BaseModel):
    phone_number: str
    telegram_id: int


class AuthResponse(BaseModel):
    user_id: int
    role: str
    customer_name: str | None = None
    telegram_id: int | None = None


class UserResponse(BaseModel):
    id: int
    customer_name: str | None
    phone_number: str
    role: str
    telegram_id: int | None = None
    created_at: str


class UserListResponse(BaseModel):
    users: list[UserResponse]
    count: int