"""
First-level algorithms (non recursive)
"""

import collections

from ..lazy import (
    numpy,
    sympy,
)
from ..sequence import (
    Sequence,
    Const, Integer,
    Arithmetic, Geometric,
    Power, make_fibonacci, make_tribonacci,
    Repunit,
    RecursiveSequence,
    BackIndexer,
)
from ..sequence.sequence_utils import (
    make_linear_combination,
    make_power,
    iter_monomials,
    make_monomial,
)
from ..utils import (
    affine_transformation,
    get_base, get_power, lcm, gcd,
    sequence_matches,
    linear_combination,
)
from .base import Algorithm


__all__ = [
    "CatalogAlgorithm",
    "ConstAlgorithm",
    "AffineTransformAlgorithm",
    "ArithmeticAlgorithm",
    "GeometricAlgorithm",
    "PowerAlgorithm",
    "FibonacciAlgorithm",
    "TribonacciAlgorithm",
    "PolynomialAlgorithm",
    "LinearCombinationAlgorithm",
    "RepunitAlgorithm",
]


class CatalogAlgorithm(Algorithm):
    """Search for known sequences in catalog"""
    __accepts_undefined__ = True
    __min_items__ = 1

    def iter_sequences(self, manager, items, rank):
        for x in manager.catalog.iter_matching_sequences(items):
            yield x
        #yield from manager.catalog.iter_matching_sequences(items)


class ConstAlgorithm(Algorithm):
    """Search for const sequences"""
    __min_items__ = 1

    def iter_sequences(self, manager, items, rank):
        if items:
           value = items[0]
           for item in items[1:]:
               if item != value:
                   return
           yield Const(value)
        

class AffineTransformAlgorithm(Algorithm):
    """Search for affine transformations of known sequences"""
    __min_items__ = 2

    def iter_sequences(self, manager, items, rank):
        catalog = manager.catalog
        for sequences, values in catalog.iter_sequences_values():
            values = values[:len(items)]
            if len(values) != len(items):
                continue
            result = affine_transformation(values, items)
            if result is None:
                result = affine_transformation(items, values)
                if result:
                    m, q = result
                    if m != 0:
                        for sequence in sequences:
                            sq = self.make_inverse_affine_transformation(q, m, sequence)  #(sequence - q) // m
                            # assert_sequence_matches(sq, items)
                            yield sq
            else:
                m, q = result
                for sequence in sequences:
                    sq = self.make_affine_transformation(q, m, sequence)
                    # assert_sequence_matches(sq, items)
                    yield sq

    def make_affine_transformation(self, q, m, sequence):
        # q + m * sequence
        parts = []
        if q != 0:
            parts.append(Const(value=q))
        if m == 1:
            parts.append(sequence)
        elif m != 0:
            parts.append(m * sequence)
        if parts:
            seq = parts[0]
            for part in parts[1:]:
                seq += part
            return seq
        else:
            return Const(value=0)

    def make_inverse_affine_transformation(self, q, m, sequence):
        #(sequence - q) // m
        if q == 0:
            token = sequence
        else:
            token = sequence - q
        if m == 1:
            return token
        elif m == -1:
            return -token
        else:
            return token // m


class ArithmeticAlgorithm(Algorithm):
    """Search for Arithmetic sequences"""

    def iter_sequences(self, manager, items, rank):
        if len(set(items.derivative)) == 1:
            seq = self.make_arithmetic(items[0], items.derivative[0])
            yield seq

    def make_arithmetic(self, start, step):
        if step == 0:
            return Const(value=start)
        elif start == 0 and step == 1:
            return Integer()
        else:
            return Arithmetic(start=start, step=step)


class TribonacciAlgorithm(Algorithm):
    """Search for fibonacci sequences"""
    __min_items__ = 4

    def iter_sequences(self, manager, items, rank):
        icmp = []
        for idx in range(2, len(items)):
            icmp.append(items[idx - 1] + items[idx - 2])
        if all(x == y for x, y in zip(items.derivative[2:], icmp)):
            yield make_tribonacci(items[0], items[1], items[2])


