from sqlalchemy.orm import Session
from .models import Order

class OrderRepository:
    def __init__(self, db: Session): self.db = db
    def save(self, order: Order) -> Order: self.db.add(order); self.db.commit(); self.db.refresh(order); return order
    def list_for_user(self, user_id: int) -> list[Order]: return self.db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
    def get_for_user(self, order_number: str, user_id: int) -> Order | None: return self.db.query(Order).filter(Order.order_number == order_number, Order.user_id == user_id).first()
