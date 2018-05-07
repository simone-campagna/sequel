"""
Base Algorithm
"""

import abc

from ..items import Items
from ..utils import sequence_matches
from ..item import Item

__all__ = [
    "Algorithm",
    "RecursiveAlgorithm",
]


class Algorithm(abc.ABC):
    __min_items__ = 3
    __accepts_undefined__ = False
    __init_keys__ = []

    def min_items(self):
        return self.__min_items__

    def accepts_undefined_items(self):
        return self.__accepts_undefined__

    def __call__(self, manager, items, rank):
        if not isinstance(items, Items):
            items = Items(items)
        if len(items) < self.min_items():
            return  # too few items
        if items.is_fully_defined() or self.accepts_undefined_items():
            yield from self.iter_sequences(manager, items, rank)
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
            for sequence in self.iter_sequences(manager, search_items, rank):
                if sequence_matches(sequence, items):
                    yield sequence

    @abc.abstractmethod
    def iter_sequences(self, manager, items, rank):
        raise NotImplementedError()

    def _repr_kwargs(self):
        return ["{}={!r}".format(key, getattr(self, key)) for key in self.__init_keys__]

    def __repr__(self):
        return "{}({})".format(type(self).__name__, ", ".join(self._repr_kwargs()))


class RecursiveAlgorithm(Algorithm):

    @abc.abstractmethod
    def rank_increase(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def sub_search(self, manager, items, rank):
        raise NotImplementedError()

    def iter_sequences(self, manager, items, rank):
        yield from ()
        self.sub_search(manager, items, rank)

    def sub_queue(self, manager, rank, items, sub_items, callback, kwargs):
        dependency = manager.make_dependency(
            algorithm=self,
            callback=callback,
            items=items,
            kwargs=kwargs)
        manager.queue(sub_items, rank=rank + self.rank_increase(), dependencies=[dependency])
