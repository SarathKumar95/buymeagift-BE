from fastapi import APIRouter

from app.modules.address.router import router as address_router
from app.modules.auth.router import router as auth_router
from app.modules.order.router import router as order_router
from app.modules.user.router import router as user_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(address_router)
api_router.include_router(order_router)
