from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID
from src.Application.create_order import AddressData, CreateOrderInput, OrderItemData, ProductData

ORDER_ID = UUID('00000000-0000-0000-0000-000000000001')
CUSTOMER_ID = '550e8400-e29b-41d4-a716-446655440000'
PRODUCT_ID = '497f6eca-6276-4993-bfeb-53cbbbaf6080'
NOW = datetime(2026, 10, 24, 9, tzinfo=timezone.utc)


def valid_input():
    return CreateOrderInput(CUSTOMER_ID,
        (OrderItemData(ProductData(PRODUCT_ID, 'Mechanical Keyboard', Decimal('99.99')), 2),),
        AddressData('Kyiv', 'Khreshchatyk 1', '01001', 'Ukraine'))


def valid_payload():
    return {'customerId': CUSTOMER_ID,
            'items': [{'product': {'productId': PRODUCT_ID, 'name': 'Mechanical Keyboard',
                                  'unitPrice': 99.99}, 'quantity': 2}],
            'shippingAddress': {'city': 'Kyiv', 'street': 'Khreshchatyk 1',
                                'postalCode': '01001', 'country': 'Ukraine'}}
