import sys
import os

import sequel
from sequel import sequence
from sequel.utils import (
    gcd, lcm, factorize, divisors, affine_transformation,
    get_power, get_base, perfect_power,
    linear_combination,
)

import pytest


@pytest.mark.parametrize("values, result", [
    ([20], 20),
    ([20, 30], 10),
    ([20, 30, 40], 10),
    ([0, 20, 30, 40], 10),
    ([1, 20, 30, 40], 1),
    ([20, 40, 60], 20),
])
def test_gcd(values, result):
    assert gcd(*values) == result
    for x in values:
        assert x % result == 0


@pytest.mark.parametrize("values, result", [
    ([20], 20),
    ([20, 30], 60),
    ([20, 30, 40], 120),
    ([0, 20, 30, 40], 0),
    ([1, 20, 30, 40], 120),
    ([20, 30, 60], 60),
])
def test_lcm(values, result):
    assert lcm(*values) == result
    for x in values:
        if x != 0:
            assert result % x == 0


@pytest.mark.parametrize("n, result", [
    (0, []),
    (1, []),
    (2, [(2, 1)]),
    (4, [(2, 2)]),
    (29, [(29, 1)]),
    (144, [(2, 4), (3, 2)]),
    (154, [(2, 1), (7, 1), (11, 1)]),
    (1024, [(2, 10)]),
])
def test_gcd(n, result):
    assert list(factorize(n)) == result
    for f, p in result:
        assert n % (f ** p) == 0


@pytest.mark.parametrize("n, result", [
    (0, []),
    (1, [1]),
    (2, [1, 2]),
    (4, [1, 2, 4]),
    (144, [1, 2, 3, 4, 6, 8, 9, 12, 16, 18, 24, 36, 48, 72, 144]),
    (154, [1, 2, 7, 11, 14, 22, 77, 154]),
])
def test_divisors(n, result):
    assert sorted(divisors(n)) == sorted(result)
    for x in result:
        assert n % x == 0


@pytest.mark.parametrize("x, y, result", [
    ([1], [5], (5, 0)),
    ([1, 1], [5, 5], (5, 0)),
    ([1, 1], [5, 6], None),
    ([1, 2], [5, 5], (0, 5)),
    ([1, 1, 1, 1], [5, 5, 5, 5], (5, 0)),
    ([2, 2, 2, 2], [5, 5, 5, 5], (2, 1)),
    ([1, 1, 3, 6], [5, 5, 13, 25], (4, 1)),
    ([1, 3], [108, 124], (8, 100)),
    ([5, 10], [1, 2], None),
    ([5, 5], [1, 1], (0, 1)),
])
def test_affine_transformation(x, y, result):
    assert affine_transformation(x, y) == result


@pytest.mark.parametrize("x, result", [
    ([0], None),
    ([0, 1], None),
    ([0, 1, 2], 1),
    ([0, 1, 4], 2),
    ([1, 1, 4], None),
    ([0, 1, 8, 27], 3),
])
def test_get_power(x, result):
    assert get_power(x) == result


@pytest.mark.parametrize("x, result", [
    ([1], None),
    ([1, 2], 2),
    ([1, 2, 4], 2),
    ([1, 2, 8], None),
    ([1, 3, 9], 3),
])
def test_get_base(x, result):
    assert get_base(x) == result


@pytest.mark.parametrize("x, result", [
    (0, False),
    (1, False),
    (2, False),
    (3, False),
    (4, (2, 2)),
    (8, (2, 3)),
    (16, (2, 4)),
    (32, (2, 5)),
    (64, (2, 6)),
    (125, (5, 3)),
    (-4, False),
    (-8, (-2, 3)),
    (-16, False),
    (-32, (-2, 5)),
    (-64, False),
])
def test_perfect_power(x, result):
    assert perfect_power(x) == result



_iilist = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29],
    [-1, -2, -3, -4, -5, -6, -7, -8, -9, 0],
    [0, 1, 8, 27, 64, 125, 216, 343, 512, 729],
    [-2, 4, -8, 16, -32, 64, -128, 256, -512, 1024],
]
_sol = [0, 2, -3, 0, 1]


def _mkitems(ii, sol, denom):
    print("====")
    for x, y in zip(sol, ii):
        print(x, y)
    return [sum((x * yi)//denom for yi in y) for x, y in zip(sol, ii)]


@pytest.mark.parametrize("input_items_list, solution, denom, kwargs, found", [
    [_iilist, [0, 2, -3, 0, 1], 1, {}, True],
    [_iilist, [4, 0, 0, 0, 1], 2, {}, True],
    [_iilist, [4, 0, 0, 0, 1], 2, {'rationals': False, 'max_elapsed': 0.1}, False],
])
def test_linear_combination(input_items_list, solution, denom, kwargs, found):
    # for c, ii in enumerate(input_items_list):
    #     print("ii[{}]:".format(c), ii)
    # print("solution:", solution)
    # print("denom:", denom)
    length = len(input_items_list[0])
    # print("length:", length)
    # print("====")
    items = [sum(((coeff * input_items[i])//denom) for coeff, input_items in zip(solution, input_items_list)) for i in range(length)]
    # print("items:", items)
    # print("kwargs:", kwargs)
    if found:
        result = [(tuple(solution), denom)]
    else:
        result = []
    #print("result:", result)
    assert list(linear_combination(items, input_items_list, **kwargs)) == result
