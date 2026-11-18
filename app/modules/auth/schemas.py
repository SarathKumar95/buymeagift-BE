from pydantic import BaseModel, EmailStr, Field, field_validator

from app.modules.user.schemas import validate_indian_phone


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=20)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return validate_indian_phone(value)


class LoginIn(BaseModel):
    email: EmailStr
    password: str
