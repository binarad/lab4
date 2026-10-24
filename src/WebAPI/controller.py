from decimal import Decimal
from src.Application.create_order import (
    AddressData, CreateOrder, CreateOrderInput, OrderItemData, ProductData,
)
from src.Domain.ports import RepositoryError
from src.Domain.order import DomainError


class RequestError(ValueError):
    pass


def problem(status, title, detail):
    return {'type': 'about:blank', 'title': title, 'status': status, 'detail': detail}


def required_object(value, fields):
    if not isinstance(value, dict) or not set(fields).issubset(value):
        raise RequestError('Expected object with fields: ' + ', '.join(fields))
    return value


def parse_request(payload):
    data = required_object(payload, ['customerId', 'items', 'shippingAddress'])
    if not isinstance(data['items'], list):
        raise RequestError('items must be an array.')
    items = []
    for raw in data['items']:
        item = required_object(raw, ['product', 'quantity'])
        product = required_object(item['product'], ['productId', 'name', 'unitPrice'])
        price = product['unitPrice']
        if isinstance(price, bool) or not isinstance(price, (int, float, Decimal)):
            raise RequestError('unitPrice must be a JSON number.')
        items.append(OrderItemData(ProductData(
            product['productId'], product['name'], Decimal(str(price))), item['quantity']))
    address = required_object(data['shippingAddress'], ['city', 'street', 'postalCode', 'country'])
    return CreateOrderInput(data['customerId'], tuple(items), AddressData(
        address['city'], address['street'], address['postalCode'], address['country']))


def response_body(result):
    address = result.shipping_address
    return {
        'id': result.id, 'customerId': result.customer_id,
        'items': [{'product': {'productId': item.product.product_id,
                              'name': item.product.name,
                              'unitPrice': float(item.product.unit_price)},
                   'quantity': item.quantity} for item in result.items],
        'totalAmount': float(result.total_amount), 'status': result.status,
        'shippingAddress': {'city': address.city, 'street': address.street,
                            'postalCode': address.postal_code, 'country': address.country},
        'createdAt': result.created_at,
    }


class OrderController:
    def __init__(self, create_order: CreateOrder):
        self._create_order = create_order

    def post(self, payload):
        try:
            data = parse_request(payload)
        except RequestError as error:
            return 400, problem(400, 'Bad Request', str(error))
        try:
            result = self._create_order.execute(data)
            return 201, response_body(result)
        except DomainError as error:
            return 422, problem(422, 'Unprocessable Entity', str(error))
        except RepositoryError:
            return 503, problem(503, 'Service Unavailable', 'Order storage is unavailable.')
