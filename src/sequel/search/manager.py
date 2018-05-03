"""
Search manager
"""

import abc
import bisect
import collections
import functools
import itertools

from ..catalog import create_catalog
from ..items import make_items, Items

from .base import SearchAlgorithm


__all__ = [
    "Collector",
    "Handler",
    "StopAtFirst",
    "StopAtLast",
    "StopBelowComplexity",
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


@functools.total_ordering
class CollectorEntry(object):
    def __init__(self, sequence, complexity=None):
        if complexity is None:
            complexity = sequence.complexity()
        self.sequence = sequence
        self.complexity = complexity

    def __lt__(self, other):
        return self.complexity < other.complexity

    # def __eq__(self, other):
    #     return self.complexity == other.complexity


class Collector(object):
    def __init__(self):
        self._entries = []
        self._partials = []

    def first_entry(self):
        if self._entries:
            return self._entries[0]

    def add(self, *sequences):
        for sequence in sequences:
            sequence = sequence.simplify()
            item = CollectorEntry(sequence)
            index = bisect.bisect_left(self._entries, item)
            if index >= len(self._entries) or not sequence.equals(self._entries[index].sequence):
                self._entries.insert(index, item)
                yield sequence
                self._partials.append(item)

    def __len__(self):
        return len(self._entries)

    def __iter__(self):
        for entry in self._entries:
            yield entry.sequence

    def entries(self):
        yield from self._entries

    def partials(self):
        partials = self._partials
        if partials:
            # partials.sort(key=lambda x: x.complexity)
            for entry in partials:
                yield entry.sequence
            partials.clear()


class Handler(abc.ABC):
    def __init__(self):
        self.collector = Collector()

    @abc.abstractmethod
    def __bool__(self):
        raise NotImplementedError()

                
class StopAtFirst(Handler):
    def __bool__(self):
        return bool(self.collector)


class StopAtLast(Handler):
    def __bool__(self):
        return False


class StopBelowComplexity(Handler):
    def __init__(self, complexity=10):
        self.complexity = complexity
        super().__init__()

    def __bool__(self):
        entry = self.collector.first_entry()
        return entry is not None and entry.complexity <= self.complexity


class Manager(object):
    def __init__(self, size):
        self.size = size
        self.catalog = create_catalog(size)
        self._queue = []
        self._queued_items = set()
        self._entries = {}
        self.algorithms = []

    def add_algorithm(self, algorithm):
        if not isinstance(algorithm, SearchAlgorithm):
            raise TypeError("{!r}: not a SearchAlgorithm".format(algorithm))
        self.algorithms.append(algorithm)

    def search(self, items, handler=None):
        items = make_items(items)
        if handler is None:
            handler = StopAtFirst()
        else:
            if not isinstance(handler, Handler):
                raise TypeError("{!r} is not an Handler".format(handler))
        dependency = self.make_dependency(
            callback=(lambda manager, items, sequences: handler.collector.add(*sequences)),
            items=())
        self.queue(items, priority=0, dependencies=[dependency])
        queue = self._queue
        while queue:
            entry = queue.pop(0)
            priority = entry.priority
            items = entry.items
            for algorithm in self.algorithms:
                sequences = set(algorithm(self, items, priority))
                if sequences:
                    self.set_found(priority, items, sequences)
                yield from handler.collector.partials()
                if handler:
                    break
            self._queued_items.discard(entry.items)

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
