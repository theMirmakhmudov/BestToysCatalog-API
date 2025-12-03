from pydantic import BaseModel

class UserOut(BaseModel):
    id: int
    customer_name: str
    phone_number: str
    phone_number: str
    role: str
    created_at: str
