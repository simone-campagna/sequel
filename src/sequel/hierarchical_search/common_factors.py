"""
Search for common factors
"""

from ..items import Items
from ..utils import gcd, divisors, sequence_matches

from .base import RecursiveSearchAlgorithm


__all__ = [
    "SearchCommonFactors",
]


class SearchCommonFactors(RecursiveSearchAlgorithm):
    """Search for sequence s(n) = C * s1(n)"""
    __min_items__ = 3
    __accepts_undefined__ = False

    def __init__(self, sub_algorithm, name=None,
                 max_value=2**100, max_divisors=10):
        super().__init__(sub_algorithm=sub_algorithm, name=name)
        self.max_value = max_value
        self.max_divisors = max_divisors

    def _impl_call(self, catalog, items, info, options):
        items_gcd = gcd(*items)
        if items_gcd > self.max_value:
            return
        divisors_list = [d for d in divisors(items_gcd) if d != 1]
        divisors_list.sort(reverse=True)  # largest first
        info = info.sub(rank=1)
        for divisor in divisors_list:
            sub_items = Items(item // divisor for item in items)
            for sub_sequence, sub_info in self.sub_search(catalog, sub_items, info, options):
                sequence = divisor * sub_sequence
                if sequence_matches(sequence, items):
                    yield sequence, sub_info
