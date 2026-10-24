"""Small educational DI container with constructor factories and three lifetimes.

It is used exclusively by the composition root, never by business code.
Scopes and registrations are configured before the sequential demo server runs.
Resources requiring dispose/close are outside the scope of this container.
"""
from dataclasses import dataclass
from enum import Enum


class Lifetime(Enum):
    TRANSIENT = 'Transient'
    SCOPED = 'Scoped'
    SINGLETON = 'Singleton'


@dataclass(frozen=True)
class Registration:
    factory: object
    lifetime: Lifetime


class Container:
    def __init__(self):
        self._registrations = {}
        self._singletons = {}
        self._sealed = False

    def register(self, key, factory, lifetime):
        if self._sealed:
            raise RuntimeError('Container configuration is already sealed.')
        if key in self._registrations:
            raise ValueError('Duplicate registration.')
        self._registrations[key] = Registration(factory, lifetime)

    def create_scope(self):
        self._sealed = True
        return Scope(self)


class Scope:
    def __init__(self, container):
        self._container = container
        self._instances = {}
        self._stack = []
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._instances.clear()
        self._closed = True

    def resolve(self, key):
        if self._closed:
            raise RuntimeError('Scope is closed.')
        registration = self._container._registrations[key]
        if key in self._stack:
            raise RuntimeError('Circular dependency.')
        if registration.lifetime is Lifetime.SCOPED:
            if any(self._container._registrations[k].lifetime is Lifetime.SINGLETON
                   for k in self._stack):
                raise RuntimeError('Singleton cannot capture a Scoped dependency.')
            cache = self._instances
        elif registration.lifetime is Lifetime.SINGLETON:
            cache = self._container._singletons
        else:
            cache = None
        if cache is not None and key in cache:
            return cache[key]
        self._stack.append(key)
        try:
            instance = registration.factory(self)
            if cache is not None:
                cache[key] = instance
            return instance
        finally:
            self._stack.pop()
