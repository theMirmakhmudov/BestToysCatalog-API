from pydantic import BaseModel, Field
from typing import List, Optional

class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)

class OrderCreate(BaseModel):
    shipping_address: str = Field(min_length=5, max_length=255)
    phone_number: str = Field(pattern=r"^\+[1-9]\d{9,14}$")
    comment: Optional[str] = Field(default=None, max_length=500)
    items: List[OrderItemIn]

class OrderUpdate(BaseModel):
    shipping_address: str | None = None
    phone_number: str | None = None
    comment: str | None = None

class CancelRequest(BaseModel):
    cancel_reason: str = Field(min_length=1, max_length=300)
