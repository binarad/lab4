from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4
from src.Domain.ports import RepositoryError
from src.Domain.order import Order


class MemoryOrderStore:
    """Process-wide demo storage without request/user context."""
    def __init__(self):
        self._orders = {}
        self._lock = Lock()

    def insert(self, order: Order) -> None:
        with self._lock:
            if order.id in self._orders:
                raise RepositoryError('Order identity already exists.')
            self._orders[order.id] = order


class InMemoryOrderRepository:
    def __init__(self, store: MemoryOrderStore):
        self._store = store

    def add(self, order: Order) -> None:
        self._store.insert(order)


class SystemClock:
    def now(self):
        return datetime.now(timezone.utc)


class UuidGenerator:
    def next_id(self):
        return uuid4()
