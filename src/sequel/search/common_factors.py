"""
Search for common factors
"""

from ..items import Items
from ..utils import gcd, divisors, sequence_matches, assert_sequence_matches

from .base import SearchAlgorithm


__all__ = [
    "SearchCommonFactors",
]


class SearchCommonFactors(SearchAlgorithm):
    """Search for sequence s(n) = C * s1(n)"""
    __min_items__ = 3
    __accepts_undefined__ = False

    def __init__(self, max_value=2**100, max_divisors=10):
        super().__init__()
        self.max_value = max_value
        self.max_divisors = max_divisors

    def iter_sequences(self, manager, items, priority):
        yield from ()
        # try to find lseq matching [items * common_divisor]
        items_gcd = gcd(*items)
        if items_gcd > self.max_value:
            return
        divisors_list = [d for d in divisors(items_gcd) if d != 1]
        divisors_list.sort(reverse=True)  # largest first
        for divisor in divisors_list:
            sub_items = Items(item // divisor for item in items)
            dependency = manager.make_dependency(
                callback=self._found_left,
                items=items,
                divisor=divisor)
            manager.queue(sub_items, priority=priority + 1, dependencies=[dependency])


    def _found_left(self, manager, items, sequences, divisor):
        for l_sequence in sequences:
            sequence = l_sequence * divisor
            assert_sequence_matches(sequence, items)
            yield sequence

