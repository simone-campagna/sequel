"""
Search mul/div/pow sequences
"""

import itertools

from ..item import ANY, Interval
from ..items import make_items
from ..utils import (
    factorize, gcd, divisors,
    assert_sequence_matches, sequence_matches,
    perfect_power,
)

from .base import RecursiveAlgorithm



__all__ = [
    "AddAlgorithm",
    "SubAlgorithm",
    "MulAlgorithm",
    "DivAlgorithm",
    "PowAlgorithm",
    "ConstPowAlgorithm",
]


class AddAlgorithm(RecursiveAlgorithm):
    """Search for s1 = lseq + rseq"""

    def rank_increase(self, rank):
        return rank + 1

    def sub_search(self, manager, items, rank):
        catalog = manager.catalog
        # try to find lseq matching [items // rseq]
        for r_sequences, r_values in catalog.iter_sequences_values():
            sub_items = [item - r_value for item, r_value in zip(items, r_values)]
            self.sub_queue(
                manager, rank, items, sub_items, self._found_left,
                {'r_sequences': r_sequences})

    def _found_left(self, manager, items, sequences, r_sequences):
        for l_sequence in sequences:
            for r_sequence in r_sequences:
                sequence = l_sequence + r_sequence
                assert_sequence_matches(sequence, items)
                yield sequence


class SubAlgorithm(RecursiveAlgorithm):
    """Search for s1 = lseq - rseq"""

    def rank_increase(self, rank):
        return rank + 1

    def sub_search(self, manager, items, rank):
        catalog = manager.catalog
        # try to find lseq matching [items // rseq]
        for r_sequences, r_values in catalog.iter_sequences_values():
            sub_items = [item + r_value for item, r_value in zip(items, r_values)]
            self.sub_queue(
                manager, rank, items, sub_items, self._found_left,
                {'r_sequences': r_sequences})

    def _found_left(self, manager, items, sequences, r_sequences):
        for l_sequence in sequences:
            for r_sequence in r_sequences:
                sequence = l_sequence - r_sequence
                assert_sequence_matches(sequence, items)
                yield sequence


class MulAlgorithm(RecursiveAlgorithm):
    """Search for s1 = lseq * rseq"""

    def rank_increase(self, rank):
        return rank + 1

    def sub_search(self, manager, items, rank):
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
                self.sub_queue(
                    manager, rank, items, sub_items, self._found_left,
                    {'r_sequences': r_sequences})

    def _found_left(self, manager, items, sequences, r_sequences):
        for l_sequence in sequences:
            for r_sequence in r_sequences:
                sequence = l_sequence * r_sequence
                assert_sequence_matches(sequence, items)
                yield sequence


class DivAlgorithm(RecursiveAlgorithm):
    """Search for s1 = lseq // rseq"""

    def rank_increase(self, rank):
        return rank + 1

    def sub_search(self, manager, items, rank):
        catalog = manager.catalog
        # try to find lseq matching [items * rseq]
        for r_sequences, r_values in catalog.iter_sequences_values():
            sub_items = []
            for item, r_value in zip(items, r_values):
                if r_value == 0:
                    break
                else:
                    vl = item * r_value
                    vr = vl + r_value - 1
                    if vr == vl:
                        vv = vr
                    else:
                        vv = Interval(vl, vr)
                    sub_items.append(vv)
            else:
                # ok
                self.sub_queue(
                    manager, rank, items, sub_items, self._found_left,
                    {'r_sequences': r_sequences})

    def _found_left(self, manager, items, sequences, r_sequences):
        for l_sequence in sequences:
            for r_sequence in r_sequences:
                sequence = l_sequence // r_sequence
                if sequence_matches(sequence, items):
                    yield sequence


class PowAlgorithm(RecursiveAlgorithm):
    """Search for s1 ** s2"""

    __init_keys__ = ["max_value"]

    def rank_increase(self, rank):
        return rank + 1

    def __init__(self, max_value=2**50):
        self.max_value = abs(max_value)

    def sub_search(self, manager, items, rank):
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

        for res in itertools.product(*ires):
            left_items = [x[0] for x in res]
            right_items = [x[1] for x in res]
            self.sub_queue(
                manager, rank + 1, items, left_items, self._found_left,
                {'rank': rank, 'orig_items': items, 'right_items': right_items})

    def _found_left(self, manager, items, sequences, rank, orig_items, right_items):
        yield from ()
        left_sequences = set(sequences)
        self.sub_queue(
            manager, rank, items, right_items, self._found_right,
            {'rank': rank, 'orig_items': orig_items, 'left_sequences': left_sequences})

    def _found_right(self, manager, items, sequences, rank, orig_items, left_sequences):
        for l_sequence in left_sequences:
            for r_sequence in sequences:
                sequence = l_sequence ** r_sequence
                if sequence_matches(sequence, orig_items):
                    yield sequence


class ConstPowAlgorithm(RecursiveAlgorithm):
    """Search for s1 ** C"""

    __init_keys__ = ["max_value"]

    def rank_increase(self, rank):
        return rank + 1

    def __init__(self, max_value=2**50):
        self.max_value = abs(max_value)

    def sub_search(self, manager, items, rank):
        cur_gcd = None
        p_items = []
        for item in items:
            ppower = perfect_power(item)
            if ppower is False:
                return
            root, power = ppower
            if cur_gcd is None:
                cur_gcd = power
            else:
                cur_gcd = gcd(cur_gcd, power)
            if cur_gcd <= 1:
                return
            p_items.append(ppower)
        for divisor in reversed(list(divisors(cur_gcd))):
            if divisor > 1:
                sub_items = []
                for root, power in p_items:
                    sub_items.append(root ** (power // divisor))
                self.sub_queue(
                    manager, rank, items, sub_items, self._found_left,
                    {'power': divisor})
        #for p_value, p_power in factorize(cur_gcd):
        return

    def _found_left(self, manager, items, sequences, power):
        for l_sequence in sequences:
            sequence = l_sequence ** power
            assert_sequence_matches(sequence, items)
            yield sequence
