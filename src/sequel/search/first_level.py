"""
First-level algorithms (non recursive)
"""

import collections
import time

import numpy as np
import sympy

from .base import SearchAlgorithm
from ..sequence import (
    Sequence,
    Const, Integer,
    Arithmetic, Geometric,
    Power, make_fibonacci,
    Repunit,
)
from ..utils import (
    affine_transformation,
    get_base, get_power, lcm, gcd,
    sequence_matches,
    assert_sequence_matches,
)

__all__ = [
    "SearchCatalog",
    "SearchAffineTransform",
    "SearchArithmetic",
    "SearchGeometric",
    "SearchAffineGeometric",
    "SearchPower",
    "SearchFibonacci",
    "SearchPolynomial",
    "SearchLinearCombination",
    "SearchRepunit",
]


class SearchCatalog(SearchAlgorithm):
    """Search for known sequences in catalog"""
    __accepts_undefined__ = True
    __min_items__ = 1

    def iter_sequences(self, manager, items, priority):
        yield from manager.catalog.iter_matching_sequences(items)


class SearchAffineTransform(SearchAlgorithm):
    """Search for affine transformations of known sequences"""

    def iter_sequences(self, manager, items, priority):
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
                            assert_sequence_matches(sq, items)
                            yield sq
            else:
                m, q = result
                for sequence in sequences:
                    sq = self.make_affine_transformation(q, m, sequence)
                    assert_sequence_matches(sq, items)
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


class SearchArithmetic(SearchAlgorithm):
    """Search for Arithmetic sequences"""

    def iter_sequences(self, manager, items, priority):
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


class SearchGeometric(SearchAlgorithm):
    """Search for Geometric sequences"""

    def iter_sequences(self, manager, items, priority):
        base = get_base(items)
        if base is not None:
            yield Geometric(base=base)


class SearchAffineGeometric(SearchAlgorithm):
    """Search for sequences a + b * c^i == a + b * Geometric(c)"""

    def iter_sequences(self, manager, items, priority):
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
        den = items[0] - (2 * items[1]) + items[2]
        if den == 0:
            return
        fa = ((items[0] * items[2]) - (items[1] ** 2)) / den
        a = int(fa)
        if a != fa or a == items[0]:
            return
        b = items[0] - a
        fc = (items[1] - a) / (items[0] - a)
        c = int(fc)
        if c != fc or c < 2:
            return
        sequence = a + b * Geometric(base=c)
        # sequence = sequence.simplify()
        # can fail since only few elements are checked
        if sequence_matches(sequence, items):
            yield sequence


class SearchPower(SearchAlgorithm):
    """Search for i ** pwr"""

    def iter_sequences(self, manager, items, priority):
        pwr = get_power(items)
        if pwr is not None:
            yield Power(power=pwr)


class SearchFibonacci(SearchAlgorithm):
    """Search for fibonacci sequences"""
    __min_items__ = 3

    def iter_sequences(self, manager, items, priority):
        if items.derivative[1:] == items[:-2]:
            first, second = items[:2]
            fs_gcd = gcd(first, second)
            if fs_gcd > 1:
                first //= fs_gcd
                second //= fs_gcd
            fib = make_fibonacci(first=first, second=second)
            if fs_gcd != 1:
                fib = fs_gcd * fib
            yield fib


class SearchPolynomial(SearchAlgorithm):
    """Search for polynomials"""
    __min_items__ = 3

    def __init__(self, min_degree=3, max_degree=5):
        super().__init__()
        self.min_degree = max(2, min_degree)
        self.max_degree = max_degree

    def iter_sequences(self, manager, items, priority):
        integer = Integer()
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


def _make_linear_combination(coeffs, sequences, denom):
    result = None
    for coeff, sequence in zip(coeffs, sequences):
        if coeff != 0:
            if coeff == 1:
                token = sequence
            elif coeff == -1:
                token = -sequence
            else:
                token = int(coeff) * sequence
            if result is None:
                result = token
            else:
                result += token
    if denom != 1:
        result //= denom
    return result


LCInfo = collections.namedtuple(
    "LCInfo", "max_items sequences values")


