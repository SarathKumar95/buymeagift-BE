import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.infrastructure.auth import hash_password, verify_password
from app.infrastructure.email import EmailDeliveryError, send_verification_email
from app.modules.user.crud import UserRepository
from app.modules.user.models import User

from .crud import VerificationTokenRepository
from .models import EmailVerificationToken


class DuplicateEmailError(Exception): pass
class DuplicatePhoneError(Exception): pass
class InvalidCredentialsError(Exception): pass
class AccountDisabledError(Exception): pass
class InvalidVerificationTokenError(Exception): pass
class GoogleEmailNotVerifiedError(Exception): pass


class AuthService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)
        self.tokens = VerificationTokenRepository(db)

    def register(self, name: str, email: str, phone: str, password: str) -> User:
        email = email.lower()
        if self.users.get_by_email(email): raise DuplicateEmailError
        if self.users.get_by_phone(phone): raise DuplicatePhoneError
        user = User(name=name, email=email, phone=phone, password_hash=hash_password(password))
        self.users.save(user)
        self.send_verification(user)
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email.lower())
        if not user or not user.password_hash or not verify_password(password, user.password_hash): raise InvalidCredentialsError
        if not user.is_active: raise AccountDisabledError
        return user

    def _create_verification_token(self, user: User) -> str:
        raw_token = secrets.token_urlsafe(32)
        token = EmailVerificationToken(user_id=user.id, token_hash=hashlib.sha256(raw_token.encode()).hexdigest(), expires_at=datetime.now(timezone.utc) + timedelta(hours=24))
        self.tokens.save(token)
        return raw_token

    def send_verification(self, user: User) -> None:
        raw_token = self._create_verification_token(user)
        send_verification_email(user.name, user.email, raw_token)

    def verify_email(self, raw_token: str) -> User:
        verification = self.tokens.get_by_hash(hashlib.sha256(raw_token.encode()).hexdigest())
        now = datetime.now(timezone.utc)
        if not verification or verification.used_at or verification.expires_at < now: raise InvalidVerificationTokenError
        user = self.users.get_by_id(verification.user_id)
        if not user: raise InvalidVerificationTokenError
        verification.used_at = now
        user.is_email_confirmed = True
        self.tokens.commit()
        return user

    def resolve_google_user(self, info: dict) -> User:
        email = (info.get("email") or "").lower()
        if not email or not info.get("email_verified"): raise GoogleEmailNotVerifiedError
        user = self.users.get_by_google_sub(info["sub"])
        if not user:
            user = self.users.get_by_email(email)
            if user:
                user.google_sub = info["sub"]
            else:
                user = User(name=info.get("name") or email.split("@")[0], email=email, phone="PENDING-" + secrets.token_hex(5), google_sub=info["sub"])
            self.users.save(user)
        return user
