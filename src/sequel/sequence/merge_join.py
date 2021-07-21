"""
Merge sequences
"""

import abc

from .base import Sequence, Iterator
from ..lazy import gmpy2


__all__ = [
    'BlockSequence',
    'merge',
    'join',
]


class BlockSequence(Iterator):
    def __new__(cls, *iterables):
        c_iterables = []
        for iterable in iterables:
            if isinstance(iterable, float) or gmpy2.is_integer(iterable):
                iterable = (int(iterable),)
            elif isinstance(iterable, list):
                iterable = tuple(iterable)
            if isinstance(iterable, (tuple, Sequence)):
                c_iterables.append(iterable)
            else:
                raise TypeError(iterable)
        return super().__new__(cls, *c_iterables)

    def __init__(self, *iterables):
        self._iterables = iterables


class merge(BlockSequence):
    def __iter__(self):
        for iterable in self._iterables:
            yield from iterable


class join(BlockSequence):
    def __iter__(self):
        iterators = [iter(iterable) for iterable in self._iterables]
        while True:
            value = None
            unset = True
            for iterator in iterators:
                try:
                    if unset:
                        value = next(iterator)
                        unset = False
                    else:
                        next(iterator)
                except StopIteration:
                    pass
            if unset:
                raise StopIteration
            yield value
