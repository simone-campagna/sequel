"""
Base SearchAlgorithm
"""

import abc
import collections
import copy
import time

from ..items import Items
from ..modules import load_ref, make_ref
from ..utils import sequence_matches
from ..item import Item

__all__ = [
    "Serialization",
    "SearchInfo",
    "SearchOptions",
    "SearchAlgorithm",
    "RecursiveSearchAlgorithm",
]


class Serialization(object):
    def __init__(self, data=None):
        if data is None:
            data = {}
        self._data = data
        self._instances = collections.defaultdict(dict)

    def data(self):
        return self._data

    def load(self, instance_name):
        dct = self._data[instance_name]
        instance_class = load_ref(dct["type"])
        iset = self._instances[instance_class]
        if instance_name in iset:
            instance = iset[instance_name]
        else:
            instance, initializers = instance_class.from_dict(copy.deepcopy(dct["kwargs"]), self)
            iset[instance_name] = instance
            for initializer in initializers:
                initializer(instance)
        return instance

    def store(self, instance):
        cls = type(instance)
        iset = self._instances[cls]
        if instance in iset:
            return iset[instance]
        else:
            name = instance.name
            iset[instance] = name
            self._data[name] = {
                "type": make_ref(cls),
                "kwargs": copy.deepcopy(instance.to_dict(self)),
            }
            return name


_SearchInfo = collections.namedtuple(
    "_SearchInfo",
    "max_depth depth max_rank rank log",
)

class SearchInfo(_SearchInfo):
    def __new__(cls, max_depth, max_rank, log=False, depth=0, rank=0):
        return super().__new__(cls, max_depth=max_depth, max_rank=max_rank, log=log, depth=depth, rank=rank)

    def sub(self, depth=1, rank=1):
        return self._replace(depth=self.depth + depth, rank=self.rank + rank)


SearchOptions = collections.namedtuple(
    "SearchOptions",
    "profiler log",
)


class SearchAlgorithm(abc.ABC):
    __registry__ = collections.defaultdict(dict)
    __serialization_keys__ = ['name']
    __min_items__ = 3
    __accepts_undefined__ = False

    def __init__(self, name=None):
        self.name = self.register(self, name)

    @classmethod
    def register(cls, instance, name=None):
        itype = type(instance)
        cls_dict = cls.__registry__[itype]
        if instance in cls_dict:
            return cls_dict[instance]
        else:
            if name is None:
                name = "{}_{}".format(itype.__name__, len(cls_dict))
            cls_dict[instance] = name
            return name

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

    def __call__(self, catalog, items, info, options):
        if not isinstance(items, Items):
            items = Items(items)
        if not items.is_fully_defined():
            if not self.accepts_undefined_items():
                # try with sub_items:
                sub_items = []
                for item in items:
                    if isinstance(item, Item):
                        break
                    sub_items.append(item)
                sub_items = Items(sub_items)
                for sequence, info in self(catalog, sub_items, info, options):
                    if sequence_matches(sequence, items):
                        yield sequence, info
                return
        accepted, reason = self.accepts(items, info, options)
        if not accepted:
            if info.log:
                print("  " * info.depth + self.name + " not accepted: " + reason)
        else:
            profiler = options.profiler
            log = options.log
            if log:
                print("  " * info.depth + self.name + " - " + " ".join(str(x) for x in items))
            if profiler is not None:
                timing = profiler[self.name]
            iterator = iter(self._impl_call(catalog, items, info, options))
            total_time = 0
            try:
                while True:
                    t0 = time.time()
                    try:
                        sequence, sequence_info = next(iterator)
                    except StopIteration:
                        break
                    t1 = time.time()
                    t_elapsed = t1 - t0
                    total_time += t_elapsed
                    if log:
                        print("  " * info.depth + self.name + "-> " + str(sequence) + " [{:.2f}s]".format(t_elapsed))
                    yield sequence, sequence_info
            finally:
                if profiler is not None:
                    timing.add_timing(total_time)

    @abc.abstractmethod
    def _impl_call(self, catalog, items, info, options):
        raise NotImplementedError()

    def search(self, catalog, items, max_depth=10, max_rank=10, log=False, profiler=None):
        if not isinstance(items, Items):
            items = Items(items)
        info = SearchInfo(max_depth=max_depth, max_rank=max_rank)
        options = SearchOptions(profiler=profiler, log=log)
        for sequence, info in self(catalog, items, info, options):
            yield sequence

    def name(self):
        return self.name

    def to_dict(self, serialization):
        return {key: getattr(self, key) for key in self.__serialization_keys__}

    @classmethod
    def from_dict(cls, dct, serialization):
        return cls(**dct), []

    def __repr__(self):
        return "{}({})".format(
            type(self).__name__,
            ", ".join("{}={!r}".format(key, getattr(self, key)) for key in self.__serialization_keys__))


class RecursiveSearchAlgorithm(SearchAlgorithm):
    __serialization_keys__ = SearchAlgorithm.__serialization_keys__ + ['sub_algorithm']

    def __init__(self, sub_algorithm, name=None):
        super().__init__(name=name)
        self.sub_algorithm = sub_algorithm

    def to_dict(self, serialization):
        dct = super().to_dict(serialization)
        dct['sub_algorithm'] = serialization.store(dct['sub_algorithm'])
        return dct

    def _set_sub_algorithm(self, sub_algorithm):
        self.sub_algorithm = sub_algorithm

    @classmethod
    def from_dict(cls, dct, serialization):
        sub_algorithm_name = dct["sub_algorithm"]
        dct['sub_algorithm'] = None
        instance, initializers = super().from_dict(dct, serialization)
        instance.sub_algorithm = serialization.load(sub_algorithm_name)
        initializers += [lambda x: x._set_sub_algorithm(serialization.load(sub_algorithm_name))]
        return instance, initializers

    def sub_search(self, catalog, items, info, options):
        yield from self.sub_algorithm(catalog, items, info, options)
        # found_sequences = set()
        # for sub_sequence, sub_info in self.sub_algorithm(catalog, items, info, options):
        #     yield sub_sequence, sub_info
        #     found_sequences.add(sub_sequence)
        # for sequence in found_sequences:
        #     catalog.register(sequence)
