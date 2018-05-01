"""
Sequence cache
"""

import collections

__all__ = [
    'Cache',
]


class Cache(object):
    def __init__(self, size=100):
        self._size = size
        self._cache = collections.OrderedDict()

    @property
    def size(self):
        return self._size

    def __len__(self):
        return len(self._cache)

    def __iter__(self):
        yield from self._cache

    def register(self, sequence):
        self._cache[sequence] = []

    def iter_sequence_values(self, num):
        for sequence in self._cache:
            values = self.get_values(sequence, num)
            yield sequence, values
            
    def iter_matching_sequences(self, items):
        for sequence, values in self.iter_sequence_values(len(items)):
            for item, value in zip(values, items):
                if item != value:
                    break
            else:
                yield sequence

    def get_values(self, sequence, num):
        if sequence in self._cache:
            cache = self._cache[sequence]
            if not cache:
                cache = sequence.get_values(max(self._size, num))
            if len(cache) < num:
                return cache + sequence.get_values(len(cache), start=num - len(cache))
            elif len(cache) > num:
                return cache[:num]
            else:
                return cache
        else:
            return [value for _, value in zip(range(num), sequence)]
            
    def matches(self, sequence, items):
        values = self.get_values(sequence, len(items))
        for item, value in zip(items, values):
            if item != value:
                return False
        return True
