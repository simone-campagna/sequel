"""
Functionals
"""

import abc
from itertools import chain, count, repeat

from .base import Iterator, Add, Sub, Const, Integer


__all__ = [
    'summation',
    'product',
    'derivative',
    'integral',
    'ifelse',
    'where',
    'moessner',
]


class Functional(Iterator):
    def __init__(self, operand):
        self.operand = self.make_sequence(operand)

    def len_hint(self):
        return self.operand.len_hint()

    def children(self):
        yield self.operand

    def _str_impl(self):
        return "{}({})".format(
            type(self).__name__,
            str(self.operand))

    def simplify(self):
        operand = self.operand.simplify()
        return self.__class__(operand)


class summation(Functional):
    def __iter__(self):
        value = 0
        for item in self.operand:
            value = value + item
            yield value


class product(Functional):
    def __iter__(self):
        value = 1
        for item in self.operand:
            value = value * item
            yield value


class derivative(Functional):
    def __iter__(self):
        it = iter(self.operand)
        try:
            prev = next(it)
            while True:
                item = next(it)
                yield item - prev
                prev = item
        except StopIteration:
            return

    def len_hint(self):
        l_operand = self.operand.len_hint()
        if l_operand is None:
            return None
        else:
            return max(0, l_operand - 1)

    def __call__(self, i):
        return self.operand(i + 1) - self.operand(i)

    def simplify(self):
        instance = super().simplify()
        operand = instance.operand
        if isinstance(operand, (Add, Sub)):
            l_op, r_op = operand.left, operand.right
            if isinstance(l_op, Const):
                if isinstance(r_op, Const):
                    return Const(0)
                else:
                    if isinstance(operand, Sub):
                        return self.__class__(-r_op)
                    else:
                        return self.__class__(r_op)
            elif isinstance(r_op, Const):
                return self.__class__(l_op)
        elif isinstance(operand, integral):
            return operand.operand
        return instance


class integral(Functional):
    def __init__(self, operand, start=0):
        super().__init__(operand)
        self.start = start

    def len_hint(self):
        l_operand = self.operand.len_hint()
        if l_operand is None:
            return None
        else:
            return l_operand + 1

    def __iter__(self):
        value = self.start
        yield value
        prev = value
        for item in self.operand:
            value = prev + item
            yield value
            prev = value

    def _str_impl(self):
        return "{}({}, start={})".format(
            type(self).__name__,
            str(self.operand),
            self.start)

    def equals(self, other):
        if super().equals(other):
            return self.start == other.start
        else:
            return False

    def simplify(self):
        operand = self.operand.simplify()
        if isinstance(operand, derivative):
            start = self.start - operand.operand[0]
            if start == 0:
                return operand.operand
            else:
                return start + operand.operand
        instance = self.__class__(operand, start=self.start)
        return instance


class ifelse(Functional):
    def __init__(self, condition, true_sequence, false_sequence):
        super().__init__(condition)
        self.true_sequence = self.make_sequence(true_sequence)
        self.false_sequence = self.make_sequence(false_sequence)

    def __iter__(self):
        # print(self.operand, ":::", self.true_sequence, ":::", self.false_sequence)
        for c, t, f in zip(self.operand, self.true_sequence, self.false_sequence):
            if c:
                yield t
            else:
                yield f

    def __call__(self, i):
        if self.operand(i):
            return self.true_sequence(i)
        else:
            return self.false_sequence(i)

    def children(self):
        yield from super().children()
        yield self.true_sequence
        yield self.false_sequence

    def _str_impl(self):
        return "{}({}, {}, {})".format(
            type(self).__name__,
            str(self.operand),
            str(self.true_sequence),
            str(self.false_sequence))

    def simplify(self):
        operand = self.operand.simplify()
        true_sequence = self.true_sequence.simplify()
        false_sequence = self.false_sequence.simplify()
        return self.__class__(operand, true_sequence, false_sequence)


class where(Functional):
    def __init__(self, condition, sequence=Integer()):
        super().__init__(condition)
        self.sequence = sequence

    def __iter__(self):
        for cond, value in zip(self.operand, self.sequence):
            if cond:
                yield value

    def _str_impl(self):
        return "{}({}, {})".format(
            type(self).__name__,
            str(self.operand),
            str(self.sequence))


class moessner(Functional):
    """Moessner algorithm (see https://www.youtube.com/watch?v=rGlpyFHfMgI):

moessner(1):

1   2 | 3   4 | 5   6 | 7   8 | 9  10 | ...
    ^       ^       ^       ^       ^
1       4       9       16      25
^       ^       ^       ^       ^
moessner(2):

1   2   3 | 4   5   6 | 7   8   9 |10   ...
        ^           ^           ^
1   3       7  12      19  27
    ^           ^           ^
1           8          27
^           ^           ^

Try:
    moessner(1)   -> n ** 2
    moessner(2)   -> n ** 3
    moessner(i)   -> factorial | n
"""
    def __init__(self, sequence=Const(1), start=1):
        super().__init__(sequence)
        self.start = start

    def _reduce_block(self, prev, block):
        if len(block) == 1:
            return block
        offsets = chain(prev[1:], repeat(0))
        values = block
        result = []
        result.append(block[-1])
        while len(values) > 1:
            offset = next(offsets)
            new_value = offset
            new_values = []
            for value in values[:-1]:
                new_value += value
                new_values.append(new_value)
            values = new_values
            result.append(values[-1])
        return result

    def _iter_blocks(self):
        index = self.start
        for item in self.operand:
            items = list(range(index, index + item + 1))
            yield items
            index += item + 1

    def __iter__(self):
        reduce_block = self._reduce_block
        prev = []
        for block in self._iter_blocks():
            reduced_block = reduce_block(prev, block)
            yield reduced_block[-1]
            prev = reduced_block
