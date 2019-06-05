"""
Factorial Sequence
"""

import collections

from .base import Function
from .trait import Trait
from ..utils import gmpy2


__all__ = [
    'Factorial',
]


class Factorial(Function):
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO]

    def __call__(self, i):
        return self.__gmpy2__.fac(i)

    def description(self):
        return """f(n) := n * f(n - 1), f(0) := 1"""

    @classmethod
    def register(cls):
        cls.register_factory('factorial', cls)
