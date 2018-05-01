import pytest

from sequel.sequence import derivative, integral, compile_sequence


@pytest.mark.parametrize("source, ref_source", [
    ("derivative(p + 5)", "derivative(p)"),
    ("derivative(p - 5)", "derivative(p)"),
    ("derivative(3 * p - 5)", "derivative(3 * p)"),
    ("derivative(3 + 2 * p)", "derivative(2 * p)"),
    ("derivative(3 - 2 * p)", "derivative(-2 * p)"),
    ("derivative(integral(p))", "p"),
    ("derivative(integral(p, start=3))", "p"),
    ("derivative(integral(-2 * p))", "-2 * p"),
    ("integral(derivative(p))", "-2 + p"),
    ("integral(derivative(p), start=5)", "3 + p"),
])
def test_simplify(source, ref_source):
    sequence = compile_sequence(source)
    simpl_sequence = sequence.simplify()
    print(sequence, "->", simpl_sequence)
    assert simpl_sequence.get_values(10) == sequence.get_values(10)
    ref_sequence = compile_sequence(ref_source)
    assert simpl_sequence == ref_sequence
