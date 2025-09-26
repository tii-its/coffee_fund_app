# Import all models to make them available for alembic
from .users import User
from .products import Product
from .consumptions import Consumption
from .money_moves import MoneyMove
from .audit import Audit

__all__ = ["User", "Product", "Consumption", "MoneyMove", "Audit"]