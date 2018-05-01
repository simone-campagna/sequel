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


Power(power=2).register('square', Trait.INJECTIVE, Trait.POSITIVE)
Power(power=3).register('cube', Trait.INJECTIVE, Trait.POSITIVE)


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


Arithmetic(start=0, step=2).register('even', Trait.INJECTIVE, Trait.POSITIVE)
Arithmetic(start=1, step=2).register('odd', Trait.INJECTIVE, Trait.POSITIVE)


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


Geometric(base=2).register('power_of_2', Trait.INJECTIVE, Trait.POSITIVE, Trait.NON_ZERO)
Geometric(base=3).register('power_of_3', Trait.INJECTIVE, Trait.POSITIVE, Trait.NON_ZERO)
Geometric(base=10).register('power_of_10', Trait.INJECTIVE, Trait.POSITIVE, Trait.NON_ZERO)


class ZeroOne(Function):
    def __call__(self, i):
        return i % 2

    def description(self):
        return """f(n) =  n % 2  => [0, 1, 0, 1, 0, 1, ...]"""


ZeroOne().register('zero_one', Trait.POSITIVE)
