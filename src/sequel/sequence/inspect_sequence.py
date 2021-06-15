"""
"""

import collections
import enum
import weakref

from .base import (
    Sequence, RecursiveSequence, Compose,
    Add, Sub, Mul, Div, Mod, Pow,
)
from .fibonacci import Fib, Trib
from .functional import Functional
from .miscellanea import Arithmetic, Geometric
from .polygonal import Polygonal
from .roundrobin import roundrobin

__all__ = [
    'inspect_sequence',
]


class Flag(enum.Enum):
    CORE = 0
    LINEAR_COMBINATION = 1
    RECURSIVE_SEQUENCE = 2
    AFFINE_TRANSFORM = 3
    FUNCTIONAL = 4
    POLYGONAL = 5
    COMPOSE = 6
    ROUNDROBIN = 7
    GEOMETRIC = 8
    ARITHMETIC = 9
    FIBONACCI = 10
    TRIBONACCI = 11
    ADD = 12
    SUB = 13
    MUL = 14
    DIV = 15
    MOD = 16
    POW = 17


Info = collections.namedtuple("Info", "contains flags")
_DATA = weakref.WeakKeyDictionary()


def inspect_sequence(sequence):
    if not isinstance(sequence, Sequence):
        raise TypeError(sequence)
    if not sequence in _DATA:
        _DATA[sequence] = _make_info(sequence)
    return _DATA[sequence]
        

def _make_info(sequence):
    contains = set()
    flags = set()
    core_sequences = set(Sequence.get_registry().values())
    if sequence in core_sequences:
        flags.add(Flag.CORE)
    else:
        if isinstance(sequence, RecursiveSequence):
            flags.add(Flag.RECURSIVE_SEQUENCE)
        elif isinstance(sequence, Polygonal):
            flags.add(Flag.POLYGONAL)
        elif isinstance(sequence, Functional):
            flags.add(Flag.FUNCTIONAL)
        elif isinstance(sequence, Compose):
            flags.add(Flag.COMPOSE)
        elif isinstance(sequence, Geometric):
            flags.add(Flag.GEOMETRIC)
        elif isinstance(sequence, Arithmetic):
            flags.add(Flag.ARITHMETIC)
        elif isinstance(sequence, roundrobin):
            flags.add(Flag.ROUNDROBIN)
        elif isinstance(sequence, Fib):
            flags.add(Flag.FIBONACCI)
        elif isinstance(sequence, Trib):
            flags.add(Flag.TRIBONACCI)
        elif isinstance(sequence, Add):
            flags.add(Flag.ADD)
        elif isinstance(sequence, Sub):
            flags.add(Flag.SUB)
        elif isinstance(sequence, Mul):
            flags.add(Flag.MUL)
        elif isinstance(sequence, Div):
            flags.add(Flag.DIV)
        elif isinstance(sequence, Mod):
            flags.add(Flag.MOD)
        elif isinstance(sequence, Pow):
            flags.add(Flag.POW)
        for depth, seq in sequence.walk():
            if seq in core_sequences:
               contains.add(seq)
    return Info(contains=frozenset(contains), flags=frozenset(flags))


def register_info(sequence, contains=(), flags=()):
    if not isinstance(sequence, Sequence):
        raise TypeError(sequence)
    info = inspect_sequence(sequence)
    _DATA[sequence] = Info(
        contains=info.contains.union(contains),
        flags=info.flags.union(flags),
    )
