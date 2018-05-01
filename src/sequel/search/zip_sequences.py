"""
Search zip algorithm class
"""

import itertools

from ..items import Items
from ..sequence import Zip
from ..utils import sequence_matches

from .base import SearchAlgorithm


__all__ = [
    "SearchZip",
]


class SearchZip(SearchAlgorithm):
    """Search for Zip(s1, s2, ...)"""
    __min_items__ = 3
    __accepts_undefined__ = True

    def __init__(self, max_level=3):
        super().__init__()
        self.max_level = max_level

    def iter_sequences(self, manager, items, priority):
        yield from ()
        for level in range(2, self.max_level + 1):
            sub_items = Items(items[0::level])
            if len(sub_items) < 3:
                continue
            sub_priority = priority + level - 1
            dependency = manager.make_dependency(
                callback=self._found_sequence,
                items=items,
                orig_items=items,
                priority=sub_priority,
                results=(),
                index=0,
                level=level)
            manager.queue(sub_items, priority=sub_priority, dependencies=[dependency])
 
    def _found_sequence(self, manager, items, sequences, orig_items, priority, results, index, level):
        if index < level:
            results += (sequences,)
            index += 1
            sub_items = Items(items[index::level])
            dependency = manager.make_dependency(
                callback=self._found_sequence,
                items=items,
                orig_items=orig_items,
                priority=priority,
                results=results,
                index=index,
                level=level)
            manager.queue(sub_items, priority=priority, dependencies=[dependency])
        else:
            for seq_list in itertools.product(*results):
                sequence = Zip(*seq_list)
                if sequence_matches(sequence, orig_items):
                    yield sequence
