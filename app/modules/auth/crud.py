from sqlalchemy.orm import Session

from .models import EmailVerificationToken


class VerificationTokenRepository:
    def __init__(self, db: Session): self.db = db
    def get_by_hash(self, token_hash: str) -> EmailVerificationToken | None:
        return self.db.query(EmailVerificationToken).filter(EmailVerificationToken.token_hash == token_hash).first()
    def save(self, token: EmailVerificationToken) -> EmailVerificationToken:
        self.db.add(token); self.db.commit(); self.db.refresh(token); return token
    def commit(self) -> None: self.db.commit()
