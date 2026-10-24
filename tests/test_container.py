"""Separate composition tests: no HTTP server, files, database, or sockets."""
import unittest
from src.Application.create_order import Clock, CreateOrder, IdGenerator
from src.Domain.ports import OrderRepository
from src.WebAPI.bootstrap import build_container
from src.WebAPI.container import Container, Lifetime
from src.WebAPI.controller import OrderController


from tests.fixtures import valid_payload


class ContainerTests(unittest.TestCase):
    def test_scoped_is_shared_within_request_and_distinct_across_requests(self):
        container = build_container()
        with container.create_scope() as first, container.create_scope() as second:
            for key in (OrderRepository, CreateOrder):
                self.assertIs(first.resolve(key), first.resolve(key))
                self.assertIsNot(first.resolve(key), second.resolve(key))

    def test_singleton_clock_is_shared_across_requests(self):
        container = build_container()
        with container.create_scope() as first, container.create_scope() as second:
            self.assertIs(first.resolve(Clock), second.resolve(Clock))

    def test_transient_generator_is_always_new(self):
        with build_container().create_scope() as scope:
            self.assertIsNot(scope.resolve(IdGenerator), scope.resolve(IdGenerator))

    def test_complete_object_graph_creates_order(self):
        with build_container().create_scope() as scope:
            status, body = scope.resolve(OrderController).post(valid_payload())
            self.assertEqual(status, 201)
            self.assertEqual(body['totalAmount'], 199.98)

    def test_singleton_cannot_capture_scoped_dependency(self):
        container = Container()
        container.register('scoped', lambda s: object(), Lifetime.SCOPED)
        container.register('singleton', lambda s: s.resolve('scoped'), Lifetime.SINGLETON)
        with container.create_scope() as scope:
            with self.assertRaisesRegex(RuntimeError, 'cannot capture'):
                scope.resolve('singleton')

    def test_circular_dependency_is_rejected(self):
        container = Container()
        container.register('loop', lambda s: s.resolve('loop'), Lifetime.TRANSIENT)
        with container.create_scope() as scope:
            with self.assertRaisesRegex(RuntimeError, 'Circular'):
                scope.resolve('loop')

    def test_closed_scope_is_rejected(self):
        with build_container().create_scope() as scope:
            scope.resolve(Clock)
        with self.assertRaisesRegex(RuntimeError, 'closed'):
            scope.resolve(Clock)
