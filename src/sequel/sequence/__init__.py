"""
Sequence module
"""

from .base import (
    Sequence, Function, Iterator,
    Integer, Natural,
    Const,
    Compose,
    compile_sequence,
)

from .catalan import Catalan
from .factorial import Factorial
from .fibonacci import (
    Fib01, Fib11, Lucas, Fib, make_fibonacci,
    Trib, make_tribonacci,
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
from .merge_join import (
    merge, join,
)
from .number_theory import (
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
from .trait import (
    Trait,
    verify_traits,
)
from .roundrobin import (
    roundrobin,
)
from .generate import (
    generate,
)
