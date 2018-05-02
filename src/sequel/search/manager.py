"""
Search manager
"""

import bisect
import collections
import itertools

from ..catalog import create_catalog
from ..items import make_items, Items

from .base import SearchAlgorithm


__all__ = [
    "Manager",
]


Dependency = collections.namedtuple(
    "Dependency", "callback items args kwargs")


class Entry(collections.namedtuple("EntryNT", "priority items dependencies")):
    def __new__(cls, priority, items, dependencies=()):
        return super().__new__(cls, priority, items, list(dependencies))

    def ordering_key(self):
        return (self.priority, -len(self.dependencies))

    def __lt__(self, other):
        return self.ordering_key() < other.ordering_key()


class Manager(object):
    def __init__(self, size):
        self.size = size
        self.catalog = create_catalog(size)
        self._queue = []
        self._queued_items = set()
        self._entries = {}
        self._results = set()
        self.algorithms = []

    def add_algorithm(self, algorithm):
        if not isinstance(algorithm, SearchAlgorithm):
            raise TypeError("{!r}: not a SearchAlgorithm".format(algorithm))
        self.algorithms.append(algorithm)

    def search(self, items):
        items = make_items(items)
        dependency = self.make_dependency(
            callback=self.set_result,
            items=())
        self.queue(items, priority=0, dependencies=[dependency])
        queue = self._queue
        results = self._results
        while queue and not results:
            entry = queue.pop(0)
            priority = entry.priority
            items = entry.items
            for algorithm in self.algorithms:
                sequences = set(algorithm(self, items, priority))
                if sequences:
                    self.set_found(priority, items, sequences)
                if results:
                    break
            self._queued_items.discard(entry.items)
        # while self._queue and not self._results:
        #     self.process()
        sequences = sorted(results, key=lambda x: x.complexity())
        yield from sequences

    def set_result(self, manager, items, sequences):
        sequences = set(sequences)
        self._results.update(sequences)
        yield from sequences

    @classmethod
    def make_dependency(cls, callback, items, *args, **kwargs):
        return Dependency(callback=callback, items=items, args=args, kwargs=kwargs)

    def queue(self, items, priority, dependencies):
        queue = self._queue
        if not isinstance(items, Items):
            items = make_items(items)
        insert = False
        if items in self._entries:
            entry = self._entries[items]
            index = bisect.bisect_left(queue, entry)
            if index < len(queue) and queue[index].items.equals(entry.items):
                del queue[index]
                insert = True
            dependencies = entry.dependencies + list(dependencies)
            entry = entry._replace(priority=min(entry.priority, priority), dependencies=dependencies)
        else:
            entry = Entry(
                priority=priority,
                items=items,
                dependencies=dependencies,
            )
            insert = True
        if insert:
            bisect.insort_left(queue, entry)
        self._entries[items] = entry

        self._queued_items.add(entry.items)

    # def process(self):
    #     queue = self._queue
    #     while queue:
    #         entry = queue.pop(0)
    #         priority = entry.priority
    #         items = entry.items
    #         for algorithm in self.algorithms:
    #             sequences = set(algorithm(self, items, priority))
    #             if sequences:
    #                 self.set_found(priority, items, sequences)
    #         self._queued_items.discard(entry.items)
    #         break

    def set_found(self, priority, items, sequences):
        managed = set()
        found_res = {items: sequences}
        while found_res:
            new_found_res = collections.defaultdict(set)
            for items, sequences in found_res.items():
                if not isinstance(items, Items):
                    items = make_items(items)
                idict = collections.defaultdict(set)
                for sequence in sequences:
                    values = tuple(sequence.get_values(self.size))
                    idict[values].add(sequence)
                for i_items, i_sequences in idict.items():
                    self.catalog.register(*i_sequences, items=i_items)
                entry = self._entries.get(items, None)
                if entry is not None:
                    for dependency in entry.dependencies:
                        dep_sequences = set(dependency.callback(self, dependency.items, sequences, *dependency.args, **dependency.kwargs))
                        if dep_sequences and dependency.items not in managed:
                            new_found_res[dependency.items].update(dep_sequences)
                            managed.add(dependency.items)
            found_res = new_found_res
