import unittest
from dataclasses import replace
from decimal import Decimal
from unittest.mock import Mock
from src.Application.create_order import Clock, CreateOrder, IdGenerator
from src.Domain.ports import OrderRepository, RepositoryError
from src.Domain.order import DomainError, OrderStatus
from tests.fixtures import CUSTOMER_ID, NOW, ORDER_ID, valid_input


class CreateOrderTests(unittest.TestCase):
    def setUp(self):
        self.repository = Mock(spec=OrderRepository)
        self.clock = Mock(spec=Clock)
        self.ids = Mock(spec=IdGenerator)
        self.clock.now.return_value = NOW
        self.ids.next_id.return_value = ORDER_ID
        self.use_case = CreateOrder(self.repository, self.clock, self.ids)

    def test_success_saves_order_through_port(self):
        result = self.use_case.execute(valid_input())
        self.repository.add.assert_called_once()
        order = self.repository.add.call_args.args[0]
        self.assertEqual(order.id, ORDER_ID)
        self.assertEqual(str(order.customer_id), CUSTOMER_ID)
        self.assertEqual(order.status, OrderStatus.NEW)
        self.assertEqual(order.total_amount.amount, Decimal('199.98'))
        self.assertEqual(order.created_at, NOW)
        self.assertEqual(order.shipping_address.city, 'Kyiv')
        self.assertEqual(result.total_amount, Decimal('199.98'))
        self.assertEqual(result.id, str(ORDER_ID))
        self.assertEqual(result.status, 'NEW')

    def test_empty_order_does_not_write(self):
        with self.assertRaises(DomainError):
            self.use_case.execute(replace(valid_input(), items=()))
        self.repository.add.assert_not_called()
        self.clock.now.assert_not_called()
        self.ids.next_id.assert_not_called()

    def test_port_failure_propagates_without_hidden_io(self):
        failure = RepositoryError('simulated unavailable storage')
        self.repository.add.side_effect = failure
        with self.assertRaises(RepositoryError) as caught:
            self.use_case.execute(valid_input())
        self.assertIs(caught.exception, failure)
        self.repository.add.assert_called_once()

    def test_invalid_quantities_do_not_write(self):
        data = valid_input()
        for quantity in [0, -1, 1001, 1.5, True, '2']:
            with self.subTest(quantity=quantity), self.assertRaises(DomainError):
                self.use_case.execute(replace(data, items=(replace(data.items[0], quantity=quantity),)))
        self.repository.add.assert_not_called()
        self.clock.now.assert_not_called()

    def test_invalid_prices_do_not_write(self):
        data = valid_input()
        for amount in [Decimal('-0.01'), Decimal('NaN'), Decimal('Infinity'), Decimal('1e309')]:
            item = replace(data.items[0], product=replace(data.items[0].product, unit_price=amount))
            with self.subTest(amount=amount), self.assertRaises(DomainError):
                self.use_case.execute(replace(data, items=(item,)))
        self.repository.add.assert_not_called()

    def test_invalid_customer_identity_does_not_write(self):
        with self.assertRaises(DomainError):
            self.use_case.execute(replace(valid_input(), customer_id='not-a-uuid'))
        self.repository.add.assert_not_called()

    def test_invalid_address_does_not_write(self):
        data = valid_input()
        with self.assertRaises(DomainError):
            self.use_case.execute(replace(data, shipping_address=replace(data.shipping_address, city='K')))
        self.repository.add.assert_not_called()

    def test_item_count_limit(self):
        data = valid_input()
        result = self.use_case.execute(replace(data, items=data.items * 100))
        self.assertEqual(result.total_amount, Decimal('19998.00'))
        self.repository.reset_mock()
        with self.assertRaises(DomainError):
            self.use_case.execute(replace(data, items=data.items * 101))
        self.repository.add.assert_not_called()

    def test_total_is_exact_for_decimal_prices(self):
        data = valid_input()
        item = replace(data.items[0], quantity=3,
                       product=replace(data.items[0].product, unit_price=Decimal('0.1')))
        result = self.use_case.execute(replace(data, items=(item,)))
        self.assertEqual(result.total_amount, Decimal('0.3'))

    def test_free_product_is_allowed_by_original_contract(self):
        data = valid_input()
        item = replace(data.items[0], product=replace(data.items[0].product, unit_price=Decimal('0')))
        self.assertEqual(self.use_case.execute(replace(data, items=(item,))).total_amount, Decimal('0'))

    def test_clock_failure_does_not_write(self):
        self.clock.now.side_effect = RuntimeError('clock unavailable')
        with self.assertRaisesRegex(RuntimeError, 'clock unavailable'):
            self.use_case.execute(valid_input())
        self.repository.add.assert_not_called()

    def test_total_overflow_does_not_write(self):
        data = valid_input()
        item = replace(data.items[0], product=replace(data.items[0].product, unit_price=Decimal('1e308')))
        with self.assertRaises(DomainError):
            self.use_case.execute(replace(data, items=(item,)))
        self.repository.add.assert_not_called()
