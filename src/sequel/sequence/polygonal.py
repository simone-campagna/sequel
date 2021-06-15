"""
Miscellanea
"""

import collections

from .base import Function
from .trait import Trait

__all__ = [
    'Polygonal',
]


class Polygonal(Function):
    def __init__(self, sides):
        self.__sides = sides

    @property
    def sides(self):
        return self.__sides

    def __call__(self, i):
        return i + ((self.__sides - 2) * i * (i - 1) // 2)

    def description(self):
        if self.__sides == 3:
            name = "triangular"
        elif self.__sides == 4:
            name = "square"
        elif self.__sides == 5:
            name = "pentagonal"
        elif self.__sides == 6:
            name = "hexagonal"
        else:
            name = "{}-polygonal".format(self.__sides)
        return """f(n) := the n-th {} number""".format(name)

    def equals(self, other):
        if super().equals(other):
            return self.sides == other.sides
        else:
            return False

    @classmethod
    def register(cls):
        cls.register_factory('triangular', lambda: cls(3).set_traits(Trait.INJECTIVE, Trait.POSITIVE, Trait.INCREASING),
            oeis='A000217',
        )
        cls.register_factory('pentagonal', lambda: cls(5).set_traits(Trait.INJECTIVE, Trait.POSITIVE, Trait.INCREASING),
            oeis='A000326',
        )
        cls.register_factory('hexagonal', lambda: cls(6).set_traits(Trait.INJECTIVE, Trait.POSITIVE, Trait.INCREASING),
            oeis='A000384',
        )
