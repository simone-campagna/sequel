"""
Catalan Sequence
"""

import collections

from .base import Function
from .trait import Trait


__all__ = [
    'Catalan',
]


class Catalan(Function):
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO]

    def __call__(self, i):
        gmpy2 = self.__gmpy2__
        return gmpy2.mpz(gmpy2.round_away(gmpy2.bincoef(2 * i, i) / (i + 1)))

    def description(self):
        return """f(n): n-th Catalan number"""

    @classmethod
    def register(cls):
        cls.register_factory('catalan', cls)
