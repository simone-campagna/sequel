"""
Repunit Sequence
"""

import itertools
import gmpy2

from .base import Sequence
from .trait import Trait

__all__ = [
    'Repunit',
]


class Repunit(Sequence):
    def __init__(self, base=10):
        self.__base = gmpy2.mpz(base)

    def description(self):
        return "f(n) := the repunit sequence in base {}".format(self.__base)

    @property
    def base(self):
        return self.__base

    def __call__(self, i):
        return ((self.__base ** (i + 1)) - 1) // (self.__base - 1)

    def __iter__(self):
        s = 1
        base = self.__base
        for i in itertools.count(start=1):
            yield s
            s += base ** i


Repunit().register('repunit').set_traits(Trait.POSITIVE, Trait.NON_ZERO, Trait.INJECTIVE)


class Demlo(Sequence):
    def description(self):
        return "f(n) := the Demlo numbers, defined as repunit ** 2"

    def __call__(self, i):
        return (((10 ** (i + 1)) - 1) // (10 - 1)) ** 2

    def __iter__(self):
        s = 1
        base = 10
        for i in itertools.count(start=1):
            yield s ** 2
            s += base ** i


#(Repunit() ** 2).register('demlo').set_traits(Trait.POSITIVE, Trait.NON_ZERO, Trait.INJECTIVE).set_doc("f(n) := the Demlo numbers, defined as repunit ** 2")
Demlo().register('demlo').set_traits(Trait.POSITIVE, Trait.NON_ZERO, Trait.INJECTIVE)

