import pytest
from sequel import sequence
from sequel.sequence.sequence_utils import (
    make_linear_combination,
    make_power,
)


_p = sequence.compile_sequence('p')
_fib01 = sequence.compile_sequence('fib01')
_m_exp = sequence.compile_sequence('m_exp')
_p_5 = sequence.Const(5)
_m_5 = sequence.Const(-5)
_p_10 = sequence.Const(10)
_m_10 = sequence.Const(-10)
_p_20 = sequence.Const(20)
_m_20 = sequence.Const(-20)

@pytest.mark.parametrize("coeffs, items, denom, result", [
    [[1, 2, 3], [_p, _fib01, _m_exp], 1, _p + 2 * _fib01 + 3 * _m_exp],
    [[1, -2, 0], [_p, _fib01, _m_exp], 1, _p - 2 * _fib01],
    [[-1, -2, 0], [_p, _fib01, _m_exp], 1, -_p - 2 * _fib01],
    [[-3, -2, 0], [_p, _fib01, _m_exp], 1, -3 * _p - 2 * _fib01],
    [[1, -2, 0], [_p, _fib01, _m_exp], -1, -_p + 2 * _fib01],
    [[1, -2, 0], [_p, _fib01, _m_exp], -2, (-_p + 2 * _fib01) // 2],
    [[2, -2, 4], [_p, _fib01, _m_exp], -2, -_p + _fib01 - 2 * _m_exp],
    [[12, -15, 6], [_p, _fib01, _m_exp], -3, -4 * _p + 5 * _fib01 - 2 * _m_exp],
    [[12, -15, 6], [_p, _fib01, _m_exp], -6, (-4 * _p + 5 * _fib01 - 2 * _m_exp) // 2],
    [[12, -18, 60], [_p, _fib01, _m_exp], -30, (-2 * _p + 3 * _fib01 - 10 * _m_exp) // 5],
    [[2], [_p_10], 1, _p_20],
    [[-2], [_p_10], 1, _m_20],
    [[2], [_m_10], 1, _m_20],
    [[-2], [_m_10], 1, _p_20],
    [[2], [_p_10], 2, _p_10],
    [[-2], [_p_10], 2, _m_10],
    [[2], [_m_10], 2, _m_10],
    [[-2], [_m_10], 2, _p_10],
    [[2], [_p_10], 4, _p_5],
    [[-2], [_p_10], 4, _m_5],
    [[2], [_m_10], 4, _m_5],
    [[-2], [_m_10], 4, _p_5],
    [[1, 2], [_p, _p_10], 1, _p + _p_20],
    [[1, -2], [_p, _p_10], 1, _p - _p_20],
    [[1, 2], [_p, _m_10], 1, _p - _p_20],
    [[1, -2], [_p, _m_10], 1, _p + _p_20],
    [[-12, 1, 0], [sequence.Const(1), 7, 0], 1, sequence.Const(-5)],
])
def test_make_linear_combination(coeffs, items, denom, result):
    r = make_linear_combination(coeffs, items, denom)
    print(coeffs, items, "|||", r, "|||", result)
    assert r.equals(result)
    assert str(r) == str(result)


@pytest.mark.parametrize("item, power, result", [
    [_p, 0, _p ** 0],
    [_p, 1, _p],
    [-_p, 1, -_p],
    [_p, 2, _p ** 2],
    [-_p, 2, (-_p) ** 2],
    [_p_10, 2, sequence.compile_sequence('100')],
])
def test_make_power(item, power, result):
    r = make_power(item, power)
    #print(r)
    #print(result)
    assert r.equals(result)
    assert str(r) == str(result)

