"""
Fibonacci Sequence
"""

import collections

from ..lazy import gmpy2
from ..utils import gcd
from .base import Sequence, Function, Iterator
from .trait import Trait


__all__ = [
    'Fib01',
    'Fib11',
    'Lucas',
    'Fib',
    'make_fibonacci',
    'Trib',
    'make_tribonacci',
]


class Fib01(Function):
    __traits__ = [Trait.POSITIVE, Trait.INCREASING]

    def __call__(self, i):
        return gmpy2.fib(i)

    def description(self):
        return """f(n) := f(n - 2) + f(n - 1), f(0) := 0, f(1) := 1 (Fibonacci sequence [0, 1, 1, 2, 3, 5, 8, ...])"""

    @classmethod
    def register(cls):
        cls.register_factory('fib01', cls)


class Fib11(Function):
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO, Trait.INCREASING]

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
    def __init__(self, first=0, second=1, scale=1):
        self.__first = first
        self.__second = second
        self.__scale = scale

    @property
    def first(self):
        return self.__first

    @property
    def second(self):
        return self.__second

    @property
    def scale(self):
        return self.__scale

    def __iter__(self):
        f, s, scale = self.__first, self.__second, self.__scale
        while True:
            yield f
            f, s = s, f + scale * s

    def description(self):
        return """f(n) := {obj.scale} * f(n - 1) + f(n - 2), f(0) := {obj.first}, f(1) := {obj.second}""".format(
            obj=self)

    def equals(self, other):
        if super().equals(other):
            return self.first == other.first and self.second == other.second and self.scale == other.scale
        else:
            return False

    @classmethod
    def register(cls):
        cls.register_factory('pell', lambda: cls(0, 1, 2).set_traits(Trait.INJECTIVE, Trait.POSITIVE, Trait.INCREASING))


class Trib(Iterator):
    def __init__(self, first=0, second=1, third=1):
        self.__first = first
        self.__second = second
        self.__third = third

    @property
    def first(self):
        return self.__first

    @property
    def second(self):
        return self.__second

    @property
    def third(self):
        return self.__third

    def __iter__(self):
        f, s, t = self.__first, self.__second, self.__third
        while True:
            yield f
            f, s, t = s, t, t + f + s

    def description(self):
        return """f(n) := f(n - 1) + f(n - 2) + f(n - 3), f(0) := {obj.first}, f(1) := {obj.second}, f(2) := {obj.third}""".format(
            obj=self)

    def equals(self, other):
        if super().equals(other):
            return self.first == other.first and self.second == other.second and self.third == other.third
        else:
            return False

    @classmethod
    def register(cls):
        cls.register_factory('tribonacci', lambda: cls(0, 1, 1).set_traits(Trait.POSITIVE, Trait.INCREASING))


def make_fibonacci(first=0, second=1, scale=1):
    g = gcd(first, second,)
    if abs(g) > 1:
        first //= g
        second //= g
    key = (first, second, scale)
    if key == (0, 1, 1):
        seq = Sequence.get_registry()['fib01']
    elif key == (1, 1, 1):
        seq = Sequence.get_registry()['fib11']
    elif key == (2, 1, 1):
        seq = Sequence.get_registry()['lucas']
    else:
        seq = Fib(first, second, scale)
    if g != 1:
        return g * seq
    else:
        return seq


def make_tribonacci(first=0, second=1, third=1):
    g = gcd(first, second,)
    if abs(g) > 1:
        first //= g
        second //= g
        return g * Trib(first, second, third)
    else:
        return Trib(first, second, third)