class GeometricAlgorithm(Algorithm):
    """Search for Geometric sequences"""

    def iter_sequences(self, manager, items, rank):
        base = get_base(items)
        if base is not None:
            yield Geometric(base=base)
        else:
            # affine transform
            # solve a + b * c^x = items, with x = [0, 1, 2, 3, ...]:
            # 0. x == 0: a + b * c^0 = a + b := items[0] == i0
            #    b = i0 - a
            # 1. x == 1: a + b * c^1 = a + b * c := i1
            #    a + (i0 - a) * c = i1
            #    c = (i1 - a) / (i0 - a)
            # 2. x == 2: a + b * c^2 = a + b * c^2 := i2
            #    a + (i0 - a) * [(i1 - a) / (i0 - a)]^2 = i2
            #    a + (i1 - a)^2 / (i0 - a) = i2
            #    (i1 - a)^2 / (i0 - a) = i2 - a
            #    (i1 - a)^2 = (i0 - a) * (i2 - a)
            #    i1^2 + a^2 - 2 * a * i1 = i0 * i2 - i0 * a - i2 * a + a*2
            #    -2 * i1 * a + (i0 + i2) * a = i0 * i2 - i1^2
            #    (i0 -2 * i1 + i2) * a = i0 * i2 - i1^2
            #    a = (i0 * i2 - i1^2) / (i0 -2 * i1 + i2)
            if len(items) < 3:
                return
            i0, i1, i2 = items[:3]
            den = i0 - (2 * i1) + i2
            if den == 0:
                return

            fa = ((i0 * i2) - (i1 ** 2)) / den
            a = int(fa)
            if a != fa or a == i0:
                return
            b = i0 - a
            fc = (i1 - a) / (i0 - a)
            c = int(fc)
            if c != fc or c < 2:
                return
            sequence = Geometric(base=c)
            if b == -1:
                sequence = -sequence
            elif b != 1:
                sequence = b * sequence
            if a != 0:
                sequence = a + sequence
            #sequence = a + b * Geometric(base=c)
            # sequence = sequence.simplify()
            # can fail since only few elements are checked
            if sequence_matches(sequence, items):
                yield sequence


class PowerAlgorithm(Algorithm):
    """Search for i ** pwr"""

    def iter_sequences(self, manager, items, rank):
        pwr = get_power(items)
        if pwr is not None:
            yield Power(power=pwr)


class FibonacciAlgorithm(Algorithm):
    """Search for fibonacci sequences"""
    __min_items__ = 3

    def iter_sequences(self, manager, items, rank):
        # f0, f1, (s*f1 + f0), (s*(s*f1 + f0) + f1)
        if items.derivative[1:] == items[:-2]:
            first, second = items[:2]
            fs_gcd = gcd(first, second)
            if abs(fs_gcd) > 1:
                first //= fs_gcd
                second //= fs_gcd
            fib = make_fibonacci(first=first, second=second)
            if abs(fs_gcd) != 1:
                fib = fs_gcd * fib
            yield fib
        elif len(items) >= 4:
            idiffs = []
            icmp = []
            for idx in range(2, len(items)):
                idiffs.append(items[idx] - items[idx - 1] - items[idx - 2])
                icmp.append(items[idx - 1])
            result = affine_transformation(icmp, idiffs)
            if result is not None:
                m, q = result
                if q == 0:
                    sq = make_fibonacci(first=items[0], second=items[1], scale=m + 1)
                    # assert_sequence_matches(sq, items)
                    yield sq


class PolynomialAlgorithm(Algorithm):
    """Search for polynomials"""
    __min_items__ = 3
    __init_keys__ = ["min_degree", "max_degree"]

    def __init__(self, min_degree=3, max_degree=5):
        super().__init__()
        self.min_degree = max(2, min_degree)
        self.max_degree = max_degree

    def iter_sequences(self, manager, items, rank):
        integer = Integer()
        np = numpy.module()
        for degree in range(self.min_degree, min(len(items), self.max_degree + 1)):
            try:
                m = np.ndarray(dtype=np.int64, shape=(degree, degree))
                for i in range(degree):
                    for j in range(degree):
                        m[i, j] = i ** j
                poly = np.linalg.solve(m, np.array(items[:degree], dtype=np.int64))
                if np.all(np.rint(poly) == poly):
                    sequence = None
                    if poly[-1] == 0:
                        break
                    for power, value in enumerate(poly):
                        coeff = int(round(value, 0))
                        if coeff:
                            if sequence is None:
                                sequence = coeff * integer ** power
                            else:
                                if coeff > 0:
                                    sequence += coeff * integer ** power
                                else:
                                    sequence -= (-coeff) * integer ** power
                    if sequence is not None:
                        sequence = sequence.simplify()
                        # can fail if len(items) > degree:
                        if sequence_matches(sequence, items):
                            yield sequence
            except OverflowError:
                # import traceback
                # traceback.print_exc()
                pass


