"""
Base SearchAlgorithm
"""

import abc

from ..items import Items
from ..utils import sequence_matches
from ..item import Item

__all__ = [
    "SearchAlgorithm",
]


class SearchAlgorithm(abc.ABC):
    __min_items__ = 3
    __accepts_undefined__ = False

    def min_items(self):
        return self.__min_items__

    def accepts_undefined_items(self):
        return self.__accepts_undefined__

    def accepts(self, items, info, options):
        min_items = self.min_items()
        if len(items) < min_items:
            return False, "too few items: {!r} < {!r}".format(len(items), min_items)
        elif info.depth > info.max_depth:
            return False, "depth exceeded: {!r} > {!r}".format(info.depth, info.max_depth)
        elif info.rank > info.max_rank:
            return False, "rank exceeded: {!r} > {!r}".format(info.rank, info.max_rank)
        elif (not self.accepts_undefined_items()) and not items.is_fully_defined():
            return False, "not fully defined"
        return True, ""

    def __call__(self, manager, items, priority):
        if not isinstance(items, Items):
            items = Items(items)
        if len(items) < self.min_items():
            return  # too few items
        if items.is_fully_defined() or self.accepts_undefined_items():
            yield from self.iter_sequences(manager, items, priority)
        else:
            # try with sub_items:
            search_items = []
            for item in items:
                if isinstance(item, Item):
                    break
                search_items.append(item)
            search_items = Items(search_items)
            if len(search_items) < self.min_items():
                return  # too few items
            for sequence in self.iter_sequences(manager, search_items, priority):
                if sequence_matches(sequence, items):
                    yield sequence

    @abc.abstractmethod
    def iter_sequences(self, manager, items, priority):
        raise NotImplementedError()

    def __repr__(self):
        return "{}()".format(type(self).__name__)
