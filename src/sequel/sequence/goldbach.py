"""
Goldbach-related sequences
"""

import itertools

from ..lazy import gmpy2
from .base import EnumeratedSequence
from .trait import Trait

__all__ = [
    'GoldbachIncreasingPartition',
    'GoldbachSmallestPrime',
]


class GoldbachIncreasingPartition(EnumeratedSequence):
    __stash__ = None
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO, Trait.INCREASING, Trait.PARTIALLY_KNOWN]

    @classmethod
    def _create_stash(cls):
        return [
            4, 6, 12, 30, 98, 220, 308, 556, 992, 2642, 5372, 7426, 43532, 54244, 63274, 113672, 128168,
            194428, 194470, 413572, 503222, 1077422, 3526958, 3807404, 10759922, 24106882, 27789878,
            37998938, 60119912, 113632822, 187852862, 335070838, 419911924,
        ]

    @classmethod
    def register(cls):
        cls.register_factory('goldbach_increasing_partition', cls,
            oeis='A025018',
            description='goldbach_increasing_partition(n) := numbers k such that least prime in the Goldbach partition of k increases',
        )


class GoldbachSmallestPrime(EnumeratedSequence):
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO, Trait.INCREASING, Trait.PARTIALLY_KNOWN]
    __stash__ = None

    @classmethod
    def _create_stash(cls):
        return [
            2, 3, 5, 7, 19, 23, 31, 47, 73, 103, 139, 173, 211, 233, 293, 313, 331, 359, 383, 389,
            523, 601, 727, 751, 829, 929, 997, 1039, 1093, 1163, 1321, 1427, 1583, 1789, 1861, 1877,
            1879, 2029, 2089, 2803, 3061, 3163, 3457, 3463, 3529, 3613, 3769, 3917, 4003, 4027, 4057,
        ]

    @classmethod
    def register(cls):
        cls.register_factory('goldbach_smallest_prime', cls,
            oeis='A025019',
            description='goldbach_smallest_prime(n) := smallest prime in Goldbach partition of goldbach_increasing_partition(n)',
        )


def create_goldbach_smallest_partition_stash(start=None, stop_when=None):
    if start is None:
        start = []
    lst = list(start)
    gmpy2_module = gmpy2.module()
    is_prime = gmpy2_module.is_prime
    next_prime = gmpy2_module.next_prime
    def smallest_goldbach_prime(n):
        n_half = n // 2
        p = 2
        while not is_prime(n - p):
            p = next_prime(p)
            if p > n_half:
                return
        return p

    if stop_when is None:
        stop_when = lambda x, y: False

    record = 0
    lst = []
    print("start = [", flush=True)
    try:
        for i in itertools.count(4, 2):
            p = smallest_goldbach_prime(i)
            if p > record:
                lst.append((i, p))
                print("    ({}, {}),".format(i, p), flush=True)
                record = p
            if stop_when(i, p):
                break
    except KeyboardInterrupt:
        pass
    finally:
        print("]", flush=True)
        gip = [int(x[0]) for x in lst]
        gsp = [int(x[1]) for x in lst]
        print(GoldbachIncreasingPartition.__name__)
        print(gip)
        print(GoldbachSmallestPrime.__name__)
        print(gsp)
