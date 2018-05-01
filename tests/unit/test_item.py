import operator

import gmpy2

import pytest

from sequel.item import Item, Any, ANY, Range, Set, Value, make_item, simplify_item



def test_any_is_singleton():
    assert ANY is Any()


@pytest.mark.parametrize("operator, left, right, result", [
    (operator.eq, ANY, -10, True),
    (operator.eq, ANY, 0, True),
    (operator.eq, ANY, 10, True),
    (operator.ne, ANY, -10, False),
    (operator.ne, ANY, 0, False),
    (operator.ne, ANY, 10, False),
    (operator.eq, Range(-3, 3), -4, False),
    (operator.eq, Range(-3, 3), -3, True),
    (operator.eq, Range(-3, 3), 0, True),
    (operator.eq, Range(-3, 3), 3, True),
    (operator.eq, Range(-3, 3), 4, False),
    (operator.eq, Set(-3, 2), -3, True),
    (operator.eq, Set(-3, 2), -2, False),
    (operator.eq, Set(-3, 2), 2, True),
    (operator.eq, Set(-3, 2), 3, False),
])
def test_item_comparison(operator, left, right, result):
    assert operator(left, right) == result
    assert operator(right, left) == result


@pytest.mark.parametrize("source, kwargs, value", [
    ("12", {}, 12),
    ("12", {'simplify': False}, Value(12)),
    ("12", {'simplify': True}, 12),
    ("-2", {}, -2),
    ("ANY", {}, ANY),
    ("ANY", {'simplify': False}, ANY),
    ("Any()", {}, ANY),
    ("%", {}, ANY),
    ("Range(2, 2)", {}, 2),
    ("Range(2, 2)", {'simplify': False}, Range(2, 2)),
    ("2..2", {}, 2),
    ("2..2", {'simplify': False}, Range(2, 2)),
    ("Range(2, 4)", {}, Range(2, 4)),
    ("2..4", {}, Range(2, 4)),
    ("Set(2)", {}, 2),
    ("Set(2)", {'simplify': False}, Set(2)),
    ("Set(2, 4)", {}, Set(2, 4)),
    ("2,4", {}, Set(2, 4)),
    ("2,3,100", {}, Set(2, 3, 100)),
])
def test_make_item(source, kwargs, value):
    v = make_item(source, **kwargs)
    if isinstance(value, Item):
        assert value.equals(v)
    else:
        assert value == v


@pytest.mark.parametrize("value, size, values", [
    (ANY, None, None),
    (Value(12), 1, [12]),
    (Range(-2, 2), 5, [-2, -1, 0, 1, 2]),
    (Set(2, 3), 2, [2, 3]),
    (Set(2), 1, [2]),
])
def test_item_size(value, size, values):
    assert value.size == size
    if size is None:
        with pytest.raises(ValueError):
            l = tuple(value.iter_values())
    else:
        assert sorted(value.iter_values()) == sorted(values)


@pytest.mark.parametrize("value, simplified", [
    (ANY, ANY),
    (Value(12), 12),
    (Range(-2, 2), Range(-2, 2)),
    (Range(-2, -2), -2),
    (Set(2, 3), Set(2, 3)),
    (Set(2), 2),
    (10, 10),
])
def test_simplify_item(value, simplified):
    v = simplify_item(value)
    if isinstance(simplified, Item):
        assert simplified.equals(v)
    else:
        assert simplified == v
