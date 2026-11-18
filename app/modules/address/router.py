from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.modules.user.models import User
from .schemas import AddressIn, AddressOut
from .service import AddressNotFoundError, AddressService

router = APIRouter(prefix="/api/addresses", tags=["addresses"])


@router.get("", response_model=list[AddressOut])
def list_addresses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return AddressService(db).list_addresses(user.id)


@router.post("", response_model=AddressOut, status_code=201)
def create_address(payload: AddressIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return AddressService(db).create_address(user.id, payload.model_dump())


@router.delete("/{address_id}")
def delete_address(address_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        AddressService(db).delete_address(user.id, address_id)
    except AddressNotFoundError:
        raise HTTPException(404, "Address not found")
    return {"message": "Address deleted"}
