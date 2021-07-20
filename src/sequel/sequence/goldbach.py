"""
Goldbach-related sequences
"""

import itertools

from ..lazy import gmpy2
from .base import EnumeratedSequence, StashMixin, Function
from .trait import Trait

__all__ = [
    'GoldbachPartitionsCount',
    'GoldbachPartitionsIncreasingValues',
    'GoldbachPartitionsSmallestPrimes',
]


class GoldbachPartitionsCount(StashMixin, Function):
    __traits__ = [Trait.POSITIVE, Trait.SLOW]
    __stash__ = None

    def __call__(self, i):
        gmpy2_module = gmpy2.module()
        is_prime = gmpy2_module.is_prime
        next_prime = gmpy2_module.next_prime
        p = 2
        e = 2 + i * 2
        e_half = 1 + i
        count = 0
        while p <= e_half:
            if is_prime(e - p):
                count += 1
            p = next_prime(p)
        return count
        
    @classmethod
    def _create_stash(cls):
        return [
            0, 1, 1, 1, 2, 1, 2, 2, 2, 2, 3, 3, 3, 2, 3, 2, 4, 4, 2, 3, 4, 3, 4, 5, 4, 3, 5, 3, 4, 6,
            3, 5, 6, 2, 5, 6, 5, 5, 7, 4, 5, 8, 5, 4, 9, 4, 5, 7, 3, 6, 8, 5, 6, 8, 6, 7, 10, 6, 6,
            12, 4, 5, 10, 3, 7, 9, 6, 5, 8, 7, 8, 11, 6, 5, 12, 4, 8, 11, 5, 8, 10, 5, 6, 13, 9, 6,
            11, 7, 7, 14, 6, 8, 13, 5, 8, 11, 7, 9, 13, 8, 9, 14, 7, 7, 19, 6, 8, 13, 7, 9, 11, 7,
            7, 12, 9, 7, 15, 9, 9, 18, 8, 9, 16, 6, 9, 16, 9, 8, 14, 10, 9, 16, 8, 9, 19, 7, 11, 16,
            7, 14, 16, 8, 12, 17, 10, 8, 19, 8, 11, 21, 9, 10, 15, 8, 12, 17, 9, 10, 15, 11, 11, 20,
            7, 10, 24, 6, 11, 19, 9, 13, 17, 10, 9, 16, 13, 10, 20, 9, 10, 22, 8, 14, 18, 8, 14, 18,
            10, 11, 22, 13, 10, 19, 12, 9, 27, 11, 11, 21, 7, 14, 17, 11, 13, 20, 13, 11, 21, 10,
            11, 30, 11, 12, 21, 9, 14, 19, 13, 11, 21, 14, 13, 21, 12, 13, 27, 12, 12, 24, 9, 16,
            28, 12, 13, 24, 15, 13, 23, 14, 11, 29, 11, 14, 23, 9, 19, 22, 13, 13, 23, 13, 15, 27,
            15, 14, 32, 11, 14, 23, 11, 17, 24, 11, 15, 25, 14, 17, 22, 13, 14, 30, 10, 13, 30, 11,
            19, 23, 11, 11, 23, 18, 14, 24, 13, 13, 31, 11, 16, 26, 12, 19, 25, 12, 13, 29, 16, 15,
            27, 12, 15, 32, 12, 14, 27, 13, 20, 26, 15, 19, 26, 18, 17, 31, 12, 16, 41, 10, 14, 28,
            15, 18, 25, 17, 16, 27, 21, 15, 29, 13, 19, 41, 14, 16, 31, 11, 21, 33, 15, 17, 28, 21,
            16, 30, 16, 16, 39, 11, 19, 30, 14, 24, 31, 18, 19, 24, 16, 17, 37, 14, 15, 39, 14, 15,
            31, 15, 21, 31, 15, 19, 29, 18, 19, 31, 18, 19, 39, 14, 17, 35, 15, 21, 30, 17, 17, 31,
            26, 18, 32, 16, 15, 44, 14, 18, 30, 15, 22, 34, 17, 14, 38, 21, 16, 32, 16, 14, 39, 18,
            20, 34, 17, 20, 29, 16, 21, 34, 22, 22, 33, 18, 17, 51, 18, 17, 32, 15, 25, 31, 20, 19,
            39, 18, 17, 33, 17, 21, 46, 18, 19, 36, 14, 25, 39, 21, 18, 37, 23, 19, 34, 20, 19, 48,
            15, 17, 34, 15, 31, 31, 20, 18, 35, 23, 20, 47, 18, 18, 43, 17, 20, 36, 18, 24, 34, 18,
            20, 33, 25, 23, 37, 19, 22, 45, 16, 18, 45, 17, 27, 32, 17, 19, 35, 26, 17, 39, 20, 23,
            52, 13, 25, 37, 17, 28, 36, 18, 18, 42, 25, 23, 39, 18, 20, 51, 18, 22, 42, 18, 25, 36,
            21, 27, 40, 26, 22, 39, 19, 19, 57, 18, 24, 44, 19, 27, 37, 24, 24, 39, 25, 21, 40, 20,
            27, 54, 20, 21, 39, 18, 26, 48, 23, 18, 40, 28, 24, 44, 25, 25, 54, 16, 23, 41, 22, 34,
            47, 19, 23, 39, 26, 22, 49, 23, 20, 58, 18, 24, 38, 26, 27, 36, 19, 22, 42, 29, 25, 43,
            24, 22, 58, 18, 22, 49, 19, 26, 40, 20, 20, 43, 33, 23, 45, 24, 24, 54, 19, 28, 43, 20,
            32, 42, 22, 21, 49, 27, 25, 45, 22, 22, 55, 28, 25, 42, 18, 34, 44, 23, 26, 45, 28, 23,
            51, 20, 21, 68, 22, 26, 42, 21, 27, 40, 26, 25, 42, 27, 26, 46, 22, 29, 60, 23, 26, 49,
            20, 33, 53, 24, 24, 46, 30, 23, 46, 27, 26, 66, 21, 26, 53, 22, 41, 47, 25, 25, 45, 27,
            27, 54, 25, 22, 60, 22, 21, 41, 24, 33, 44, 27, 27, 48, 28, 27, 47, 23, 27, 61, 20, 24,
            59, 20, 30, 44, 24, 24, 45, 34, 27, 48, 23, 25, 58, 18, 30, 47, 20, 34, 41, 22, 23, 57,
            35, 25, 50, 22, 23, 60, 27, 28, 45, 20, 36, 49, 26, 34, 48, 33, 29, 47, 25, 24, 73, 22,
            30, 51, 26, 34, 52, 29, 25, 52, 31, 27, 50, 28, 32, 67, 27, 27, 51, 25, 33, 59, 23, 26,
            56, 31, 27, 48, 28, 27, 69, 22, 32, 47, 26, 46, 46, 21, 30, 51, 31, 28, 62, 24, 25, 72,
            29, 28, 51, 25, 38, 57, 23, 26, 47, 31, 34, 58, 28, 26, 71, 25, 27, 64, 24, 36, 53, 23,
            30, 47, 42, 35, 53, 27, 32, 65, 24, 35, 55, 29, 40, 60, 27, 27, 67, 35, 27, 52, 26, 28,
            76, 28, 31, 55, 27, 39, 54, 28, 34, 53, 37, 35, 56, 28, 31, 83, 24, 31, 56, 26, 37, 57,
            32, 28, 52, 34, 30, 55, 30, 32, 78, 26, 27, 68, 21, 38, 64, 29, 31, 53, 36, 25, 55, 35,
            33, 76, 25, 33, 55, 25, 48, 52, 27, 30, 55, 41, 29, 69, 32, 31, 73, 28, 27, 53, 33, 37,
            59, 25, 30, 52, 36, 36, 66, 31, 27, 75, 31, 31, 72, 28, 36, 53, 28, 27, 53, 46, 27, 58,
            33, 29, 76, 25, 34, 62, 28, 37, 54, 32, 28, 70, 38, 28, 54, 32, 29, 76, 34, 32, 53, 28,
            43, 58, 30, 36, 61, 38, 33, 61, 30, 28, 91, 35, 32, 63, 33, 36, 55, 36, 30, 58, 36, 30,
            66, 28, 35, 81, 30, 34, 58, 30, 39, 68, 28, 33, 65, 41, 30, 58, 34, 31, 83, 29, 35, 53,
            27, 48, 56, 26, 29, 62, 38, 32, 71, 33, 32, 82, 30, 32, 58, 30, 42, 59, 27, 28, 56, 37,
            44, 59, 35, 28, 84, 27, 35, 73, 28, 41, 59, 32, 32, 62, 49, 29, 64, 33, 33, 85, 30, 38,
            75, 25, 42,
        ]

    @classmethod
    def register(cls):
        cls.register_factory('g_part_count', cls,
            # oeis='A025018',
            description='g_part_count(n) := number of Goldbach partitions for 2 * n',
        )


