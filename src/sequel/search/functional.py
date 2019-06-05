"""
Search integral/derivative algorithm class
"""


from ..items import Items
from ..sequence import integral, derivative, summation, product
from ..utils import sequence_matches

from .base import RecursiveAlgorithm


__all__ = [
    "SummationAlgorithm",
    "ProductAlgorithm",
    "IntegralAlgorithm",
    "DerivativeAlgorithm",
]


class SummationAlgorithm(RecursiveAlgorithm):
    """Search for sums"""
    __min_items__ = 3
    __accepts_undefined__ = False

    def rank_increase(self, rank):
        return rank + 1

    def sub_search(self, manager, items, rank):
        s_items = []
        last = 0
        for item in items:
            value = item - last
            s_items.append(value)
            last = item
        sub_items = Items(s_items)
        self.sub_queue(
            manager, rank, items, sub_items, self._found_operand,
            {})

    def _found_operand(self, manager, items, sequences):
        for operand in sequences:
            sequence = summation(operand)
            if sequence_matches(sequence, items):
                yield sequence

 
class ProductAlgorithm(RecursiveAlgorithm):
    """Search for prods"""
    __min_items__ = 3
    __accepts_undefined__ = False

    def rank_increase(self, rank):
        return rank + 1

    def sub_search(self, manager, items, rank):
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
        self.sub_queue(
            manager, rank, items, sub_items, self._found_operand,
            {})

    def _found_operand(self, manager, items, sequences):
        for operand in sequences:
            sequence = product(operand)
            if sequence_matches(sequence, items):
                yield sequence


class IntegralAlgorithm(RecursiveAlgorithm):
    """Search for integrals"""
    __min_items__ = 3
    __accepts_undefined__ = False

    def rank_increase(self, rank):
        return rank + 1

    def sub_search(self, manager, items, rank):
        if items.derivative:
            sub_items = Items(items.derivative)
            self.sub_queue(
                manager, rank, items, sub_items, self._found_operand,
                {})

    def _found_operand(self, manager, items, sequences):
        for operand in sequences:
            sequence = integral(operand, start=items[0]).simplify()
            if sequence_matches(sequence, items):
                yield sequence


class DerivativeAlgorithm(RecursiveAlgorithm):
    """Search for derivatives"""
    __min_items__ = 3
    __accepts_undefined__ = False

    def rank_increase(self, rank):
        return rank + 1

    def sub_search(self, manager, items, rank):
        sub_items = Items(items.make_integral())
        self.sub_queue(
            manager, rank, items, sub_items, self._found_operand,
            {})

    def _found_operand(self, manager, items, sequences):
        for operand in sequences:
            sequence = derivative(operand).simplify()
            if sequence_matches(sequence, items):
                yield sequence
