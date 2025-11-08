from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    customer_name: str = Field(min_length=2, max_length=100)
    phone_number: str = Field(pattern=r"^\+[1-9]\d{9,14}$")
    email: EmailStr

class AdminRegisterRequest(RegisterRequest):
    password: str | None = Field(default=None, min_length=8, max_length=128)

class AdminChangePasswordRequest(BaseModel):
    user_id: int = Field(..., ge=1)
    new_password: str = Field(..., min_length=6)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class LoginRequest(BaseModel):
    phone_number: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int