class GoldbachPartitionsIncreasingValues(EnumeratedSequence):
    __stash__ = None
    __traits__ = [Trait.POSITIVE, Trait.NON_ZERO, Trait.INCREASING, Trait.PARTIALLY_KNOWN]

    @classmethod
    def _create_stash(cls):
        return [
            4, 6, 12, 30, 98, 220, 308, 556, 992, 2642, 5372, 7426, 43532, 54244, 63274, 113672, 128168,
            194428, 194470, 413572, 503222, 1077422, 3526958, 3807404, 10759922, 24106882, 27789878,
            37998938, 60119912, 113632822, 187852862, 335070838, 419911924, 721013438,
        ]

    @classmethod
    def register(cls):
        cls.register_factory('g_part_incr', cls,
            oeis='A025018',
            description='g_part_incr(n) := numbers k such that least prime in the Goldbach partition of k increases',
        )


class GoldbachPartitionsSmallestPrimes(EnumeratedSequence):
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
        cls.register_factory('g_part_pmin', cls,
            oeis='A025019',
            description='g_part_pmin(n) := smallest prime in Goldbach partition of g_part_incr(n)',
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
        print(GoldbachPartitionsIncreasingValues.__name__)
        print(gip)
        print(GoldbachPartitionsSmallestPrimes.__name__)
        print(gsp)
