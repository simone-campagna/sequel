"""
Search zip algorithm class
"""

import itertools

from ..items import Items
from ..sequence import roundrobin
from ..utils import sequence_matches

from .base import RecursiveAlgorithm


__all__ = [
    "RoundrobinAlgorithm",
]


class RoundrobinAlgorithm(RecursiveAlgorithm):
    """Search for roundrobin(s1, s2, ...)"""
    __min_items__ = 3
    __accepts_undefined__ = True
    __init_keys__ = ["max_level"]

    def __init__(self, max_level=3):
        super().__init__()
        self.max_level = max_level

    def rank_increase(self, rank):
        return rank + 1

    def sub_search(self, manager, items, rank):
        for level in range(2, self.max_level + 1):
            sub_items = Items(items[0::level])
            if len(sub_items) < 3:
                continue
            sub_rank = rank + level - 2
            self.sub_queue(
                manager, sub_rank, items, sub_items, self._found_sequence,
                {'orig_items': items, 'sub_rank': sub_rank, 'results': (), 'index': 0, 'level': level})
 
    def _found_sequence(self, manager, items, sequences, orig_items, sub_rank, results, index, level):
        if index < level:
            results += (sequences,)
            index += 1
            sub_items = Items(items[index::level])
            self.sub_queue(
                manager, sub_rank, items, sub_items, self._found_sequence,
                {'orig_items': orig_items, 'sub_rank': sub_rank, 'results': results, 'index': index, 'level': level})
        else:
            if results:
                for seq_list in itertools.product(*results):
                    sequence = roundrobin(*seq_list)
                    if sequence_matches(sequence, orig_items):
                        yield sequence
