"""Separate local HTTP integration check; intentionally outside the unit suite."""
from copy import deepcopy
from http.client import HTTPConnection
from http.server import HTTPServer
from pathlib import Path
import json
import sys
import threading
from uuid import UUID

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from src.WebAPI.bootstrap import build_container, example_payload, make_handler


def main():
    valid = example_payload()
    empty = deepcopy(valid)
    empty['items'] = []
    bad_quantity = deepcopy(valid)
    bad_quantity['items'][0]['quantity'] = 0
    negative_price = deepcopy(valid)
    negative_price['items'][0]['product']['unitPrice'] = -1
    bad_address = deepcopy(valid)
    bad_address['shippingAddress']['postalCode'] = '01'
    bad_customer = deepcopy(valid)
    bad_customer['customerId'] = 'invalid'
    override = deepcopy(valid)
    override.update(totalAmount=0, status='PAID')
    cases = [
        ('create_order', '/orders', json.dumps(valid), 'application/json', 201),
        ('reject_empty_order', '/orders', json.dumps(empty), 'application/json', 422),
        ('reject_zero_quantity', '/orders', json.dumps(bad_quantity), 'application/json', 422),
        ('reject_negative_price', '/orders', json.dumps(negative_price), 'application/json', 422),
        ('reject_bad_address', '/orders', json.dumps(bad_address), 'application/json', 422),
        ('reject_bad_uuid', '/orders', json.dumps(bad_customer), 'application/json', 422),
        ('reject_missing_fields', '/orders', '{}', 'application/json', 400),
        ('reject_bad_json', '/orders', '{bad json', 'application/json', 400),
        ('reject_nan_json', '/orders', json.dumps(valid).replace('99.99', 'NaN'), 'application/json', 400),
        ('reject_double_overflow', '/orders', json.dumps(valid).replace('99.99', '1e309'), 'application/json', 422),
        ('reject_wrong_route', '/tasks', '{}', 'application/json', 404),
        ('reject_wrong_media', '/orders', '{}', 'text/plain', 415),
        ('reject_empty_body', '/orders', '', 'application/json', 413),
        ('server_controls_total_and_status', '/orders', json.dumps(override), 'application/json', 201),
    ]
    lines = ['Order Service: separate HTTP integration check (not unit tests)',
             'Bind: 127.0.0.1, ephemeral port; no external services or database.']
    with HTTPServer(('127.0.0.1', 0), make_handler(build_container())) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for name, path, payload, media, expected in cases:
                connection = HTTPConnection('127.0.0.1', server.server_port, timeout=5)
                try:
                    connection.request('POST', path, payload, {'Content-Type': media})
                    response = connection.getresponse()
                    body = json.loads(response.read())
                    assert response.status == expected, (name, response.status, body)
                    UUID(response.getheader('X-Trace-ID'))
                    content_type = response.getheader('Content-Type')
                    if expected == 201:
                        assert content_type.startswith('application/json')
                        assert body['totalAmount'] == 199.98 and body['status'] == 'NEW'
                        assert body['customerId'] == valid['customerId']
                        assert body['items'] == valid['items']
                        assert body['shippingAddress'] == valid['shippingAddress']
                        UUID(body['id'])
                    else:
                        assert content_type.startswith('application/problem+json')
                        assert body['status'] == expected
                        assert {'type', 'title', 'status', 'detail'} <= body.keys()
                    lines.append(f'PASS {name}: POST {path} -> {response.status}; {content_type}')
                finally:
                    connection.close()
        finally:
            server.shutdown()
            thread.join(timeout=5)
    lines.append(f'PASS: {len(cases)} checks; server stopped and socket closed.')
    (root / 'docs/http_smoke_test.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
