"""
Functionals
"""

import abc

from .base import Iterator, Add, Sub, Const

__all__ = [
    'summation',
    'product',
    'derivative',
    'integral',
    'ifelse',
]


class Functional(Iterator):
    def __init__(self, operand):
        self.operand = self.make_sequence(operand)

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
        prev = next(it)
        while True:
            item = next(it)
            yield item - prev
            prev = item

    def simplify(self):
        instance = super().simplify()
        operand = instance.operand
        if isinstance(operand, (Add, Sub)):
            l_op, r_op = operand.left, operand.right
            if isinstance(l_op, Const):
                if isinstance(r_op, Const):
                    return Const(0)
                else:
                    if isinstance(instance, Sub):
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
        for c, t, f in zip(self.operand, self.true_sequence, self.false_sequence):
            if c:
                yield t
            else:
                yield f

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
