"""
Search composition algorithm class
"""

import collections
import itertools

from ..items import Items
from ..sequence import Trait, Integer, Sequence
from ..utils import sequence_matches

from .base import RecursiveAlgorithm


__all__ = [
    "ComposeAlgorithm",
]


class ComposeAlgorithm(RecursiveAlgorithm):
    """Search for sequence composition"""
    __min_items__ = 5
    __accepts_undefined__ = False
    __init_keys__ = ["group_size", "cache_size", "max_abs_value", "max_results"]

    def __init__(self, group_size=2, cache_size=1000, max_abs_value=10 ** 10, max_results=10):
        super().__init__()
        self.group_size = group_size
        self.cache_size = cache_size
        self.max_abs_value = abs(max_abs_value)
        self.max_results = max_results
        self.__cache = None

    def rank_increase(self, rank):
        if rank == 0:
            return rank
        else:
            return rank + 1

    def _get_cache(self, catalog):
        if self.__cache is None:
            generic_cache = []
            injective_cache = collections.defaultdict(dict)

            excluded = {Integer()}

            for sequence in Sequence.get_registry().values():
                if sequence in excluded or sequence.has_traits(Trait.SLOW) or sequence.has_traits(Trait.FAST_GROWING):
                    continue
                iterator = enumerate(sequence.get_values(self.cache_size))
                if sequence.has_traits(Trait.INJECTIVE):
                    for index, item in iterator:
                        injective_cache[item][sequence] = index
                else:
                    item_indices = collections.defaultdict(list)
                    for index, item in iterator:
                        if len(item_indices[item]) < self.group_size:
                            item_indices[item].append(index)
                        if abs(item) > self.max_abs_value:
                            break
                    generic_cache.append((sequence, item_indices))
            self.__cache = {
                'injective': injective_cache,
                'generic': generic_cache,
            }
        return self.__cache

    def iterindices(self, catalog, items):
        cache = self._get_cache(catalog)
        # inj:
        candidates = set()
        injective_cache = cache['injective']
        for sequence in injective_cache[items[0]]:
            candidates.add(sequence)
        for item in items[1:]:
            s_indices = set(injective_cache[item])
            candidates.intersection_update(s_indices)
            if not candidates:
                break
        for sequence in candidates:
            indices = [injective_cache[item][sequence] for item in items]
            yield sequence, indices

        # generic:
        generic_cache = cache['generic']
        for sequence, item_indices in generic_cache:
            grps = []
            for item in items:
                if item in item_indices:
                    grps.append(item_indices[item])
                else:
                    break
            if len(grps) >= 5:
                if self.max_results is None:
                    until = itertools.count()
                else:
                    until = range(self.max_results)
                for indices, _ in zip(itertools.product(*grps), until):
                    # print("::: non-inj", sequence, indices)
                    yield sequence, indices

    def sub_search(self, manager, items, rank):
        for sequence, indices in self.iterindices(manager.catalog, items):
            sub_items = Items(indices)
            self.sub_queue(
                manager, rank, items, sub_items, self._found_index_sequence,
                {'sequence': sequence})

    def _found_index_sequence(self, manager, items, sequences, sequence):
        for index_sequence in sequences:
            sequence = sequence | index_sequence
            if sequence_matches(sequence, items):
                yield sequence
