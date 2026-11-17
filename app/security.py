import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_TO_A_LONG_RANDOM_SECRET_BEFORE_DEPLOYMENT")
ALGORITHM = "HS256"
COOKIE_NAME = "randomgift_session"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def create_access_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    return jwt.encode({"sub": str(user_id), "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)

def set_session_cookie(response, user_id: int):
    response.set_cookie(
        COOKIE_NAME, create_access_token(user_id), httponly=True, secure=COOKIE_SECURE,
        samesite="lax", max_age=7 * 24 * 60 * 60, path="/"
    )

def clear_session_cookie(response):
    response.set_cookie(
        COOKIE_NAME, "", httponly=True, secure=COOKIE_SECURE, samesite="lax",
        max_age=0, expires=0, path="/"
    )

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Account unavailable")
    return user

def get_admin_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user
