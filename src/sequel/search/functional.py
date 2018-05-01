"""
Search integral/derivative algorithm class
"""


from ..items import Items
from ..sequence import integral, derivative, summation, product
from ..utils import sequence_matches

from .base import SearchAlgorithm


__all__ = [
    "SearchSummation",
    "SearchProduct",
    "SearchIntegral",
    "SearchDerivative",
]


class SearchSummation(SearchAlgorithm):
    """Search for sums"""
    __min_items__ = 3
    __accepts_undefined__ = False

    def iter_sequences(self, manager, items, priority):
        yield from ()
        s_items = []
        last = 0
        for item in items:
            value = item - last
            s_items.append(value)
            last = item
        sub_items = Items(s_items)
        # print("sum:", [int(x) for x in sub_items])
        dependency = manager.make_dependency(
            callback=self._found_operand,
            items=items)
        manager.queue(sub_items, priority=priority + 1, dependencies=[dependency])

    def _found_operand(self, manager, items, sequences):
        for operand in sequences:
            sequence = summation(operand)
            if sequence_matches(sequence, items):
                yield sequence

 
class SearchProduct(SearchAlgorithm):
    """Search for prods"""
    __min_items__ = 3
    __accepts_undefined__ = False

    def iter_sequences(self, manager, items, priority):
        yield from ()
        s_items = []
        last = 1
        for item in items:
            if last == 0:
                value = 0
            else:
                value, mod = divmod(item, last)
                if mod != 0:
                    return
            s_items.append(value)
            last = item
        sub_items = Items(s_items)
        dependency = manager.make_dependency(
            callback=self._found_operand,
            items=items)
        manager.queue(sub_items, priority=priority + 1, dependencies=[dependency])

    def _found_operand(self, manager, items, sequences):
        for operand in sequences:
            sequence = product(operand)
            if sequence_matches(sequence, items):
                yield sequence


class SearchIntegral(SearchAlgorithm):
    """Search for integrals"""
    __min_items__ = 3
    __accepts_undefined__ = False

    def iter_sequences(self, manager, items, priority):
        yield from ()
        if items.derivative:
            sub_items = Items(items.derivative)
            dependency = manager.make_dependency(
                callback=self._found_operand,
                items=items)
            manager.queue(sub_items, priority=priority + 1, dependencies=[dependency])

    def _found_operand(self, manager, items, sequences):
        for operand in sequences:
            sequence = integral(operand, start=items[0]).simplify()
            if sequence_matches(sequence, items):
                yield sequence


class SearchDerivative(SearchAlgorithm):
    """Search for derivatives"""
    __min_items__ = 3
    __accepts_undefined__ = False

    def iter_sequences(self, manager, items, priority):
        yield from ()
        sub_items = Items(items.make_integral())
        dependency = manager.make_dependency(
            callback=self._found_operand,
            items=items)
        manager.queue(sub_items, priority=priority + 1, dependencies=[dependency])

    def _found_operand(self, manager, items, sequences):
        for operand in sequences:
            sequence = derivative(operand).simplify()
            if sequence_matches(sequence, items):
                yield sequence
