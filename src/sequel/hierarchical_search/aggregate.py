"""
Aggregate SearchAlgorithm
"""

from .base import SearchAlgorithm
import copy


__all__ = [
    "SearchAggregate",
]


class SearchAggregate(SearchAlgorithm):
    __serialization_keys__ = SearchAlgorithm.__serialization_keys__ + ['algorithms']
    __accepts_undefined__ = True
    __min_items__ = 1

    def __init__(self, algorithms, name=None):
        super().__init__(name=name)
        self.algorithms = []
        self.add_algorithms(*algorithms)

    def add_algorithms(self, *algorithms):
        for algorithm in algorithms:
            if not isinstance(algorithm, SearchAlgorithm):
                raise TypeError("{!r} is not a SearchAlgorithm".format(algorithm))
            self.algorithms.append(algorithm)

    def to_dict(self, serialization):
        dct = super().to_dict(serialization)
        dct["algorithms"] = [serialization.store(algorithm) for algorithm in self.algorithms]
        return dct

    @classmethod
    def from_dict(cls, dct, serialization):
        algorithm_names = dct["algorithms"]
        dct["algorithms"] = []
        instance, initializers = super().from_dict(dct, serialization)
        initializers += [lambda x: x.add_algorithms(*[serialization.load(name) for name in algorithm_names])]
        return instance, initializers

    def _impl_call(self, catalog, items, info, options):
        info = info.sub(rank=1)
        found_sequences = set()
        for algorithm in self.algorithms:
            num_found = 0
            for sequence, sub_info in algorithm(catalog, items, info, options):
                if sequence not in found_sequences:
                    yield sequence, sub_info
                    found_sequences.add(sequence)
                    num_found += 1
            if num_found > 0:
                break
