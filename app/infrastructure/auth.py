from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.infrastructure.config import settings
from app.infrastructure.database import get_db
from app.modules.user.crud import UserRepository
from app.modules.user.models import User

ALGORITHM = "HS256"
COOKIE_NAME = "randomgift_session"
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def _create_access_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    return jwt.encode({"sub": str(user_id), "exp": expires}, settings.jwt_secret_key, algorithm=ALGORITHM)


def set_session_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(COOKIE_NAME, _create_access_token(user_id), httponly=True, secure=settings.cookie_secure, samesite="lax", max_age=7 * 24 * 60 * 60, path="/")


def clear_session_cookie(response: Response) -> None:
    response.set_cookie(COOKIE_NAME, "", httponly=True, secure=settings.cookie_secure, samesite="lax", max_age=0, expires=0, path="/")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        user_id = int(jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    user = UserRepository(db).get_active_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Account unavailable")
    return user


def get_admin_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user
