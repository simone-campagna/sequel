"""
Fibonacci Sequence
"""

import collections

from ..lazy import gmpy2
from .base import Sequence, Function, Iterator
from .trait import Trait


__all__ = [
    'Fib01',
    'Fib11',
    'Lucas',
    'Fib',
    'make_fibonacci',
]


class Fib01(Function):
    __traits__ = [Trait.POSITIVE]

    def __call__(self, i):
        return gmpy2.fib(i)

    def description(self):
        return """f(n) := f(n - 2) + f(n - 1), f(0) := 0, f(1) := 1 (Fibonacci sequence [0, 1, 1, 2, 3, 5, 8, ...])"""

    @classmethod
    def register(cls):
        cls.register_factory('fib01', cls)


class Fib11(Function):
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO]

    def __call__(self, i):
        return gmpy2.fib(i + 1)

    def description(self):
        return """f(n) := f(n - 2) + f(n - 1), f(0) := 1, f(1) := 1 (Fibonacci sequence [1, 1, 2, 3, 5, 8, ...])"""

    @classmethod
    def register(cls):
        cls.register_factory('fib11', cls)


class Lucas(Function):
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO, Trait.INJECTIVE]

    def __call__(self, i):
        return gmpy2.lucas(i)

    @classmethod
    def register(cls):
        cls.register_factory('lucas', cls)


class Fib(Iterator):
    def __init__(self, first=0, second=1):
        self.__first = first
        self.__second = second

    @property
    def first(self):
        return self.__first

    @property
    def second(self):
        return self.__second

    def __iter__(self):
        f, s = self.__first, self.__second
        while True:
            yield f
            f, s = s, f + s

    def description(self):
        return """f(n) := f(n - 2) + f(n - 1), f(0) := 2, f(1) := 1 (Fibonacci sequence [2, 1, 3, 4, 7, ...])"""

    def equals(self, other):
        if super().equals(other):
            return self.first == other.first and self.second == other.second
        else:
            return False


def make_fibonacci(first=0, second=1):
    fs = (first, second)
    if fs == (0, 1):
        return Sequence.get_registry()['fib01']
    elif fs == (1, 1):
        return Sequence.get_registry()['fib11']
    elif fs == (2, 1):
        return Sequence.get_registry()['lucas']
    else:
        return Fib(first, second)
