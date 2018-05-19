"""
Search integral/derivative algorithm class
"""

import itertools
import time

from ..item import ANY, Interval
from ..items import Items
from ..utils import (
    factorize, gcd, divisors,
    assert_sequence_matches, sequence_matches,
)

from .base import RecursiveSearchAlgorithm



__all__ = [
    "SearchMul",
    "SearchDiv",
    "SearchPow",
]


class SearchMul(RecursiveSearchAlgorithm):
    """Search for s1 = lseq * rseq"""

    def _impl_call(self, catalog, items, info, options):
        # try to find lseq matching [items // rseq]
        info = info.sub(rank=1)
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
                sub_items = Items(sub_items)
                for l_sequence, sub_info in self.sub_search(catalog, sub_items, info, options):
                    for r_sequence in r_sequences:
                        sequence = l_sequence * r_sequence
                        assert_sequence_matches(sequence, items)
                        yield sequence, sub_info


class SearchDiv(RecursiveSearchAlgorithm):
    """Search for s1 = lseq // rseq"""

    def _impl_call(self, catalog, items, info, options):
        # try to find lseq matching [items * rseq]
        info = info.sub(rank=1)
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
                        sub_items.append(Interval(vv, vv + r_value - 1))
            else:
                # ok
                sub_items = Items(sub_items)
                for l_sequence, sub_info in self.sub_search(catalog, sub_items, info, options):
                    for r_sequence in r_sequences:
                        sequence = l_sequence // r_sequence
                        assert_sequence_matches(sequence, items)
                        yield sequence, sub_info


class SearchPow(RecursiveSearchAlgorithm):
    """Search for s1 ** s2"""
    def __init__(self, sub_algorithm, max_value=2**50, max_elapsed=2.0, name=None):
        super().__init__(sub_algorithm=sub_algorithm, name=name)
        self.max_value = abs(max_value)
        self.max_elapsed = max_elapsed

    def _impl_call(self, catalog, items, info, options):
        if 0 in items:
            return
        t0 = time.time()
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
                # print("POW ***", item, abs_item, fact, power)
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
        info = info.sub(rank=1)
        base_rank = info.rank
        l_base_info = info
        for res in itertools.product(*ires):
            left_items = [x[0] for x in res]
            right_items = [x[1] for x in res]
            # print("POW::: l={} r={}".format([str(x) for x in left_items], [str(x) for x in right_items]))
            # print(left_items)
            # print(right_items)
            for left_sequence, left_sequence_info in self.sub_search(catalog, left_items, l_base_info, options):
                r_base_info = info._replace(rank=left_sequence_info.rank)
                for right_sequence, right_sequence_info in self.sub_search(catalog, right_items, r_base_info, options):
                    sequence = left_sequence ** right_sequence
                    if sequence_matches(sequence, items):
                        info_list = [left_sequence_info, right_sequence_info]
                        max_depth = max(i.depth for i in info_list)
                        sequence_info = right_sequence_info._replace(depth=max_depth)
                        yield sequence, sequence_info
                    if time.time() - t0 >= self.max_elapsed:
                        return
