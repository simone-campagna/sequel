"""
Factorial Sequence
"""

import collections

from ..lazy import gmpy2
from .base import Function
from .trait import Trait


__all__ = [
    'Factorial',
]


class Factorial(Function):
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO, Trait.INCREASING]

    def __call__(self, i):
        return gmpy2.fac(i)

    def description(self):
        return """f(n) := n * f(n - 1), f(0) := 1"""

    @classmethod
    def register(cls):
        cls.register_factory('factorial', cls)
