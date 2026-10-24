from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, localcontext
from enum import Enum
from math import isfinite
from uuid import UUID


class DomainError(ValueError):
    pass


def identity(value, field: str) -> UUID:
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str):
        raise DomainError(f'{field} must be a UUID.')
    try:
        return UUID(value)
    except ValueError as error:
        raise DomainError(f'{field} must be a UUID.') from error


def text(value, field: str, minimum: int, maximum: int) -> str:
    if not isinstance(value, str) or not minimum <= len(value) <= maximum:
        raise DomainError(f'{field} must contain {minimum} to {maximum} characters.')
    if not value.strip():
        raise DomainError(f'{field} cannot contain only whitespace.')
    return value


@dataclass(frozen=True)
class Money:
    amount: Decimal

    def __post_init__(self):
        if not isinstance(self.amount, Decimal) or not self.amount.is_finite():
            raise DomainError('Price must be a finite decimal.')
        if self.amount < 0 or not isfinite(float(self.amount)):
            raise DomainError('Price must be non-negative and fit the API double format.')


@dataclass(frozen=True)
class ProductSnapshot:
    product_id: UUID
    name: str
    unit_price: Money

    def __post_init__(self):
        if not isinstance(self.product_id, UUID) or not isinstance(self.unit_price, Money):
            raise DomainError('Invalid product identity or price.')
        text(self.name, 'Product name', 1, 200)


@dataclass(frozen=True)
class OrderItem:
    product: ProductSnapshot
    quantity: int

    def __post_init__(self):
        if not isinstance(self.product, ProductSnapshot):
            raise DomainError('An order item must contain a product snapshot.')
        if type(self.quantity) is not int or not 1 <= self.quantity <= 1000:
            raise DomainError('Quantity must be an integer from 1 to 1000.')


@dataclass(frozen=True)
class Address:
    city: str
    street: str
    postal_code: str
    country: str

    def __post_init__(self):
        text(self.city, 'City', 2, 100)
        text(self.street, 'Street', 2, 200)
        text(self.postal_code, 'Postal code', 3, 20)
        text(self.country, 'Country', 2, 100)


class OrderStatus(str, Enum):
    NEW = 'NEW'
    CONFIRMED = 'CONFIRMED'
    PAID = 'PAID'
    PROCESSING = 'PROCESSING'
    SHIPPED = 'SHIPPED'
    DELIVERED = 'DELIVERED'
    CANCELLED = 'CANCELLED'


@dataclass(frozen=True, eq=False)
class Order:
    id: UUID
    customer_id: UUID
    items: tuple[OrderItem, ...]
    shipping_address: Address
    created_at: datetime
    status: OrderStatus = OrderStatus.NEW

    def __post_init__(self):
        if not isinstance(self.id, UUID) or not isinstance(self.customer_id, UUID):
            raise DomainError('Order and customer identities must be UUIDs.')
        if not isinstance(self.items, tuple) or not 1 <= len(self.items) <= 100:
            raise DomainError('An order must contain 1 to 100 items.')
        if any(not isinstance(item, OrderItem) for item in self.items):
            raise DomainError('Invalid order item.')
        if not isinstance(self.shipping_address, Address):
            raise DomainError('A shipping address is required.')
        if not isinstance(self.created_at, datetime) or self.created_at.tzinfo is None:
            raise DomainError('Creation time must include a timezone.')
        if self.created_at.utcoffset() is None:
            raise DomainError('Creation time must include a timezone.')
        if self.status is not OrderStatus.NEW:
            raise DomainError('A newly created order must have status NEW.')
        if not isfinite(float(self.total_amount.amount)):
            raise DomainError('Order total must fit the API double format.')

    @property
    def total_amount(self) -> Money:
        # Keep all input decimal digits, even when their exponents differ.
        prices = [item.product.unit_price.amount for item in self.items]
        high = max(price.adjusted() for price in prices)
        low = min(price.as_tuple().exponent for price in prices)
        with localcontext() as context:
            context.prec = max(28, high - low + 12)
            return Money(sum((item.product.unit_price.amount * item.quantity
                              for item in self.items), Decimal('0')))

    def __eq__(self, other):
        if not isinstance(other, Order):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)
