"""
Utilities
"""

import itertools
import os
import sys

import gmpy2
import sympy


__all__ = [
    'gcd',
    'lcm',
    'factorize',
    'divisors',
    'affine_transformation',
    'get_power',
    'get_base',
    'sequence_matches',
    'assert_sequence_matches',
    'is_integer',
]


_MPZ_CLASS = type(gmpy2.mpz(1))

def is_integer(value):
    return isinstance(value, (int, _MPZ_CLASS))


def gcd(item0, *items):
    """Returns the GCD for multiple items"""
    if not items:
        return item0
    result = item0
    for item in items:
        result = gmpy2.gcd(result, item)
        if result == 1:
            break
    return int(result)


def lcm(item0, *items):
    """Returns the LCM for multiple items"""
    if not items:
        return item0
    result = item0
    for item in items:
        result = gmpy2.lcm(result, item)
    return int(result)


def factorize(n):
    """Yields prime factors and multiplicity"""
    if n in {0, 1}:
        return
    yield from sorted(sympy.factorint(n).items(), key=lambda x: x[0])


def divisors(n):
    """Yields all divisors of n"""
    yield from sympy.divisors(n)


def affine_transformation(x, y):
    """Try to find m, q | m * x[i] + q == y[i]"""
    x = tuple(x)
    y = tuple(y)
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    s_x = set(x)
    if len(s_x) == 1:
        x0, y0 = x[0], y[0]
        if not all(yi == y0 for yi in y[1:]):
            return
        if x0 == 0:
            return
        else:
            return divmod(y0, x0)
    elif len(s_x) >= 2:
        for (i0, x0), (i1, x1) in itertools.combinations(enumerate(x), 2):
            if x0 != x1:
                y0 = y[i0]
                y1 = y[i1]
                m, rem = divmod(y0 - y1, x0 - x1)
                if rem != 0:
                    return
                q = y0 - m * x0
                for xi, yi in zip(x, y):
                    if m * xi + q != yi:
                        return
                return (m, q)
        

def get_power(x):
    """Returns p | i ** p == x[i], or None"""
    x = tuple(x)
    if len(x) > 2 and x[0] == 0 and x[1] == 1:
        f, power = gmpy2.remove(x[2], 2)
        if f != 1:
            return
        for i, xi in enumerate(x):
            if i ** power != xi:
                return
        return power


def get_base(x):
    """Returns b | b ** i == x[i], or None"""
    x = tuple(x)
    if len(x) >= 2 and x[0] == 1:
        base = x[1]
        for i, xi in enumerate(x):
            if base ** i != xi:
                return
        return base


def sequence_matches(sequence, items):
    try:
        return all(x == y for x, y in zip(sequence, items))
    except:
        return False


def assert_sequence_matches(sequence, items):
    try:
       result = not any(x != y for x, y in zip(sequence, items))
       # print("ok", result, sequence, items, list(zip(sequence, items)), [(x, y, x!=y) for x, y in zip(sequence, items)])
    except Exception as err:
       result = False
       # print("ko", err)
    if not result:
        raise AssertionError("sequence {} does not match items {}".format(
            str(sequence), [int(x) for x in items]))
