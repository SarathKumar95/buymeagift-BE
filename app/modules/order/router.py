from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.modules.user.models import User
from .schemas import OrderCreate, OrderCreated, OrderDetail, OrderSummary
from .service import EmailConfirmationRequiredError, OrderNotFoundError, OrderService, PhoneRequiredError

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderCreated, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        order = OrderService(db).create_order(user, payload.model_dump())
    except EmailConfirmationRequiredError:
        raise HTTPException(403, "Please confirm your email address before placing an order")
    except PhoneRequiredError:
        raise HTTPException(403, "Please add your phone number before ordering")
    return OrderCreated(order_number=order.order_number, status=order.status, message="Your request has been received. No payment or shipment is enabled in this demo.")


@router.get("", response_model=list[OrderSummary])
def order_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [OrderSummary(order_number=order.order_number, status=order.status, budget=order.budget_paise // 100, created_at=order.created_at, recipient_type=order.recipient_type) for order in OrderService(db).list_orders(user.id)]


@router.get("/{order_number}", response_model=OrderDetail)
def get_order(order_number: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        order = OrderService(db).get_order(user.id, order_number)
    except OrderNotFoundError:
        raise HTTPException(404, "Order not found")
    return OrderDetail(order_number=order.order_number, status=order.status, budget=order.budget_paise // 100, created_at=order.created_at)
