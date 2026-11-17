from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Literal

Budget = Literal[399, 699, 999, 1499]
Category = Literal["Tech", "Lifestyle", "Gaming", "Fitness", "Stationery", "Home & Living"]

class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=20)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("phone")
    @classmethod
    def validate_indian_phone(cls, value: str) -> str:
        phone = value.strip()
        if not phone.startswith("+91") or not phone[3:].isdigit() or len(phone) != 13:
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return phone

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str
    is_admin: bool
    is_email_confirmed: bool
    class Config:
        from_attributes = True

class AddressIn(BaseModel):
    label: str = Field(default="Home", max_length=40)
    recipient_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=10, max_length=20)
    line1: str = Field(min_length=3, max_length=255)
    line2: str | None = None
    city: str
    state: str
    postal_code: str = Field(min_length=5, max_length=12)
    is_default: bool = False

class AddressOut(AddressIn):
    id: int
    class Config:
        from_attributes = True

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