class LinearCombinationAlgorithm(Algorithm):
    """Search for s = a * s1 + b * s2 + c * s3 + ..."""
    __init_keys__ = ["max_items", "min_components", "max_components", "rationals",
                     "min_elapsed", "max_elapsed", "exp_elapsed", "sequences"]

    def __init__(self, max_items=19, min_components=3, max_components=4, rationals=True,
                 min_elapsed=0.0, max_elapsed=3.0, exp_elapsed=0.9,
                 sequences=None):
        super().__init__()
        if sequences:
            sequences = [Sequence.compile(s) for s in sequences]
        else:
            sequences = []
        self.sequences = sequences
        core_sequences = []
        for core_sequence in Sequence.get_registry().values():
            if core_sequence not in sequences:
                core_sequences.append(core_sequence)
        sequences.extend(core_sequences)
        self._sequences = sequences
        self.min_components = min_components
        self.max_components = max_components
        self.min_elapsed = min_elapsed
        self.max_elapsed = max_elapsed
        self.exp_elapsed = exp_elapsed
        self.rationals = rationals
        self.max_items = max_items

    def iter_sequences(self, manager, items, rank):
        num_items = len(items)
        if num_items > self.max_items:
            return
        all_values = []
        for sequence in self._sequences:
            values = sequence.get_values(num_items)
            all_values.append(values)
        num_items = min(len(values) for values in all_values)
        if num_items < self.min_items():
            return
        
        all_sequences = self._sequences

        if len(items) > self.max_items:
            # not enough items
            return

        max_elapsed = max(self.min_elapsed, self.max_elapsed / (1.0 + rank) ** self.exp_elapsed)
        # print("!!!l", self.min_elapsed, self.max_elapsed, self.exp_elapsed, max_elapsed)

        all_values = [values[:num_items] for values in all_values]
        for solution, denom in linear_combination(items, all_values, min_components=self.min_components, max_components=self.max_components,
                                      max_elapsed=max_elapsed, rationals=self.rationals):
            sequence = make_linear_combination(solution, all_sequences, denom)
            if sequence_matches(sequence, items):
                yield sequence

         
class RepunitAlgorithm(Algorithm):
    """Search for repunit sequences"""
    __min_items__ = 3

    def iter_sequences(self, manager, items, rank):
        it0 = items[0]  # base ** 0 => it0 == 1
        base = items[1] - items[0]  # it0 + base ** 1 => it0 + base => base = it1 - it0
        if it0 == 1:
            sequence = Repunit(base=base)
        else:
            sequence = (it0 - 1) + Repunit(base=base)
        if sequence_matches(sequence, items):
            yield sequence


class RecursiveSequenceAlgorithm(Algorithm):
    __init_keys__ = ["max_items", "min_components", "max_components", "rationals",
                     "min_elapsed", "max_elapsed", "exp_elapsed", "max_depth", "max_power"]

    def __init__(self, max_items=19, min_components=3, max_components=4, rationals=True,
                 min_elapsed=0.0, max_elapsed=3.0, exp_elapsed=0.9,
                 max_depth=2, max_power=3):
        self.min_components = min_components
        self.max_components = max_components
        self.min_elapsed = min_elapsed
        self.max_elapsed = max_elapsed
        self.exp_elapsed = exp_elapsed
        self.rationals = rationals
        self.max_items = max_items
        self.max_depth = max_depth
        self.max_power = max(1, max_power)

    def iter_sequences(self, manager, items, rank):
        if rank > 1:
            return
        max_depth = self.max_depth
        max_power = self.max_power
        powers = list(range(1, max_power + 1))

        max_elapsed = max(self.min_elapsed, self.max_elapsed / (1.0 + rank) ** self.exp_elapsed)
        # print("!!!r", self.min_elapsed, self.max_elapsed, self.exp_elapsed, max_elapsed)

        indexers = [BackIndexer(i) for i in range(max_depth)]
        one = Sequence.compile('1')
        for depth in range(2, max_depth + 1):
            d_indexers = list(reversed(indexers[:depth]))
            i_items_list = []
            i_items_pwr = {pwr: [] for pwr in powers}
            i_items_pwr[0] = [1 for _ in d_indexers]
            d_items = items[depth:]
            for i in range(depth):
                i_items = items[i:i + len(d_items)]
                i_items_list.append(i_items)
                for pwr in powers:
                    i_items_pwr[pwr].append([i_item ** pwr for i_item in i_items])
            num_found = 0
            i_list = [[1 for _ in i_items]]  # for const term in linear combination
            i_indexers = [one]
            for power in range(1, max_power + 1):
                indices = list(range(len(d_indexers)))
                # print(":::")
                # for i_items in i_items_list:
                #     print(":::", i_items)
                for iplist in iter_monomials(indices, power):
                    # print(iplist)
                    c_indexers = make_monomial([(d_indexers[idx], pwr) for idx, pwr in iplist])
                    # print(c_indexers)
                    # r_items = [1 for _ in i_items]
                    c_items = [1 for _ in i_items]
                    for idx, pwr in iplist:
                        # for i, ival in enumerate(i_items_list[idx]):
                        #     r_items[i] *= make_power(ival, pwr)
                        for i, ival in enumerate(i_items_pwr[pwr][idx]):
                            c_items[i] *= ival
                    # assert r_items == c_items
                    i_list.append(c_items)
                    i_indexers.append(c_indexers)
                for solution, denom in linear_combination(d_items, i_list, min_components=self.min_components, max_components=self.max_components,
                                                          max_elapsed=max_elapsed, rationals=self.rationals):
                    generating_sequence = make_linear_combination(solution, i_indexers, denom)
                    sequence = RecursiveSequence(
                        known_items=tuple(items[:depth]),
                        generating_sequence=generating_sequence)
                    if sequence_matches(sequence, items):
                        yield sequence
                        num_found += 1
                if num_found > 0:
                    return
