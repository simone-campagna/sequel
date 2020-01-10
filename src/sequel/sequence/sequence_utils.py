"""
Sequence utilities
"""

from .base import Const, Sequence
from ..utils import gcd


__all__ = [
    'make_linear_combination',
    'make_power',
]


def make_linear_combination(coeffs, items, denom=1):
    orig_ci_list = list(zip(coeffs, items))
    result = None
    coeffs = []
    items = []
    for coeff, item in orig_ci_list:
        if isinstance(item, Const):
            coeff = coeff * item.value
            item = 1
        coeffs.append(coeff)
        items.append(item)
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
        if isinstance(item, Const):
            const_value = coeff * item.value
            if const_value < 0 and result is not None:
                item = Const(-const_value)
                coeff = -1
            else:
                item = Const(const_value)
                coeff = 1
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
    if result is None:
        result = Const(0)
    elif denom != 1:
        result //= denom
    return Sequence.make_sequence(result)


def make_power(expr, power):
    if isinstance(expr, Const):
        return Const(expr.value ** power)
    if power == 1:
        return expr
    else:
        return expr ** power

