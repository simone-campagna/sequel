"""
Search for common factors
"""

from ..items import Items
from ..utils import gcd, divisors, sequence_matches, assert_sequence_matches

from .base import RecursiveAlgorithm


__all__ = [
    "CommonFactorsAlgorithm",
]


class CommonFactorsAlgorithm(RecursiveAlgorithm):
    """Search for sequence s(n) = C * s1(n)"""
    __min_items__ = 3
    __accepts_undefined__ = False
    __init_keys__ = ["max_value", "max_divisors"]

    def __init__(self, max_value=2**100, max_divisors=10):
        super().__init__()
        self.max_value = max_value
        self.max_divisors = max_divisors

    def rank_increase(self):
        return 1

    def sub_search(self, manager, items, rank):
        # try to find lseq matching [items * common_divisor]
        items_gcd = gcd(*items)
        if items_gcd > self.max_value:
            return
        divisors_list = [d for d in divisors(items_gcd) if d != 1]
        divisors_list.sort(reverse=True)  # largest first
        for divisor in divisors_list:
            sub_items = Items(item // divisor for item in items)
            self.sub_queue(
                manager, rank, items, sub_items, self._found_left,
                {'divisor': divisor})

    def _found_left(self, manager, items, sequences, divisor):
        for l_sequence in sequences:
            sequence = l_sequence * divisor
            assert_sequence_matches(sequence, items)
            yield sequence

