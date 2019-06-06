"""
Catalan Sequence
"""

import collections

from ..lazy import gmpy2
from .base import Function
from .trait import Trait


__all__ = [
    'Catalan',
]


class Catalan(Function):
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO]

    def __call__(self, i):
        gmpy2_module = gmpy2.module()
        return gmpy2_module.mpz(gmpy2_module.round_away(gmpy2_module.bincoef(2 * i, i) / (i + 1)))

    def description(self):
        return """f(n): n-th Catalan number"""

    @classmethod
    def register(cls):
        cls.register_factory('catalan', cls)
