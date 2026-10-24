import unittest
from copy import deepcopy
from decimal import Decimal
from unittest.mock import Mock
from src.Application.create_order import CreateOrder, CreateOrderResult
from src.Domain.ports import RepositoryError
from src.Domain.order import DomainError
from src.WebAPI.controller import OrderController
from tests.fixtures import NOW, ORDER_ID, valid_input, valid_payload


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.scenario = Mock(spec=CreateOrder)
        data = valid_input()
        self.scenario.execute.return_value = CreateOrderResult(
            str(ORDER_ID), data.customer_id, data.items, Decimal('199.98'),
            'NEW', data.shipping_address, NOW.isoformat())
        self.controller = OrderController(self.scenario)

    def test_success_matches_original_contract_fields(self):
        status, body = self.controller.post(valid_payload())
        self.assertEqual(status, 201)
        self.assertEqual(set(body), {'id', 'customerId', 'items', 'totalAmount',
                                     'status', 'shippingAddress', 'createdAt'})
        self.assertEqual(body['totalAmount'], 199.98)
        self.assertEqual(body['items'], valid_payload()['items'])
        self.assertEqual(body['shippingAddress'], valid_payload()['shippingAddress'])

    def test_domain_error_maps_to_422_problem_details(self):
        self.scenario.execute.side_effect = DomainError('Empty order')
        status, body = self.controller.post(valid_payload())
        self.assertEqual(status, 422)
        self.assertEqual(body['status'], 422)
        self.assertEqual(set(body), {'type', 'title', 'status', 'detail'})

    def test_port_error_maps_to_503_without_leaking_details(self):
        self.scenario.execute.side_effect = RepositoryError('private storage details')
        status, body = self.controller.post(valid_payload())
        self.assertEqual(status, 503)
        self.assertNotIn('private', body['detail'])

    def test_bad_payload_does_not_call_scenario(self):
        for payload in [None, [], {}, {'customerId': 'id', 'items': [], 'shippingAddress': None}]:
            self.assertEqual(self.controller.post(payload)[0], 400)
        self.scenario.execute.assert_not_called()

    def test_missing_nested_fields_do_not_call_scenario(self):
        payload = valid_payload()
        del payload['items'][0]['product']['unitPrice']
        self.assertEqual(self.controller.post(payload)[0], 400)
        self.scenario.execute.assert_not_called()

    def test_non_numeric_price_is_not_silently_coerced(self):
        for price in ['99.99', True, None, {}]:
            payload = valid_payload()
            payload['items'][0]['product']['unitPrice'] = price
            self.assertEqual(self.controller.post(payload)[0], 400)
        self.scenario.execute.assert_not_called()

    def test_decimal_json_value_is_preserved_in_dto(self):
        payload = valid_payload()
        payload['items'][0]['product']['unitPrice'] = Decimal('0.123456789123456789')
        self.controller.post(payload)
        self.assertEqual(self.scenario.execute.call_args.args[0].items[0].product.unit_price,
                         Decimal('0.123456789123456789'))

    def test_client_total_and_status_cannot_override_server_values(self):
        payload = valid_payload()
        payload.update(totalAmount=0, status='PAID')
        status, body = self.controller.post(payload)
        self.assertEqual(status, 201)
        self.assertEqual(body['totalAmount'], 199.98)
        self.assertEqual(body['status'], 'NEW')
