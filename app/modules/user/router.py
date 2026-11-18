from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from .models import User
from .schemas import UpdatePhoneIn, UserOut
from .service import PhoneAlreadyInUseError, UserService

router = APIRouter(prefix="/api/me", tags=["user"])


@router.patch("/phone", response_model=UserOut)
def update_phone(payload: UpdatePhoneIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return UserService(db).update_phone(user, payload.phone)
    except PhoneAlreadyInUseError:
        raise HTTPException(409, "Phone number already in use")
