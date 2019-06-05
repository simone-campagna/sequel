"""
Miscellanea
"""

import collections

from .base import Function
from .trait import Trait

__all__ = [
    'Arithmetic',
    'Geometric',
    'Power',
    'ZeroOne',
]


class Power(Function):
    def __init__(self, power):
        self.__power = power

    @property
    def power(self):
        return self.__power

    def __call__(self, i):
        return i ** self.__power

    def description(self):
        return """f(n) = n ** {}""".format(self.__power)

    def equals(self, other):
        if super().equals(other):
            return self.power == other.power
        else:
            return False

    @classmethod
    def register(cls):
        cls.register_factory('square', lambda: cls(power=2).set_traits(Trait.INJECTIVE, Trait.POSITIVE))
        cls.register_factory('cube', lambda: cls(power=3).set_traits(Trait.INJECTIVE, Trait.POSITIVE))


class Arithmetic(Function):
    def __init__(self, start=0, step=1):
        self.__start = start
        self.__step = step

    @property
    def start(self):
        return self.__start

    @property
    def step(self):
        return self.__step

    def __call__(self, i):
        return self.__start + i * self.__step

    def description(self):
        return """f(n) = {} + {} * n""".format(self.__start, self.__step)

    def equals(self, other):
        if super().equals(other):
            return self.start == other.start and self.step == other.step
        else:
            return False

    @classmethod
    def register(cls):
        cls.register_factory('even', lambda: cls(start=0, step=2).set_traits(Trait.INJECTIVE, Trait.POSITIVE))
        cls.register_factory('odd', lambda: cls(start=1, step=2).set_traits(Trait.INJECTIVE, Trait.POSITIVE))


class Geometric(Function):
    def __init__(self, base):
        self.__base = base

    @property
    def base(self):
        return self.__base

    def __call__(self, i):
        return self.__base ** i

    def description(self):
        return """f(n) = {} ** n""".format(self.__base)

    def equals(self, other):
        if super().equals(other):
            return self.base == other.base
        else:
            return False

    @classmethod
    def register(cls):
        cls.register_factory('power_of_2', lambda: cls(base=2).set_traits(Trait.INJECTIVE, Trait.POSITIVE, Trait.NON_ZERO))
        cls.register_factory('power_of_3', lambda: cls(base=3).set_traits(Trait.INJECTIVE, Trait.POSITIVE, Trait.NON_ZERO))
        cls.register_factory('power_of_10', lambda: cls(base=10).set_traits(Trait.INJECTIVE, Trait.POSITIVE, Trait.NON_ZERO))


class ZeroOne(Function):
    __traits__ = [Trait.POSITIVE]

    def __call__(self, i):
        return i % 2

    def description(self):
        return """f(n) =  n % 2  => [0, 1, 0, 1, 0, 1, ...]"""

    @classmethod
    def register(cls):
        cls.register_factory('zero_one', cls)
