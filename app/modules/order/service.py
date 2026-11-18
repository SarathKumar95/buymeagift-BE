import secrets
from sqlalchemy.orm import Session
from app.modules.user.models import User
from .crud import OrderRepository
from .models import Order

class EmailConfirmationRequiredError(Exception): pass
class PhoneRequiredError(Exception): pass
class OrderNotFoundError(Exception): pass

class OrderService:
    def __init__(self, db: Session): self.orders = OrderRepository(db)
    def create_order(self, user: User, values: dict) -> Order:
        if not user.is_email_confirmed: raise EmailConfirmationRequiredError
        if user.phone.startswith("PENDING-"): raise PhoneRequiredError
        order = Order(order_number="RND-" + secrets.token_hex(4).upper(), user_id=user.id, recipient_type=values["recipient_type"], budget_paise=values["budget"] * 100, categories=",".join(values["categories"]), exclusions=",".join(values["exclusions"]), recipient_name=values["recipient_name"], recipient_email=values["recipient_email"], delivery_address=values["delivery_address"], gift_message=values["gift_message"], status="PLACED")
        return self.orders.save(order)
    def list_orders(self, user_id: int) -> list[Order]: return self.orders.list_for_user(user_id)
    def get_order(self, user_id: int, order_number: str) -> Order:
        order = self.orders.get_for_user(order_number, user_id)
        if not order: raise OrderNotFoundError
        return order