class SearchLinearCombination(SearchAlgorithm):
    """Search for s = a * s1 + b * s2 + c * s3 + ..."""
    def __init__(self, max_items=19, min_components=2, max_components=4, rationals=True,
                 max_elapsed=3.0, search_method='weighted',
                 weight_threshold=4, weight_value=0.9, sequences=None):
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
        self.max_elapsed = max_elapsed
        self.rationals = rationals
        self.weight_threshold = weight_threshold
        self.weight_value = weight_value
        self.max_items = max_items
        self.search_method = search_method

    def ordered_combinations(self, items, num, data):
        yield from itertools.combinations(items, num)
    
    def random_combinations(self, items, num, data):
        pool = tuple(items)
        n = len(pool)
        while True:
            indices = sorted(random.sample(range(n), num))
            yield tuple(pool[i] for i in indices)

    def weighted_combinations(self, items, num, data):
        pool = tuple(items)
        num_items = len(pool)
        while True:
            weights = data['weights']
            np_weights = np.array(weights, dtype=np.float32)
            np_weights /= np.sum(np_weights)
            data['weights'] = list(np_weights)
            sel_indices = np.random.choice(num_items, num, p=np_weights)
            yield tuple(pool[i] for i in sel_indices)


    def iter_sequences(self, manager, items, priority):
        t0 = time.time()
        num_items = len(items)
        if num_items > self.max_items:
            return
        # creates cache:
        all_values = []
        for sequence in self._sequences:
            values = sequence.get_values(num_items)
            all_values.append(values)
        num_items = min(len(values) for values in all_values)
        if num_items < self.min_items():
            return

        needs_weights = False
        if self.search_method == 'random':
            iter_combinations = self.random_combinations
        elif self.search_method == 'weighted':
            iter_combinations = self.weighted_combinations
            needs_weights = True
        elif self.search_method == 'ordered':
            iter_combinations = self.ordered_combinations
        else:
            raise ValueError("unknown search method {!r}".format(search_method))
        all_sequences = self._sequences

        if len(items) > self.max_items:
            # not enough items
            return

        def weight_factor(c, m, t, v):
            if c > t:
                # (c, o): (t, 0), (m, -v)
                # f(c) = a * c + b
                # f(t) = a * t + b = 0.0
                # f(m) = a * m + b = -v
                # b = -a * t
                # a * m - a * t = -v
                # a = -v / (m - t)
                a = -v / (m - t)
                b = -t * a
                off = a * c + b
            else:
                # (c, o): (t, 0), (2, v)
                # f(c) = a * c + b
                # f(t) = a * t + b = 0.0
                # f(2) = a * 2 + b = v
                # b = -a * t
                # a * 2 - a * t = v
                # a = v / (2 - t)
                a = v / (2 - t)
                b = -t * a
                off = a * c + b
            return 1 + off

        def wfactor(c):
            return weight_factor(c, m=num_items, t=self.weight_threshold, v=self.weight_value)

        all_values = [values[:num_items] for values in all_values]
        x_values = list(items)
        all_indices = [i for i, _ in enumerate(all_sequences)]
        zero_sol = [0 for _ in all_sequences]
        xs = sympy.symbols("x0:{}".format(num_items), integer=True)
        max_components = self.max_components
        rationals = self.rationals
        max_elapsed = self.max_elapsed // (1.0 + priority)
        if max_elapsed is None:
            checktime = lambda tstart: True
        else:
            checktime = lambda tstart: time.time() - tstart < max_elapsed
        data = {}
        if needs_weights:
            weights = [1.0 for _ in all_indices]
            data['weights'] = weights
        for indices in iter_combinations(all_indices, num_items, data):
            if not checktime(t0):
                break
            indices += tuple(i for i in all_indices if i not in indices)
            values = [all_values[index] for index in indices] + [x_values]
            augmented_matrix = sympy.Matrix(values).T
            m_rref, pivots = augmented_matrix.rref()
            if len(indices) in pivots:
                # x_values is not a linear combination of values
                continue
            
            rows = [list(m_rref.col(index)) for index in pivots]
            matrix = sympy.Matrix(rows)
            vector = m_rref.col(-1)
            solutions = []
            for coeffs in sympy.linsolve((matrix, vector), xs):
                denoms = []
                for coeff in coeffs:
                    if coeff.q != 1:
                        if rationals:
                            denoms.append(int(coeff.q))
                        else:
                            break
                else:
                    if denoms:
                        d_lcm = lcm(*denoms)
                    else:
                        d_lcm = 1
                    coeffs = [int(coeff * d_lcm) for coeff in coeffs]
                    solutions.append((d_lcm, coeffs))
            for denom, coeffs in solutions:
                sol = zero_sol[:]
                num_components = 0
                for pivot, coeff in zip(pivots, coeffs):
                    if coeff != 0:
                        num_components += 1
                        sol[indices[pivot]] = coeff
                if needs_weights:
                    wf = wfactor(num_components)
                    for pivot in pivots:
                        weights[indices[pivot]] *= wf
                    s_weights = sum(weights)
                    weights = [w / s_weights for w in weights]
                    data['weights'] = weights
                if max_components is None or num_components <= max_components:
                    sequence = _make_linear_combination(sol, all_sequences, denom)
                    # can fail if len(items) > 
                    if sequence_matches(sequence, items):
                        yield sequence
                    if num_components <= self.min_components:
                        return


class SearchRepunit(SearchAlgorithm):
    """Search for repunit sequences"""
    __accepts_undefined__ = True
    __min_items__ = 3

    def iter_sequences(self, manager, items, priority):
        it0 = items[0]  # base ** 0 => it0 == 1
        base = items[1] - items[0]  # it0 + base ** 1 => it0 + base => base = it1 - it0
        if it0 == 1:
            sequence = Repunit(base=base)
            if sequence_matches(sequence, items):
                yield sequence


