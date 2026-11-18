from sqlalchemy.orm import Session
from .crud import AddressRepository
from .models import Address

class AddressNotFoundError(Exception): pass
class AddressService:
    def __init__(self, db: Session): self.addresses = AddressRepository(db)
    def list_addresses(self, user_id: int) -> list[Address]: return self.addresses.list_for_user(user_id)
    def create_address(self, user_id: int, values: dict) -> Address:
        if values["is_default"]: self.addresses.clear_default_for_user(user_id)
        return self.addresses.save(Address(user_id=user_id, **values))
    def delete_address(self, user_id: int, address_id: int) -> None:
        address = self.addresses.get_for_user(address_id, user_id)
        if not address: raise AddressNotFoundError
        self.addresses.delete(address)
