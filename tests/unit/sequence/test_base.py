import pytest

from sequel.sequence import (
    Sequence,
    Compose,
    Integer, Natural,
    NegInteger, NegNatural,
    Const,
    Fib01, Fib11, Lucas, make_fibonacci, Fib,
    Prime, Sigma, Tau, Phi, Pi,
    Euler, Bell, Genocchi,
    Power, Geometric, Arithmetic,
    Polygonal,
    Factorial,
    Catalan,
    roundrobin,
    integral,
    derivative,
    Geometric,
    Arithmetic,
    Repunit,
    Demlo,
    verify_traits,
)


def _fib(i):
    if i < 2:
        return 1
    p = 1
    for n in range(2, i + 1):
        p *= n
    return p
    
_indices = list(range(10))

_refs = [
    ["i", Integer(), _indices],
    ["n", Natural(), [i + 1 for i in _indices]],
    ["NegInteger()", NegInteger(), [-i for i in _indices]],
    ["NegNatural()", NegNatural(), [-(i + 1) for i in _indices]],
    ["0", Const(value=0), [0 for _ in _indices]],
    ["5", Const(value=5), [5 for _ in _indices]],
    ["i + 3", Integer() + 3, [i + 3 for i in _indices]],
    ["3 + i", 3 + Integer(), [3 + i for i in _indices]],
    ["i - 3", Integer() - 3, [i - 3 for i in _indices]],
    ["3 - i", 3 - Integer(), [3 - i for i in _indices]],
    ["i * 3", Integer() * 3, [i * 3 for i in _indices]],
    ["3 * i", 3 * Integer(), [3 * i for i in _indices]],
    ["i // 3", Integer() / 3, [i // 3 for i in _indices]],
    ["10 // 4", 10 / Const(value=4), [10 // 4 for i in _indices]],
    ["i // 3", Integer() // 3, [i // 3 for i in _indices]],
    ["10 // 4", 10 // Const(value=4), [10 // 4 for i in _indices]],
    ["i % 3", Integer() % 3, [i % 3 for i in _indices]],
    ["3 % 2", 3 % Const(value=2), [3 % 2 for i in _indices]],
    ["i ** 3", Integer() ** 3, [i ** 3 for i in _indices]],
    ["3 ** i", 3 ** Integer(), [3 ** i for i in _indices]],
    ["5 + i ** 2", Const(value=5) + Integer() ** 2, [5 + i ** 2 for i in _indices]],
    ["5 - i ** 2", Const(value=5) - Integer() ** 2, [5 - i ** 2 for i in _indices]],
    ["5 * i ** 2", Const(value=5) * Integer() ** 2, [5 * i ** 2 for i in _indices]],
    ["5 * (i - 2)", Const(value=5) * (Integer() - 2), [5 * (i - 2) for i in _indices]],
    ["5 * i - 2", Const(value=5) * Integer() - 2, [5 * i - 2 for i in _indices]],
    ["100 // (10 + i)", Const(value=100) / (Const(value=10) + Integer()), [100 // (10 + i) for i in _indices]],
    ["-(i - 3)", -(Integer() - 3), [-(i - 3) for i in _indices]],
    ["+(i - 3)", +(Integer() - 3), [+(i - 3) for i in _indices]],
    ["abs(i - 3)", abs(Integer() - 3), [abs(i - 3) for i in _indices]],
    ["abs(i)", abs(Integer()), [abs(i) for i in _indices]],
    ["i ** 3 | i", (Integer() ** 3) | Integer(), [(i) ** 3 for i in _indices]],
    ["i ** 3 | i + 2", (Integer() ** 3) | (Integer() + 2), [(i + 2) ** 3 for i in _indices]],
    ["i | i + 2", Integer() | (Integer() + 2), [(i + 2) for i in _indices]],
    ["fib01", Fib01(), [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]],
    ["fib01", make_fibonacci(first=0, second=1), [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]],
    ["fib11", Fib11(), [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]],
    ["fib11", make_fibonacci(1, 1), [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]],
    ["fib11", make_fibonacci(first=1, second=1), [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]],
    ["lucas", Lucas(), [2, 1, 3, 4, 7, 11, 18, 29, 47, 76]],
    ["lucas", make_fibonacci(2), [2, 1, 3, 4, 7, 11, 18, 29, 47, 76]],
    ["Fib(first=2, second=3)", make_fibonacci(first=2, second=3), [2, 3, 5, 8, 13, 21, 34, 55, 89, 144]],
    ["Fib(first=2, second=3) | 2 * i", make_fibonacci(first=2, second=3) | (2 * Integer()), [2, 5, 13, 34, 89]],
    ["lucas | 2 + i", make_fibonacci(first=2, second=1) | (2 + Integer()), [3, 4, 7, 11, 18, 29, 47, 76, 123, 199]],
    ["p", Prime(), [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]],
    ["square", Power(power=2), [i ** 2 for i in _indices]],
    ["cube", Power(power=3), [i ** 3 for i in _indices]],
    ["Power(power=5)", Power(power=5), [i ** 5 for i in _indices]],
    ["power_of_2", Geometric(base=2), [2 ** i for i in _indices]],
    ["power_of_3", Geometric(base=3), [3 ** i for i in _indices]],
    ["Geometric(base=5)", Geometric(base=5), [5 ** i for i in _indices]],
    ["power_of_10", Geometric(base=10), [10 ** i for i in _indices]],
    ["Arithmetic(start=5, step=7)", Arithmetic(step=7, start=5), [5 + 7 * i for i in _indices]],
    ["Arithmetic(start=0, step=3)", Arithmetic(step=3, start=0), [3 * i for i in _indices]],
    ["odd", Arithmetic(step=2, start=1), [1 + 2 * i for i in _indices]],
    ["even", Arithmetic(step=2, start=0), [2 * i for i in _indices]],
    ["triangular", Polygonal(3), [0, 1, 3, 6, 10, 15, 21, 28, 36, 45]],
    ["Polygonal(sides=4)", Polygonal(4), [i ** 2 for i in _indices]],
    ["pentagonal", Polygonal(5), [0, 1, 5, 12, 22, 35, 51, 70, 92, 117]],
    ["hexagonal", Polygonal(6), [0, 1, 6, 15, 28, 45, 66, 91, 120, 153]],
    ["roundrobin(p, fib01)", roundrobin(Prime(), Fib01()), [2, 0, 3, 1, 5, 1, 7, 2, 11, 3]],
    ["roundrobin(p, i, fib11)", roundrobin(Prime(), Integer(), Fib11()), [2, 0, 1, 3, 1, 1, 5, 2, 2, 7]],
    ["factorial", Factorial(), [_fib(i) for i in _indices]],
    ["catalan", Catalan(), [1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862]],
    ["sigma", Sigma(), [1, 3, 4, 7, 6, 12, 8, 15, 13, 18, 12, 28, 14, 24, 24, 31, 18, 39, 20, 42, 32, 36,
                        24, 60, 31, 42, 40, 56, 30, 72, 32, 63, 48, 54, 48, 91, 38, 60, 56, 90, 42, 96,
                        44, 84, 78, 72, 48, 124, 57, 93, 72, 98, 54, 120, 72, 120, 80, 90, 60, 168, 62,
                        96, 104, 127, 84, 144, 68, 126, 96, 144]],
    ["tau", Tau(), [1, 2, 2, 3, 2, 4, 2, 4, 3, 4, 2, 6, 2, 4, 4, 5, 2, 6, 2, 6, 4, 4, 2, 8, 3, 4, 4, 6,
                    2, 8, 2, 6, 4, 4, 4, 9, 2, 4, 4, 8, 2, 8, 2, 6, 6, 4, 2, 10, 3, 6, 4, 6, 2, 8, 4, 8,
                    4, 4, 2, 12, 2, 4, 6, 7, 4, 8, 2, 6, 4, 8, 2, 12, 2, 4, 6, 6, 4, 8, 2, 10, 5, 4, 2,
                    12, 4, 4, 4, 8, 2, 12, 4, 6, 4, 4, 4, 12, 2, 6, 6, 9, 2, 8, 2, 8]],
    ["pi", Pi(), [0, 1, 2, 2, 3, 3, 4, 4, 4, 4, 5, 5, 6, 6, 6, 6, 7, 7, 8, 8, 8, 8, 9, 9, 9, 9, 9, 9, 10,
                  10, 11, 11, 11, 11, 11, 11, 12, 12, 12, 12, 13, 13, 14, 14, 14, 14, 15, 15, 15, 15, 15,
                  15, 16, 16, 16, 16, 16, 16, 17, 17, 18, 18, 18, 18, 18, 18, 19, 19, 19, 19, 20, 20, 21,
                  21, 21, 21, 21, 21]],
    ["phi", Phi(), [1, 1, 2, 2, 4, 2, 6, 4, 6, 4, 10, 4, 12, 6, 8, 8, 16, 6, 18, 8, 12, 10, 22, 8, 20, 12,
                  18, 12, 28, 8, 30, 16, 20, 16, 24, 12, 36, 18, 24, 16, 40, 12, 42, 20, 24, 22, 46, 16,
                  42, 20, 32, 24, 52, 18, 40, 24, 36, 28, 58, 16, 60, 30, 36, 32, 48, 20, 66, 32, 44]],
    ["euler", Euler(), [1, 0, -1, 0, 5, 0, -61, 0, 1385, 0, -50521, 0, 2702765, 0, -199360981, 0, 19391512145,
                        0, -2404879675441, 0, 370371188237525, 0, -69348874393137901, 0, 15514534163557086905,
                        0, -4087072509293123892361, 0, 1252259641403629865468285, 0, -441543893249023104553682821]],
    ["bell", Bell(), [1, 1, 2, 5, 15, 52, 203, 877, 4140, 21147, 115975, 678570, 4213597, 27644437,
                      190899322, 1382958545, 10480142147, 82864869804, 682076806159, 5832742205057,
                      51724158235372, 474869816156751]],
    ["genocchi", Genocchi(), [1, -1, 0, 1, 0, -3, 0, 17, 0, -155, 0, 2073, 0, -38227, 0, 929569, 0,
                              -28820619, 0, 1109652905, 0, -51943281731]],
    ["repunit", Repunit(), [1, 11, 111, 1111, 11111, 111111]],
    ["repunit", Repunit(10), [1, 11, 111, 1111, 11111, 111111]],
    ["Repunit(base=2)", Repunit(2), [1, 3, 7, 15, 31, 63]],
    ["demlo", Demlo(), [i ** 2 for i, _ in zip(Repunit(), range(10))]],
]


@pytest.mark.parametrize("string, sequence, reference", _refs)
def test_sequence_values(string, sequence, reference):
    indices = list(range(len(reference)))
    assert list(sequence[i] for i in indices) == reference
    assert list(zip(sequence, indices)) == list(zip(reference, indices))
    assert str(sequence) == string


@pytest.mark.parametrize("string, sequence, reference", _refs)
def test_sequence_string(string, sequence, reference):
    indices = list(range(len(reference)))
    assert str(sequence) == string


@pytest.mark.parametrize("string, sequence, reference", _refs)
def test_sequence_string_compile(string, sequence, reference):
    indices = list(range(len(reference)))
    seq2 = Sequence.compile(str(sequence))


@pytest.mark.parametrize("string, sequence, reference", _refs)
def test_sequence_repr_compile(string, sequence, reference):
    indices = list(range(len(reference)))
    seq2 = Sequence.compile(repr(sequence))
    assert [sequence[i] for i in indices] == [seq2[i] for i in indices]


_simplify_tests = [
    [-Const(value=-3), '3'],
    [Const(value=3) + Const(value=5), '8'],
    [Const(value=3) - Const(value=5), '-2'],
    [Integer() - Const(value=-5), 'i + 5'],
    [Integer() - Const(value=0), 'i'],
    [Integer() + Const(value=-5), 'i - 5'],
    [Integer() | Const(value=5), '5'],
    [Const(5) | Integer(), '5'],
    [Const(value=5) - (-Integer()), 'i + 5'],
    [Const(value=5) + (-Integer()), '-i + 5'],
    [0 - Integer(), '-i'],
    [0 - (-Integer()), 'i'],
    [0 * Integer(), '0'],
    [Integer() * 0, '0'],
    [1 * Integer(), 'i'],
    [Integer() * 1, 'i'],
    [-1 * Integer(), '-i'],
    [Integer() * -1, '-i'],
    [Integer() / 1, 'i'],
    [Integer() / -1, '-i'],
    [Integer() / (Const(value=3) - 2), 'i'],
    [Integer() / (Const(value=3) - 4), '-i'],
    [Integer() % 2, 'i % 2'],
    [Sequence.compile('1 + 0 * p + 1 * n - 3'), 'n - 2'],
    [Sequence.compile('0 + 1 * roundrobin(3*p - n - p + n, 9 + m_exp -3)'), 'roundrobin(2 * p, m_exp + 6)'],
    [Sequence.compile('integral(2 * p - n - p + n + 1 * m_exp * 0, start=5) * 1'), 'integral(p, start=5)'],
    [Sequence.compile('derivative(2 * p - n - p + 1 * n - 0 * m_primes) * 1 + 0'), 'derivative(p)'],
    [Sequence.compile('derivative(integral(2 * p - n - p + n + 1 * m_exp * 0, start=5) * 1)'), 'p'],
    [Sequence.compile('integral(derivative(2 * p - n - p + 1 * n - 0 * m_primes) * 1 + 0)'), '-2 + p'],
    [Sequence.compile('summation(p + n - 3 * p - n * 1)*1 + 0'), 'summation(-2 * p)'],
    [Sequence.compile('1*product(p + n - 3 * p - n * 1) + 0'), 'product(-2 * p)'],
    [Sequence.compile('(2 * p - n - p + n + 0) | roundrobin(p - n + p, p +p - n*1 - 0)'), 'p | roundrobin(-n + 2 * p, -n + 2 * p)'],
]

@pytest.mark.parametrize('sequence, simplified', _simplify_tests)
def test_sequence_simplify(sequence, simplified):
    assert str(sequence.simplify()) == simplified


@pytest.mark.parametrize('seq_a, seq_b, equals', [
    [Integer(), Integer(), True],
    [Integer() + 2, 2 + Integer(), True],
    [Integer() + 2, 1 + 2 * Integer() + 4 - Integer() - 3, True],
    [Integer() + 2, Integer(), False],
    [Compose(Prime(), Natural()), Compose(Prime(), Natural()), True],
    [Compose(Prime() + 2, Natural() - 3), Compose(2 + Prime(), -3 + Natural()), True],
    [integral(Prime() + 2), integral(3 + Prime() - 1), True],
    [integral(Prime() + 2, start=2), integral(3 + Prime() - 1), False],
    [Geometric(2), Geometric(2), True],
    [Geometric(2), Geometric(1), False],
    [Arithmetic(2, 5), Arithmetic(2, 5), True],
    [Arithmetic(5, 2), Arithmetic(2, 5), False],
    [Power(2), Power(2), True],
    [Power(1), Power(2), False],
    [Const(2), Const(2), True],
    [Const(1), Const(2), False],
    [Fib(2, 3), Fib(2, 3), True],
    [Fib(2, 3), Fib(2, 4), False],
    [Polygonal(20), Polygonal(20), True],
    [Polygonal(2), Polygonal(20), False],
])
def test_sequence_equals(seq_a, seq_b, equals):
    assert seq_a.equals(seq_b) is equals


_sequences = list(Sequence.get_registry().values())

@pytest.mark.parametrize('sequence', _sequences)
def test_verify_traits(sequence):
    items = sequence.get_values(20)
    for trait in sequence.traits:
        assert verify_traits(items, trait)
