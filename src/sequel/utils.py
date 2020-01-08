"""
Utilities
"""

import importlib.util
import itertools
import os
import sys
import time

from .lazy import gmpy2, sympy


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
    'perfect_power',
    'linear_combination',
    'make_linear_combination',
    'make_power',
]


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


def item_repr(item):
    if gmpy2.is_integer(item):
        return int(item)
    else:
        return item


def assert_sequence_matches(sequence, items):
    try:
       result = not any(x != y for x, y in zip(sequence, items))
       # print("ok", result, sequence, items, list(zip(sequence, items)), [(x, y, x!=y) for x, y in zip(sequence, items)])
    except Exception as err:
       result = False
       # print("ko", err)
    if not result:
        raise AssertionError("sequence {} does not match items {}".format(
            str(sequence), [item_repr(x) for x in items]))


def perfect_power(n):
    if n < 0:
        result = sympy.perfect_power(-n)
        if result is not False:
            root, power = result
            if power % 2 == 1:
                return (-root, power)
            else:
                return False
    else:
        return sympy.perfect_power(n)


def linear_combination(items, input_items_list, min_components=1, max_components=4, rationals=True, max_elapsed=2.0, max_solutions=1):
    t0 = time.time()
    num_items = len(items)
    # creates cache:
    num_items = min(len(values) for values in input_items_list)
    all_values = [x[:num_items] for x in input_items_list]

    x_values = list(items)
    all_indices = [i for i, _ in enumerate(all_values)]
    zero_sol = [0 for _ in all_values]
    sympy_module = sympy.module()
    xs = sympy_module.symbols("x0:{}".format(num_items), integer=True)
    weights = [1.0 for _ in all_indices]

    last_index = len(all_indices)
    indices = all_indices[:]
    #niter = 0
    found_solutions = set()
    while True:
        #niter += 1
        if max_elapsed is not None and time.time() - t0 >= max_elapsed:
            break
        indices += tuple(i for i in all_indices if i not in indices)
        values = [all_values[index] for index in indices] + [x_values]
        augmented_matrix = sympy_module.Matrix(values).T
        m_rref, pivots = augmented_matrix.rref()
        if last_index in pivots:
            # x_values is not a linear combination of values
            return

        num = len(pivots)
        num_components = 0
        coeffs = []
        for c, pivot_c in enumerate(pivots):
            coeff = 0
            for r in range(num):
                if c < r:
                    assert m_rref[r, pivot_c] == 0
                coeff += m_rref[r, pivot_c] * m_rref[c, last_index]
            if coeff != 0:
                num_components += 1
            coeffs.append(coeff)
        #print("niter:", niter, num_components, "/", num)
        if max_components is None or num_components <= max_components:
            denoms = []
            for coeff in coeffs:
                if coeff.q != 1:
                    if rationals:
                        denoms.append(int(coeff.q))
                    else:
                        break
            else:
                if denoms:
                    denom = lcm(*denoms)
                else:
                    denom = 1
                coeffs = [int(coeff * denom) for coeff in coeffs]
                solution = zero_sol[:]
                for pivot, coeff in zip(pivots, coeffs):
                    solution[indices[pivot]] = coeff
                solution = tuple(solution)
                if solution not in found_solutions:
                    found_solutions.add(solution)
                    yield solution, denom
                    if max_solutions is not None and len(found_solutions) >= max_solutions:
                        return
                if num_components <= min_components:
                    return
        # recompute weights
        for i, index in enumerate(indices):
            if i in pivots:
                weights[index] += num_components / num
            else:
                weights[index] -= sum([1 for r in range(num) if m_rref[r, i] != 0]) / num

        #for pivot in pivots:
        indices = sorted(indices[:-1], key=lambda x: weights[x]) + indices[-1:]


def make_linear_combination(coeffs, items, denom=1):
    result = None
    if denom < 0:
        denom = -denom
        coeffs = [-c for c in coeffs]
    if denom > 1:
        g = gcd(denom, *coeffs)
        # print("<<<", denom, coeffs, g)
        if g > 1:
            denom //= g
            coeffs = [c // g for c in coeffs]
        # print(">>>", denom, coeffs)
    for coeff, item in zip(coeffs, items):
        if coeff != 0:
            sign = +1
            if coeff == 1:
                token = item
            elif coeff == -1:
                token = item
                sign = -1
            else:
                c = int(coeff)
                if result is not None and c < 0:
                    c = -c
                    sign = -1
                token = c * item
            if result is None:
                if sign >= 0:
                    result = token
                else:
                    result = -token
            else:
                if sign >= 0:
                    result += token
                else:
                    result -= token
    if denom != 1:
        result //= denom
    return result


def make_power(expr, power):
    if power == 1:
        return expr
    else:
        return expr ** power
