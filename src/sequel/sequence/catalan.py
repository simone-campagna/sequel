"""
Catalan Sequence
"""

import collections

import gmpy2

from .base import Function
from .trait import Trait


__all__ = [
    'Catalan',
]


class Catalan(Function):
    def __call__(self, i):
        return gmpy2.mpz(gmpy2.round_away(gmpy2.bincoef(2 * i, i) / (i + 1)))

    def description(self):
        return """f(n): n-th Catalan number"""


Catalan().register('catalan').set_traits(Trait.POSITIVE, Trait.NON_ZERO)
