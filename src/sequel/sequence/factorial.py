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

    @classmethod
    def declare(cls):
        cls.declare_factory('factorial', cls,
            oeis='A000142',
            description='f(n) := n * f(n - 1), f(0) := 1',
        )
