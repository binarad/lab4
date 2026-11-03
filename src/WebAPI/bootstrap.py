import argparse
import json
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, HTTPServer
from uuid import uuid4
from src.Application.create_order import Clock, CreateOrder, IdGenerator
from src.Domain.ports import OrderRepository
from src.Infrastructure.adapters import (
    InMemoryOrderRepository, MemoryOrderStore, SystemClock, UuidGenerator,
)
from .container import Container, Lifetime
from .controller import OrderController, problem


def build_container():
    container = Container()
    # Singleton: shared process data protected by a lock, without request state.
    # Scoped storage would discard orders at the end of every request.
    container.register(MemoryOrderStore, lambda s: MemoryOrderStore(), Lifetime.SINGLETON)
    # Singleton: clock is stateless; per-request creation adds no isolation.
    container.register(Clock, lambda s: SystemClock(), Lifetime.SINGLETON)
    # Transient: lightweight independent generator without reusable state.
    container.register(IdGenerator, lambda s: UuidGenerator(), Lifetime.TRANSIENT)
    # Scoped: one adapter per request, suitable for a future unit of work.
    container.register(OrderRepository,
                       lambda s: InMemoryOrderRepository(s.resolve(MemoryOrderStore)),
                       Lifetime.SCOPED)
    # Scoped: use case shares request lifetime with its repository.
    container.register(CreateOrder,
                       lambda s: CreateOrder(s.resolve(OrderRepository),
                                             s.resolve(Clock), s.resolve(IdGenerator)),
                       Lifetime.SCOPED)
    # Transient: thin controller has no independent reusable state.
    container.register(OrderController,
                       lambda s: OrderController(s.resolve(CreateOrder)), Lifetime.TRANSIENT)
    return container


def example_payload():
    return {
        'customerId': '550e8400-e29b-41d4-a716-446655440000',
        'items': [{'product': {
            'productId': '497f6eca-6276-4993-bfeb-53cbbbaf6080',
            'name': 'Mechanical Keyboard', 'unitPrice': 99.99}, 'quantity': 2}],
        'shippingAddress': {'city': 'Kyiv', 'street': 'Khreshchatyk 1',
                            'postalCode': '01001', 'country': 'Ukraine'},
    }


def reject_non_json_constant(value):
    raise ValueError(f'Invalid JSON constant: {value}')


def make_handler(container):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != '/orders':
                self._respond(404, problem(404, 'Not Found', 'Route not found.'))
                return
            if self.headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
                self._respond(415, problem(415, 'Unsupported Media Type', 'Expected application/json.'))
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                self._respond(400, problem(400, 'Bad Request', 'Invalid Content-Length.'))
                return
            if not 1 <= length <= 262144:
                self._respond(413, problem(413, 'Content Too Large', 'Body must contain 1 to 262144 bytes.'))
                return
            try:
                payload = json.loads(self.rfile.read(length), parse_float=Decimal,
                                     parse_constant=reject_non_json_constant)
            except (ValueError, UnicodeDecodeError, RecursionError):
                self._respond(400, problem(400, 'Bad Request', 'Invalid JSON.'))
                return
            with container.create_scope() as scope:
                status, body = scope.resolve(OrderController).post(payload)
            self._respond(status, body)

        def _respond(self, status, body):
            data = json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
            self.send_response(status)
            media = 'application/problem+json' if status >= 400 else 'application/json'
            self.send_header('Content-Type', media + '; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('X-Trace-ID', str(uuid4()))
            self.end_headers()
            self.wfile.write(data)
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--serve', action='store_true')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    container = build_container()
    if args.serve:
        with HTTPServer(('127.0.0.1', args.port), make_handler(container)) as server:
            print(f'POST http://127.0.0.1:{args.port}/orders', flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
    else:
        with container.create_scope() as scope:
            status, body = scope.resolve(OrderController).post(example_payload())
            print(json.dumps({'http_status': status, 'body': body}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
