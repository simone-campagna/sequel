import collections
import bisect
import enum
import json
import pickle

from .lazy import gmpy2
from .sequence import Sequence

__all__ = [
    "Catalog",
    "create_catalog",
    "load_catalog",
    "store_catalog",
]


class Catalog(object):

    def __init__(self, size):
        self._size = size
        self._lst_values = []
        self._lst_sequences = []
        self._all_sequences = set()

    @property
    def size(self):
        return self._size

    def register(self, *sequences, items=()):
        items = tuple(items)
        if len(items) > self._size:
            items = items[:self._size]
        lst_values = self._lst_values
        lst_sequences = self._lst_sequences
        sequences = set(sequences).difference(self._all_sequences)
        if not sequences:
            return
        self._all_sequences.update(sequences)
        if len(items) < self._size:
            data = []
            for sequence in sequences:
                s_items = tuple(sequence.get_values(self._size))
                data.append((s_items, [sequence]))
        else:
            data = [(items, sequences)]
        for items, sequences in data:
            index = bisect.bisect_left(lst_values, items)
            if index >= len(lst_values):
                lst_values.append(items)
                lst_sequences.append(set(sequences))
            else:
                values = lst_values[index]
                if values == items:
                    lst_sequences[index].update(sequences)
                else:
                    lst_values.insert(index, items)
                    lst_sequences.insert(index, set(sequences))
            
    def iter_sequences_values(self):
        yield from zip(self._lst_sequences, self._lst_values)

    def iter_matching_sequences(self, items):
        #items = tuple(items)
        if len(items) > self._size:
            items = items[:self._size]
        if items.is_fully_defined():
            lst_values = self._lst_values
            lst_sequences = self._lst_sequences
            index = bisect.bisect_left(lst_values, items)
            for idx in range(index, len(lst_values)):
                values = lst_values[idx]
                if all(i == v for i, v in zip(items, values)):
                    yield from lst_sequences[idx]
                else:
                    break
        else:
            for values, sequences in zip(self._lst_values, self._lst_sequences):
                if all(x == y for x, y in zip(values, items)):
                    yield from sequences

    def __reduce__(self):
        return (
            self.size,
            tuple(str(sequence) for sequence in self._all_sequences),
            tuple(tuple(int(x) for x in values) for values in self._lst_values),
            tuple(tuple(str(sequence) for sequence in sequences) for sequences in self._lst_sequences),
        )

    @classmethod
    def from_status(cls, state):
        state_size, state_sequences, state_lst_values, state_lst_sequences = state
        sequence_dict = {}
        for sequence_source in state_sequences:
            sequence = Sequence.compile(sequence_source)
            sequence_dict[sequence_source] = sequence
        instance = cls(state_size)
        instance._all_sequences.update(sequence_dict)
        lst_values = instance._lst_values
        lst_sequences = instance._lst_sequences
        mpz = gmpy2.mpz
        for values, sequence_sources in zip(state_values, state_sequences):
            lst_values.append([mpz(x) for x in values])
            lst_sequences.append([sequence_dict[sequence_source] for sequence_source in sequence_sources])
        return instance


def create_catalog(size):
    catalog = Catalog(size=size)
    for sequence in Sequence.get_registry().values():
        catalog.register(sequence)
    return catalog


def store_catalog(catalog, filename):
    with open(filename, "w") as file:
        pickle.dump(catalog, file)


def load_catalog(filename):
    with open(filename, "r") as file:
        return pickle.load(file)
