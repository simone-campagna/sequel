"""
Sequence module
"""

import sys as _sys


from .base import (
    SequenceError, SequenceUnknownValueError, SequenceUnboundError, RecursiveSequenceError,
    Sequence, SequenceProxy, SequenceSlicer, Function, Iterator,
    RecursiveSequence, BackIndexer, rec,
    Integer, Natural,
    Const,
    Compose,
    compile_sequence,
    chain,
    Values,
)

from .factorial import Factorial
from .fibonacci import (
    Fib01, Fib11, Lucas, Fib, make_fibonacci,
    Trib, make_tribonacci,
)
from .goldbach import (
    GoldbachPartitionsCount,
    GoldbachPartitionsIncreasingValues,
    GoldbachPartitionsSmallestPrimes,
)
from .miscellanea import (
    Power, Geometric, Arithmetic,
)
from .polygonal import (
    Polygonal,
)
from .functional import (
    derivative, integral,
    summation, product,
    ifelse, where,
    moessner,
    moessner_ext_index,
    moessner_ext,
)
from .number_theory import (
    Catalan,
    Prime, Phi, Sigma, Tau, Pi,
    MersenneExponent,
    MersennePrime,
    Euler, Bell, Genocchi,
    LookAndSay,
    VanEck,
)
from .repunit import (
    Repunit,
    Demlo,
)
from .somos import somos, somos_break
from .trait import (
    Trait,
    verify_traits,
    get_trait_description,
)
from .roundrobin import (
    roundrobin,
)
from .generate import (
    generate,
    generate_sequences,
)
from .classify import (
    classify,
)
from .inspect_sequence import (
    inspect_sequence,
)

_mod = _sys.modules[__name__]
for _cls in Sequence, BackIndexer:
    for _name, _seq in _cls.get_registry().items():
        setattr(_mod, _name, _seq)
