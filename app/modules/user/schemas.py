from pydantic import BaseModel, EmailStr, Field, field_validator


def validate_indian_phone(value: str) -> str:
    phone = value.strip()
    if not phone.startswith("+91") or not phone[3:].isdigit() or len(phone) != 13:
        raise ValueError("Enter a valid 10-digit Indian mobile number")
    return phone


class UpdatePhoneIn(BaseModel):
    phone: str = Field(min_length=10, max_length=20)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return validate_indian_phone(value)


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str
    is_admin: bool
    is_email_confirmed: bool

    class Config:
        from_attributes = True
