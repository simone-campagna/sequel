"""
Factorial Sequence
"""

import collections

import gmpy2

from .base import Function
from .trait import Trait

__all__ = [
    'Factorial',
]


class Factorial(Function):
    def __call__(self, i):
        return gmpy2.fac(i)

    def description(self):
        return """f(n) := n * f(n - 1), f(0) := 1"""


Factorial().register('factorial').set_traits(Trait.POSITIVE, Trait.NON_ZERO)
