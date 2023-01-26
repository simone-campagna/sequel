"""
Factorial Sequence
"""

import collections

from ..lazy import gmpy2
from .base import Function
from .trait import Trait


__all__ = [
    'Factorial',
    'DoubleFactorial',
    'DoubleFactorialEven',
    'DoubleFactorialOdd',
    'Derangements',
]


class Factorial(Function):
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO, Trait.INCREASING]

    def __call__(self, i):
        return gmpy2.fac(i)

    @classmethod
    def declare(cls):
        cls.declare_factory('factorial', cls,
            oeis='A000142',
            description='n! : f(n) := n * f(n - 1), f(0) := 1',
        )


class DoubleFactorial(Function):
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO, Trait.INCREASING]

    def __call__(self, i):
        return gmpy2.double_fac(i)

    @classmethod
    def declare(cls):
        cls.declare_factory('dfactorial', cls,
            description='n!! : f(n) := n * f(n - 2), f(0) := 2 + n % 2',
        )


class DoubleFactorialEven(Function):
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO, Trait.INCREASING]

    def __call__(self, i):
        return gmpy2.double_fac(2 * i)

    @classmethod
    def declare(cls):
        cls.declare_factory('dfactorial_even', cls,
            oeis='A000165',
            description='f(n) := double_factorial(2 * n)',
        )


class DoubleFactorialOdd(Function):
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO, Trait.INCREASING]

    def __call__(self, i):
        return gmpy2.double_fac(2 * i + 1)

    @classmethod
    def declare(cls):
        cls.declare_factory('dfactorial_odd', cls,
            oeis='A001147',
            description='f(n) := double_factorial(2 * n + 1)',
        )


class Derangements(Function):
    __traits__ = [Trait.POSITIVE, Trait.INCREASING]

    def __call__(self, i):
        # res = 0
        # fac = gmpy2.fac
        # fi = fac(i)
        # for k in range(i + 1):
        #     res += (-1)**k * fi / fac(k)
        # return res
        if i < 1:
            return 1
        e = gmpy2.exp(1.0)
        return gmpy2.mpz(gmpy2.trunc((gmpy2.fac(i) + 1) / e))

    @classmethod
    def declare(cls):
        cls.declare_factory('derangements', cls,
            oeis='A000166',
            description='!n - f(n) := sum (-1)^i * i! / n!',
        )
