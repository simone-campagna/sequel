"""
First-level algorithms (non recursive)
"""

import collections
import time

from .base import Algorithm
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
    numpy,
    sympy,
)


__all__ = [
    "CatalogAlgorithm",
    "ConstAlgorithm",
    "AffineTransformAlgorithm",
    "ArithmeticAlgorithm",
    "GeometricAlgorithm",
    "PowerAlgorithm",
    "FibonacciAlgorithm",
    "PolynomialAlgorithm",
    "LinearCombinationAlgorithm",
    "RepunitAlgorithm",
]


class CatalogAlgorithm(Algorithm):
    """Search for known sequences in catalog"""
    __accepts_undefined__ = True
    __min_items__ = 1

    def iter_sequences(self, manager, items, rank):
        yield from manager.catalog.iter_matching_sequences(items)


class ConstAlgorithm(Algorithm):
    """Search for const sequences"""
    __min_items__ = 1

    def iter_sequences(self, manager, items, rank):
        if len(set(items.derivative)) <= 1:
            yield Const(items[0])
        

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


class PolynomialAlgorithm(Algorithm):
    """Search for polynomials"""
    __min_items__ = 3
    __init_keys__ = ["min_degree", "max_degree"]

    def __init__(self, min_degree=3, max_degree=5):
        super().__init__()
        self.min_degree = max(2, min_degree)
        self.max_degree = max_degree
        self._numpy = numpy()

    def iter_sequences(self, manager, items, rank):
        integer = Integer()
        np = self._numpy
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


class LinearCombinationAlgorithm(Algorithm):
    """Search for s = a * s1 + b * s2 + c * s3 + ..."""
    __init_keys__ = ["max_items", "min_components", "max_components", "rationals",
                     "min_elapsed", "max_elapsed", "exp_elapsed", "sequences"]

    def __init__(self, max_items=19, min_components=3, max_components=4, rationals=True,
                 min_elapsed=0.2, max_elapsed=2.0, exp_elapsed=-0.8,
                 sequences=None):
        super().__init__()
        self._sympy = sympy()
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
        self.exp_elapsed = -abs(exp_elapsed)
        self.rationals = rationals
        self.max_items = max_items

    def iter_sequences(self, manager, items, rank):
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

        all_sequences = self._sequences

        if len(items) > self.max_items:
            # not enough items
            return

        all_values = [values[:num_items] for values in all_values]
        x_values = list(items)
        all_indices = [i for i, _ in enumerate(all_sequences)]
        zero_sol = [0 for _ in all_sequences]
        sympy_module = self._sympy
        xs = sympy_module.symbols("x0:{}".format(num_items), integer=True)
        max_components = self.max_components
        rationals = self.rationals
        max_elapsed = max(self.min_elapsed, self.max_elapsed / (1.0 + rank) ** self.exp_elapsed)
        weights = [1.0 for _ in all_indices]

        last_index = len(all_indices)
        indices = all_indices[:]
        #niter = 0
        found_solutions = set()
        while True:
            #niter += 1
            if time.time() - t0 >= max_elapsed:
                break
            indices += tuple(i for i in all_indices if i not in indices)
            values = [all_values[index] for index in indices] + [x_values]
            augmented_matrix = sympy_module.Matrix(values).T
            m_rref, pivots = augmented_matrix.rref()
            if last_index in pivots:
                # x_values is not a linear combination of values
                return
            
            num = len(pivots)
            num_components = 0
            coeffs = []
            for c, pivot_c in enumerate(pivots):
                coeff = 0
                for r in range(num):
                    if c < r:
                        assert m_rref[r, pivot_c] == 0
                    coeff += m_rref[r, pivot_c] * m_rref[c, last_index]
                if coeff != 0:
                    num_components += 1
                coeffs.append(coeff)
            #print("niter:", niter, num_components, "/", num)
            if max_components is None or num_components <= max_components:
                denoms = []
                for coeff in coeffs:
                    if coeff.q != 1:
                        if rationals:
                            denoms.append(int(coeff.q))
                        else:
                            break
                else:
                    if denoms:
                        denom = lcm(*denoms)
                    else:
                        denom = 1
                    coeffs = [int(coeff * denom) for coeff in coeffs]
                    solution = zero_sol[:]
                    for pivot, coeff in zip(pivots, coeffs):
                        solution[indices[pivot]] = coeff
                    solution = tuple(solution)
                    if solution not in found_solutions:
                        found_solutions.add(solution)
                        sequence = _make_linear_combination(solution, all_sequences, denom)
                        # can fail if len(items) > 
                        if sequence_matches(sequence, items):
                            yield sequence
                    if num_components <= self.min_components:
                        return
            # recompute weights
            for i, index in enumerate(indices):
                if i in pivots:
                    weights[index] += num_components / num
                else:
                    weights[index] -= sum([1 for r in range(num) if m_rref[r, i] != 0]) / num
                   
            #for pivot in pivots:
            indices = sorted(indices[:-1], key=lambda x: weights[x]) + indices[-1:]


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


