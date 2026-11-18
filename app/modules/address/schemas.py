from pydantic import BaseModel, Field


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
    class Config: from_attributes = True
