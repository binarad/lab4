import unittest
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4
from src.Domain.order import Address, DomainError, Money, Order, OrderItem, ProductSnapshot
from tests.fixtures import CUSTOMER_ID, NOW, ORDER_ID, PRODUCT_ID


def order():
    return Order(ORDER_ID, UUID(CUSTOMER_ID),
                 (OrderItem(ProductSnapshot(UUID(PRODUCT_ID), 'Keyboard', Money(Decimal('99.99'))), 2),),
                 Address('Kyiv', 'Khreshchatyk 1', '01001', 'Ukraine'), NOW)


class DomainTests(unittest.TestCase):
    def test_value_objects_compare_by_value(self):
        self.assertEqual(Money(Decimal('10.0')), Money(Decimal('10.00')))
        self.assertEqual(Address('Kyiv', 'Street 1', '01001', 'Ukraine'),
                         Address('Kyiv', 'Street 1', '01001', 'Ukraine'))

    def test_entities_compare_by_identity(self):
        first = order()
        second = replace(first, customer_id=uuid4())
        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))
        self.assertNotEqual(first, replace(first, id=uuid4()))

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(DomainError):
            replace(order(), created_at=datetime(2026, 10, 24))

    def test_quantity_1000_is_accepted(self):
        first = order()
        item = replace(first.items[0], quantity=1000)
        self.assertEqual(replace(first, items=(item,)).total_amount.amount, Decimal('99990.00'))

    def test_long_product_name_is_rejected(self):
        with self.assertRaises(DomainError):
            ProductSnapshot(UUID(PRODUCT_ID), 'x' * 201, Money(Decimal('1')))

    def test_address_length_boundaries(self):
        self.assertEqual(len(Address('x' * 100, 'x' * 200, 'x' * 20, 'x' * 100).city), 100)
        with self.assertRaises(DomainError):
            Address('K', 'Street', '01001', 'Ukraine')
