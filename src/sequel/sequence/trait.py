"""
Traits
"""

import enum


__all__ = [
    'Trait',
    'verify_traits',
]


class Trait(enum.Enum):
    INJECTIVE = 1
    POSITIVE = 2
    NEGATIVE = 3
    NON_ZERO = 4
    ALTERNATING = 5
    INCREASING = 6
    DECREASING = 7
    PARTIALLY_KNOWN = 8
    FAST_GROWING = 9
    SLOW = 10


def verify_injective(items):
    return len(set(items)) == len(items)


def verify_positive(items):
    return all(item >= 0 for item in items)


def verify_negative(items):
    return all(item <= 0 for item in items)


def verify_non_zero(items):
    return all(item != 0 for item in items)


def verify_alternating(items):
    sign = lambda n: -1 if n < 0 else +1
    if not items:
        return True
    sprev = sign(items[0])
    for item in items[1:]:
        scur = sign(item)
        if scur == sprev:
            return False
        sprev = scur
    return True


def verify_increasing(items):
    prev = None
    for item in items:
        if prev is not None:
            if item < prev:
                return False
    return True


def verify_decreasing(items):
    prev = None
    for item in items:
        if prev is not None:
            if item > prev:
                return False
    return True


_VERIFY_FUNCTION = {
    Trait.INJECTIVE: verify_injective,
    Trait.POSITIVE: verify_positive,
    Trait.NEGATIVE: verify_negative,
    Trait.NON_ZERO: verify_non_zero,
    Trait.ALTERNATING: verify_alternating,
    Trait.INCREASING: verify_increasing,
    Trait.DECREASING: verify_decreasing,
}

def verify_traits(items, *traits):
    for trait in traits:
        verify_trait_function = _VERIFY_FUNCTION.get(trait, lambda x: True)
        if not verify_trait_function(items):
            return False
    return True
