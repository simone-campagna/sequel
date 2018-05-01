"""
Search mul/div/pow sequences
"""

import itertools

from ..item import ANY, Range
from ..items import make_items
from ..utils import (
    factorize, gcd, divisors,
    assert_sequence_matches, sequence_matches,
)

from .base import SearchAlgorithm



__all__ = [
    "SearchMul",
    "SearchDiv",
    "SearchPow",
]


class SearchMul(SearchAlgorithm):
    """Search for s1 = lseq * rseq"""

    def iter_sequences(self, manager, items, priority):
        yield from ()
        catalog = manager.catalog
        # try to find lseq matching [items // rseq]
        for r_sequences, r_values in catalog.iter_sequences_values():
            sub_items = []
            for item, r_value in zip(items, r_values):
                if r_value == 0:
                    if item == 0:
                        sub_items.append(ANY)
                    elif item != 0:
                        break
                else:
                    div, mod = divmod(item, r_value)
                    if mod == 0:
                        sub_items.append(div)
                    else:
                        break
            else:
                # ok
                dependency = manager.make_dependency(
                    callback=self._found_left,
                    items=items,
                    r_sequences=r_sequences)
                manager.queue(sub_items, priority=priority + 1, dependencies=[dependency])

    def _found_left(self, manager, items, sequences, r_sequences):
        for l_sequence in sequences:
            for r_sequence in r_sequences:
                sequence = l_sequence * r_sequence
                assert_sequence_matches(sequence, items)
                yield sequence


class SearchDiv(SearchAlgorithm):
    """Search for s1 = lseq // rseq"""

    def iter_sequences(self, manager, items, priority):
        yield from ()
        catalog = manager.catalog
        # try to find lseq matching [items * rseq]
        for r_sequences, r_values in catalog.iter_sequences_values():
            sub_items = []
            for item, r_value in zip(items, r_values):
                if r_value == 0:
                    break
                else:
                    if item == 0:
                        sub_items.append(0)
                    else:
                        vv = item * r_value
                        sub_items.append(Range(vv, vv + r_value - 1))
            else:
                # ok
                dependency = manager.make_dependency(
                    callback=self._found_left,
                    items=items,
                    r_sequences=r_sequences)
                manager.queue(sub_items, priority=priority + 2, dependencies=[dependency])

    def _found_left(self, manager, items, sequences, r_sequences):
        for l_sequence in sequences:
            for r_sequence in r_sequences:
                sequence = l_sequence // r_sequence
                if sequence_matches(sequence, items):
                    yield sequence


class SearchPow(SearchAlgorithm):
    """Search for s1 ** s2"""
    def __init__(self, max_value=2**50):
        self.max_value = abs(max_value)

    def iter_sequences(self, manager, items, priority):
        yield from ()
        if 0 in items:
            return
        itx = list(enumerate(items))
        itx.sort(key=lambda x: abs(x[1]))
        ires = [[(ANY, ANY)] for _ in itx]
        found = 0
        for index, item in itx:
            abs_item = abs(item)
            if abs_item > self.max_value:
                break
            res_list = []
            if abs_item == 1:
                res_list.append((ANY, 0))
            else:
                found += 1
                fact = list(factorize(abs_item))
                power = gcd(*[m for p, m in fact])
                root = 1
                for p, m in fact:
                    root *= p ** (m // power)
                for xd in divisors(power):
                    if power > 1 and xd == power:
                        continue
                    mpower = power // xd
                    if item > 0 or mpower % 2 != 0:
                        res_list.append((root ** xd, power // xd))
            ires[index] = res_list
        if found < self.__min_items__:
            return

        # print(ires)
        # for i, x in enumerate(ires):
        #     print("***", i, x)
        # input("...")
        sub_priority = priority + 3
        for res in itertools.product(*ires):
            left_items = [x[0] for x in res]
            right_items = [x[1] for x in res]
            dependency = manager.make_dependency(
                callback=self._found_left,
                items=items,
                orig_items=items,
                right_items=right_items,
                priority=sub_priority - 1)
            manager.queue(left_items, priority=sub_priority, dependencies=[dependency])

    def _found_left(self, manager, items, sequences, priority, orig_items, right_items):
        yield from ()
        left_sequences = set(sequences)
        dependency = manager.make_dependency(
            callback=self._found_right,
            items=items,
            orig_items=orig_items,
            left_sequences=left_sequences)
        manager.queue(right_items, priority=priority, dependencies=[dependency])

    def _found_right(self, manager, items, sequences, orig_items, left_sequences):
        for l_sequence in left_sequences:
            for r_sequence in sequences:
                sequence = l_sequence ** r_sequence
                if sequence_matches(sequence, orig_items):
                    yield sequence
