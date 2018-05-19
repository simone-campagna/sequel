import pytest

from sequel.item import (
    Item, Any, ANY, Interval,
    LowerBound, UpperBound, Set, Value, make_item
)
from sequel.items import Items, make_items


def equals(lst0, lst1):
    if len(lst0) != len(lst1):
        return False
    for i0, i1 in zip(lst0, lst1):
        if isinstance(i0, Item):
            if isinstance(i1, Item):
                match = i0.equals(i1)
            else:
                match = False
        elif isinstance(i1, Item):
            match = False
        else:
            match = i0 == i1
        if not match:
            return False
    return True


_tests = [
    ([], 0, []),
    ([1, 2, 3], 3, [1, 2, 3]),
    ([1, ANY, 3], None, [1, ANY, 3]),
    ([Value(1), Interval(2, 2), Set(3)], 3, [1, 2, 3]),
    ([Value(1), Interval(2, 3), Set(3, 5, 7)], 6, [1, Interval(2, 3), Set(3, 5, 7)]),
    ([Value(1), Interval(2, 3), LowerBound(2), Set(3, 5, 7)], None, [1, Interval(2, 3), LowerBound(2), Set(3, 5, 7)]),
    ([Value(1), Interval(2, 3), UpperBound(4), Set(3, 5, 7)], None, [1, Interval(2, 3), UpperBound(4), Set(3, 5, 7)]),
]


@pytest.mark.parametrize("items, size, dummy_values", _tests)
def test_items(items, size, dummy_values):
    it = Items(items)
    assert it.size == size
    assert equals(list(it), items)


@pytest.mark.parametrize("items, size, values", _tests)
def test_make_items_default(items, size, values):
    it = make_items(items)
    assert it.size == size
    assert equals(list(it), values)


@pytest.mark.parametrize("items, size, values", _tests)
def test_make_items_simplify(items, size, values):
    it = make_items(items, simplify=True)
    assert it.size == size
    assert equals(list(it), values)


@pytest.mark.parametrize("items, size, dummy_values", _tests)
def test_make_items_no_simplify(items, size, dummy_values):
    it = make_items(items, simplify=False)
    assert it.size == size
    assert equals(list(it), [make_item(x, simplify=False) for x in items])


@pytest.mark.parametrize("i0, i1, result", [
    (Items([]), Items([]), True),
    (Items([2]), Items([]), False),
    (Items([]), Items([2]), False),
    (Items([2]), Items([2]), True),
    (Items([2, 3]), Items([2]), False),
    (Items([2]), Items([2, 3]), False),
    (Items([2, 3]), Items([2, 3]), True),
    (Items([2, 3]), Items([2, Value(3)]), False),
    (Items([2, 3]), Items([2, ANY]), False),
    (Items([2, Value(3)]), Items([2, 3]), False),
    (Items([2, ANY]), Items([2, 3]), False),
    (Items([2, Value(3)]), Items([2, Value(4)]), False),
    (Items([2, Interval(3, 5)]), Items([2, Interval(3, 5)]), True),
    (Items([2, Interval(3, 4)]), Items([2, Interval(3, 5)]), False),
    (Items([2, LowerBound(3)]), Items([2, LowerBound(3)]), True),
    (Items([2, LowerBound(4)]), Items([2, LowerBound(3)]), False),
    (Items([2, UpperBound(3)]), Items([2, LowerBound(3)]), False),
    (Items([2, UpperBound(3)]), Items([2, UpperBound(3)]), True),
    (Items([2, UpperBound(3)]), Items([2, UpperBound(4)]), False),
])
def test_items_equals(i0, i1, result):
    assert i0.equals(i1) == result
