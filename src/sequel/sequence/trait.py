"""
Traits
"""

import enum


__all__ = [
    'Trait',
    'verify_traits',
    'get_trait_description',
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


TRAIT_DESCRIPTION = {
    Trait.INJECTIVE: 'every sequence item is unique',
    Trait.POSITIVE: 'every sequence item is >= 0',
    Trait.NEGATIVE: 'every sequence item is <= 0',
    Trait.NON_ZERO: 'every sequence item is != 0',
    Trait.ALTERNATING: 'sequence items are alternatively strictly positive and strictly negative',
    Trait.INCREASING: 'every sequence items is >= its predecessor',
    Trait.DECREASING: 'every sequence items is <= its predecessor',
    Trait.PARTIALLY_KNOWN: 'only some of the first sequence items are known',
    Trait.FAST_GROWING: 'the absolute value of the sequence items grows rapidly',
    Trait.SLOW: 'generation of new items is slow',
}


def get_trait_description(trait):
    return TRAIT_DESCRIPTION[trait]


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
    if not items:
        return True
    prev = items[0]
    for item in items[1:]:
        if item < prev:
            return False
        prev = item
    return True


def verify_decreasing(items):
    if not items:
        return True
    prev = items[0]
    for item in items[1:]:
        if item > prev:
            return False
        prev = item
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
