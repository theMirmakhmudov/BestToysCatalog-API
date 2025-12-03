from pydantic import BaseModel, Field
from typing import List, Optional

class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)

class OrderCreate(BaseModel):
    user_id: int
    shipping_address: str = Field(min_length=5, max_length=255)
    phone_number: str = Field(pattern=r"^\+[1-9]\d{9,14}$")
    comment: Optional[str] = Field(default=None, max_length=500)
    items: List[OrderItemIn]

class OrderUpdate(BaseModel):
    shipping_address: str | None = None
    phone_number: str | None = None
    comment: str | None = None

class CancelRequest(BaseModel):
    user_id: int
    cancel_reason: str = Field(min_length=1, max_length=300)

class OrderCreateResponse(BaseModel):
    order_id: int
    status: str
    total_amount: float
    created_at: str

class OrderUpdateResponse(BaseModel):
    order_id: int
    status: str
    cancel_reason: str | None = None

class OrderItemOut(BaseModel):
    product_id: int
    product_name: str
    product_price: float
    quantity: int
    subtotal: float
    image_url: str | None = None

class OrderResponse(BaseModel):
    order_id: int
    status: str
    customer_name: str | None
    total_amount: float
    shipping_address: str
    phone_number: str
    comment: str | None
    items: list[OrderItemOut]
    created_at: str

class OrderListResponse(BaseModel):
    orders: list[OrderResponse]
    count: int
