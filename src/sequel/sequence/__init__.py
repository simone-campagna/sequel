"""
Sequence module
"""

from .base import (
    Sequence, Function, Iterator,
    Integer, Natural,
    NegInteger, NegNatural,
    Const,
    Compose,
    compile_sequence,
)

from .catalan import Catalan
from .factorial import Factorial
from .fibonacci import (
    Fib01, Fib11, Lucas, Fib, make_fibonacci,
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
)
from .number_theory import (
    Prime, Phi, Sigma, Tau, Pi,
    MersenneExponent,
    MersennePrime,
    Euler, Bell, Genocchi,
)
from .repunit import (
    Repunit,
    Demlo,
)
from .trait import (
    Trait,
    verify_traits,
)
from .zip_sequences import (
    Zip,
)
