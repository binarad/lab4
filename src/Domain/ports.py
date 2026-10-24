from typing import Protocol
from .order import Order


class OrderRepository(Protocol):
    def add(self, order: Order) -> None: ...


class RepositoryError(RuntimeError):
    """Storage adapter failures cross the boundary through this contract."""
