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
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO, Trait.INCREASING, Trait.FAST_GROWING]

    def __call__(self, i):
        return gmpy2.fac(i)

    @classmethod
    def declare(cls):
        cls.declare_factory('factorial', cls,
            oeis='A000142',
            description='n! : f(n) := n * f(n - 1), f(0) := 1',
        )


class DoubleFactorial(Function):
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO, Trait.INCREASING, Trait.FAST_GROWING]

    def __call__(self, i):
        return gmpy2.double_fac(i)

    @classmethod
    def declare(cls):
        cls.declare_factory('dfactorial', cls,
            description='n!! :: f(n) := n * f(n - 2), f(0) := 2 + n % 2',
        )


class DoubleFactorialEven(Function):
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO, Trait.INCREASING, Trait.FAST_GROWING]

    def __call__(self, i):
        return gmpy2.double_fac(2 * i)

    @classmethod
    def declare(cls):
        cls.declare_factory('dfactorial_even', cls,
            oeis='A000165',
            description='f(n) := double_factorial(2 * n)',
        )


class DoubleFactorialOdd(Function):
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO, Trait.INCREASING, Trait.FAST_GROWING]

    def __call__(self, i):
        return gmpy2.double_fac(2 * i + 1)

    @classmethod
    def declare(cls):
        cls.declare_factory('dfactorial_odd', cls,
            oeis='A001147',
            description='f(n) := double_factorial(2 * n + 1)',
        )


class Derangements(Function):
    __traits__ = [Trait.POSITIVE, Trait.FAST_GROWING]
    #
    #      ___ n             n!      
    #      \                ____    
    # !n = /__     (-1)^i *        = (-1)^n * n * !(n-1)
    #      i = 0             i!    
    #

    def __call__(self, i):
        last = 1
        for x in range(i + 1):
            last = (-1)**x + x * last
        return last

    def __iter__(self):
        i = 0
        last = 1
        while True:
            yield last
            i += 1
            last = (-1)**i + i * last
        yield from super().__iter__()

    @classmethod
    def declare(cls):
        cls.declare_factory('derangements', cls,
            oeis='A000166',
            description='!n :: f(n) := sum (-1)^i * i! / n! == (-1)^n + n * f(n-1)',
        )
