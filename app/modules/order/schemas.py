from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field

Budget = Literal[399, 699, 999, 1499]
Category = Literal["Tech", "Lifestyle", "Gaming", "Fitness", "Stationery", "Home & Living"]

class OrderCreate(BaseModel):
    recipient_type: Literal["SELF", "SOMEONE_ELSE"]
    budget: Budget
    categories: list[Category] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    recipient_name: str = Field(min_length=1, max_length=120)
    recipient_email: EmailStr
    delivery_address: str = Field(min_length=10, max_length=1000)
    gift_message: str | None = Field(default=None, max_length=500)

class OrderCreated(BaseModel):
    order_number: str
    status: str
    message: str

class OrderSummary(BaseModel):
    order_number: str
    status: str
    budget: int
    created_at: datetime
    recipient_type: str

class OrderDetail(BaseModel):
    order_number: str
    status: str
    budget: int
    created_at: datetime
