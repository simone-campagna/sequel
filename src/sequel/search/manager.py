"""
Search manager
"""

import abc
import bisect
import collections
import functools
import itertools
import time

from ..catalog import create_catalog
from ..items import make_items, Items

from .base import Algorithm, RecursiveAlgorithm


__all__ = [
    "Collector",
    "Handler",
    "StopAtFirst",
    "StopAtLast",
    "StopBelowComplexity",
    "Manager",
]


Dependency = collections.namedtuple(
    "Dependency", "algorithm callback items kwargs")


class Entry(collections.namedtuple("EntryNT", "rank items dependencies")):
    def __new__(cls, rank, items, dependencies=()):
        return super().__new__(cls, rank, items, list(dependencies))

    def ordering_key(self):
        return (self.rank, -len(self.dependencies))

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


class Collector(object):
    def __init__(self):
        self._entries = []

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

    def __len__(self):
        return len(self._entries)

    def __iter__(self):
        for entry in self._entries:
            yield entry.sequence

    def entries(self):
        yield from self._entries


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
        self._entries = {}
        self.algorithms = []
        self.rec_algorithms = []

    def add_algorithm(self, algorithm):
        if isinstance(algorithm, RecursiveAlgorithm):
            self.rec_algorithms.append(algorithm)
        elif isinstance(algorithm, Algorithm):
            self.algorithms.append(algorithm)
        else:
            raise TypeError("{!r}: not an Algorithm".format(algorithm))

    def search(self, items, handler=None, profiler=None):
        items = make_items(items)
        if handler is None:
            handler = StopAtFirst()
        else:
            if not isinstance(handler, Handler):
                raise TypeError("{!r} is not an Handler".format(handler))
        dependency = None
        # self.make_dependency(
        #     algorithm=None,
        #     callback=(lambda manager, items, sequences: handler.collector.add(*sequences)),
        #     items=(), kwargs={})
        self.queue(items, rank=0, dependencies=[dependency])
        queue = self._queue
        algorithms = self.algorithms
        rec_algorithms = self.rec_algorithms
        rec_stack = []
        cur_rank = 0
        timings_dict = {}
        if profiler is not None:
            for algorithm in itertools.chain(self.algorithms, self.rec_algorithms):
                timings_dict[algorithm] = profiler[type(algorithm).__name__]
        while queue:
            entry = queue.pop(0)
            rank = entry.rank
            items = entry.items
            for algorithm in self.algorithms:
                algorithm_sequences = algorithm(self, items, rank)
                num_found = 0
                while True:
                    if timings_dict:
                        t0 = time.time()
                    try:
                        sequence = next(algorithm_sequences)
                    except StopIteration:
                        break
                    finally:
                        if timings_dict:
                            timings_dict[algorithm].add_timing(time.time() - t0)
                    for sequence in self._set_found(items, rank, [sequence], timings_dict):
                        yield sequence
                        handler.collector.add(sequence)
                        if handler:
                            return
                rec_stack.append(entry)
            rec_rank = cur_rank
            while rec_stack and ((not queue) or (rec_stack and rank > rec_rank)):
                entry = rec_stack.pop()
                rec_rank = entry.rank
                for rec_algorithm in rec_algorithms:
                    if timings_dict:
                        t0 = time.time()
                    for dummy in rec_algorithm(self, items, rank):
                        pass
                    if timings_dict:
                        timings_dict[rec_algorithm].add_timing(time.time() - t0)
                    if handler:
                        break
            cur_rank = rank

    @classmethod
    def make_dependency(cls, algorithm, callback, items, kwargs):
        return Dependency(algorithm=algorithm, callback=callback, items=items, kwargs=kwargs)

    def queue(self, items, rank, dependencies):
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
            entry = entry._replace(rank=min(entry.rank, rank), dependencies=dependencies)
        else:
            entry = Entry(
                rank=rank,
                items=items,
                dependencies=dependencies,
            )
            insert = True
        if insert:
            bisect.insort_left(queue, entry)
        self._entries[items] = entry

    def _set_found(self, items, rank, sequences, timings_dict):
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
                        if dependency is None:
                            yield from sequences
                        else:
                            if timings_dict:
                                t0 = time.time()
                            dep_sequences = set(dependency.callback(self, dependency.items, sequences, **dependency.kwargs))
                            if timings_dict:
                                t0 = time.time()
                            if dep_sequences and dependency.items not in managed:
                                new_found_res[dependency.items].update(dep_sequences)
                                managed.add(dependency.items)
            found_res = new_found_res
