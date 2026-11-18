from sqlalchemy.orm import Session

from .crud import UserRepository
from .models import User


class PhoneAlreadyInUseError(Exception): pass


class UserService:
    def __init__(self, db: Session): self.users = UserRepository(db)
    def update_phone(self, user: User, phone: str) -> User:
        existing = self.users.get_by_phone(phone)
        if existing and existing.id != user.id: raise PhoneAlreadyInUseError
        user.phone = phone
        return self.users.save(user)
