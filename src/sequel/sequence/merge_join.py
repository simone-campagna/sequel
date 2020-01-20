"""
Merge & join
"""

import abc

from .base import Iterator

__all__ = [
    'join',
    'merge',
]


class basemerge(Iterator):
    def __init__(self, sequence, *cuts, join=True):
        self._sequence = self.make_sequence(sequence)
        self._cuts = []
        cuts = list(cuts)
        while cuts:
            cut = int(cuts.pop(0))
            seq = self.make_sequence(cuts.pop(0))
            self._cuts.append((cut, seq))
        self._cuts.sort(key=lambda x: x[0])
        self._join = join

    def __iter__(self):
        itsequence = iter(self._sequence)
        cuts = list(self._cuts)
        if cuts:
            next_cut, next_sequence = cuts.pop(0)
        else:
            next_cut, next_sequence = None, None
        index = 0
        while True:
            if next_cut and index >= next_cut:
                itsequence = iter(next_sequence)
                if not self._join:
                   # advance sequence:
                   for item in zip(range(index), itsequence):
                       pass
                if cuts:
                    next_cut, next_sequence = cuts.pop(0)
                else:
                    next_cut, next_sequence = None, None
            yield next(itsequence)
            index += 1


class merge(basemerge):
    def __init__(self, sequence, *cuts):
        super().__init__(sequence, *cuts, join=False)


class join(basemerge):
    def __init__(self, sequence, *cuts):
        super().__init__(sequence, *cuts, join=True)
