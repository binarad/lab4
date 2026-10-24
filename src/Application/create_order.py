from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID
from src.Domain.ports import OrderRepository
from src.Domain.order import (
    Address, DomainError, Money, Order, OrderItem, ProductSnapshot, identity,
)


class Clock(Protocol):
    def now(self) -> datetime: ...


class IdGenerator(Protocol):
    def next_id(self) -> UUID: ...


@dataclass(frozen=True)
class AddressData:
    city: str
    street: str
    postal_code: str
    country: str


@dataclass(frozen=True)
class ProductData:
    product_id: str
    name: str
    unit_price: Decimal


@dataclass(frozen=True)
class OrderItemData:
    product: ProductData
    quantity: int


@dataclass(frozen=True)
class CreateOrderInput:
    customer_id: str
    items: tuple[OrderItemData, ...]
    shipping_address: AddressData


@dataclass(frozen=True)
class CreateOrderResult:
    id: str
    customer_id: str
    items: tuple[OrderItemData, ...]
    total_amount: Decimal
    status: str
    shipping_address: AddressData
    created_at: str


class CreateOrder:
    def __init__(self, repository: OrderRepository, clock: Clock, ids: IdGenerator):
        self._repository = repository
        self._clock = clock
        self._ids = ids

    def execute(self, data: CreateOrderInput) -> CreateOrderResult:
        customer_id = identity(data.customer_id, 'customerId')
        if not 1 <= len(data.items) <= 100:
            raise DomainError('An order must contain 1 to 100 items.')
        items = tuple(OrderItem(ProductSnapshot(
            identity(item.product.product_id, 'productId'), item.product.name,
            Money(item.product.unit_price)), item.quantity) for item in data.items)
        address = Address(data.shipping_address.city, data.shipping_address.street,
                          data.shipping_address.postal_code, data.shipping_address.country)
        order = Order(self._ids.next_id(), customer_id, items, address, self._clock.now())
        self._repository.add(order)
        return CreateOrderResult(
            str(order.id), str(order.customer_id),
            tuple(OrderItemData(ProductData(str(item.product.product_id),
                  item.product.name, item.product.unit_price.amount), item.quantity)
                  for item in order.items),
            order.total_amount.amount, order.status.value,
            AddressData(address.city, address.street, address.postal_code, address.country),
            order.created_at.isoformat())
