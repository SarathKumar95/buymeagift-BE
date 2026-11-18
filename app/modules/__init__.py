def load_models() -> None:
    # Import model modules so SQLAlchemy registers all metadata before initialization.
    from .address import models as address_models  # noqa: F401
    from .auth import models as auth_models  # noqa: F401
    from .order import models as order_models  # noqa: F401
    from .user import models as user_models  # noqa: F401
