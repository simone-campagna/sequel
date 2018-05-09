"""
roundrobin
"""

import abc

from .base import Iterator

__all__ = [
    'roundrobin',
]


class roundrobin(Iterator):
    def __init__(self, operand, *operands):
        self.operands = [self.make_sequence(operand)]
        self.operands.extend(self.make_sequence(op) for op in operands)

    def _simplify_backup(self):
        return self.__class__(*[operand.simplify() for operand in self.operands])

    def __iter__(self):
        its = [iter(op) for op in self.operands]
        while True:
            for it in its:
                yield next(it)

    def _str_impl(self):
        return "{}({})".format(
            type(self).__name__,
            ", ".join(str(seq) for seq in self.operands))

    def children(self):
        yield from self.operands

    def __repr__(self):
        return "{}({})".format(type(self).__name__, ", ".join(str(op) for op in self.operands))
