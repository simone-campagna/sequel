"""
Search integral/derivative algorithm class
"""


from ..items import Items
from ..sequence import integral, derivative, summation, product
from ..utils import sequence_matches

from .base import RecursiveSearchAlgorithm


__all__ = [
    "SearchSummation",
    "SearchProduct",
    "SearchIntegral",
    "SearchDerivative",
]


class SearchSum(RecursiveSearchAlgorithm):
    """Search for sums"""
    __min_items__ = 3
    __accepts_undefined__ = False

    def __init__(self, sub_algorithm, name=None):
        super().__init__(sub_algorithm=sub_algorithm, name=name)

    def _impl_call(self, catalog, items, info, options):
        s_items = []
        last = 0
        for item in items:
            value = item - last
            s_items.append(value)
            last = item
        sub_items = Items(s_items)
        # print("sum:", [int(x) for x in sub_items])
        info = info.sub(rank=1)
        for sequence, sub_info in self.sub_search(catalog, sub_items, info, options):
            seq = summation(sequence)
            if sequence_matches(seq, items):
                yield seq, sub_info


class SearchProd(RecursiveSearchAlgorithm):
    """Search for prods"""
    __min_items__ = 3
    __accepts_undefined__ = False

    def __init__(self, sub_algorithm, name=None):
        super().__init__(sub_algorithm=sub_algorithm, name=name)

    def _impl_call(self, catalog, items, info, options):
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
        # print("prod:", [int(x) for x in items], "->", [int(x) for x in sub_items])
        info = info.sub(rank=1)
        for sequence, sub_info in self.sub_search(catalog, sub_items, info, options):
            seq = product(sequence)
            if sequence_matches(seq, items):
                yield seq, sub_info


class SearchIntegral(RecursiveSearchAlgorithm):
    """Search for integrals"""
    __min_items__ = 3
    __accepts_undefined__ = False

    def __init__(self, sub_algorithm, name=None):
        super().__init__(sub_algorithm=sub_algorithm, name=name)

    def _impl_call(self, catalog, items, info, options):
        if items.derivative:
            sub_items = Items(items.derivative)
            info = info.sub(rank=1)
            for sequence, sub_info in self.sub_search(catalog, sub_items, info, options):
                seq = integral(sequence, start=items[0]).simplify()
                #print("dd..", derivative, sequence, [x for x, _ in zip(sequence, derivative)])
                #print("dd->", items, seq, [x for x, _ in zip(seq, items)])
                if sequence_matches(seq, items):
                    yield seq, sub_info


class SearchDerivative(RecursiveSearchAlgorithm):
    """Search for derivatives"""
    __min_items__ = 3
    __accepts_undefined__ = False

    def __init__(self, sub_algorithm, name=None):
        super().__init__(sub_algorithm=sub_algorithm, name=name)

    def _impl_call(self, catalog, items, info, options):
        sub_items = Items(items.make_integral())
        info = info.sub(rank=1)
        for sequence, sub_info in self.sub_search(catalog, sub_items, info, options):
            #print("ii..", integral, sequence, [x for x, _ in zip(sequence, integral)])
            #print("ii->", items, seq, [x for x, _ in zip(seq, items)])
            seq = derivative(sequence).simplify()
            if sequence_matches(seq, items):
                yield seq, sub_info
