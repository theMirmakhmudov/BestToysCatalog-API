from pydantic import BaseModel, EmailStr

class UserOut(BaseModel):
    id: int
    customer_name: str
    phone_number: str
    email: EmailStr
    role: str
    created_at: str
