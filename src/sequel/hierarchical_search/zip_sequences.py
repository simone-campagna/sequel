"""
Search zip algorithm class
"""

import itertools

from ..items import Items
from ..sequence import Zip

from .base import RecursiveSearchAlgorithm


__all__ = [
    "SearchCombine",
]


class SearchZip(RecursiveSearchAlgorithm):
    """Search for s1 | s2"""
    __min_items__ = 3
    __accepts_undefined__ = True

    def __init__(self, sub_algorithm, name=None, max_level=2):
        super().__init__(sub_algorithm=sub_algorithm, name=name)
        self.max_level = max_level

    def _impl_call(self, catalog, items, info, options):
        for level in range(2, self.max_level + 1):
            level_info = info.sub(rank=level + 1)
            base_rank = level_info.rank
            sub_items_list = [Items(items[i::level]) for i in range(level)]
            for res_list in itertools.product(*[self.sub_search(catalog, sub_items, info, options) for sub_items in sub_items_list]):
                seq_list = [x[0] for x in res_list]
                info_list = [x[1] for x in res_list]
                max_depth = max(i.depth for i in info_list)
                sum_rank = base_rank + max(i.rank - base_rank for i in info_list)
                yield Zip(*seq_list), info._replace(depth=max_depth, rank=sum_rank)
