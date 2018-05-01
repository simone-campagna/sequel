#import functools

import abc
import re

import gmpy2

from .utils import is_integer

__all__ = [
    "Item",
    "Value",
    "ANY",
    "Any",
    "Range",
    "make_item",
    "simplify_item",
]


class Item(abc.ABC):
    @abc.abstractmethod
    def __eq__(self, value):
        raise NotImplementedError()

    def _req__(self, value):
        return self == value

    def __ne__(self, value):
        return not self.__eq__(value)

    @abc.abstractmethod
    def as_string(self):
        raise NotImplementedError()

    @classmethod
    def _srepr(cls, value):
        if isinstance(value, Item):
            return value.as_string()
        return str(value)

    def equals(self, other):
        return type(self) == type(other)

    @property
    def size(self):
        return None

    def iter_values(self):
        raise ValueError("infinite size")


class Any(Item):
    __singleton__ = None

    def __new__(cls):
        if cls.__singleton__ is None:
            cls.__singleton__ = super().__new__(cls)
        return cls.__singleton__

    def __eq__(self, value):
        if isinstance(value, Item):
            return self.equals(value)
        else:
            return True

    def __repr__(self):
        return "{}()".format(type(self).__name__)

    def __str__(self):
        return "ANY"

    def as_string(self):
        return "%"

    def __hash__(self):
        return hash("ANY")

    def equals(self, other):
        return self is other


ANY = Any()


class Value(Item):
    def __init__(self, value):
        self._value = gmpy2.mpz(value)

    @property
    def value(self):
        return self._value

    def __eq__(self, value):
        if isinstance(value, Item):
            return self.equals(value)
        else:
            return self._value == value

    def as_string(self):
        return str(int(self._value))

    def __repr__(self):
        return "{}({})".format(type(self).__name__, int(self._value))

    def equals(self, other):
        if super().equals(other):
            return self._value == other._value
        return False

    @property
    def size(self):
        return 1

    def iter_values(self):
        yield self._value


class Range(Item):
    def __init__(self, min_value, max_value):
        self._min_value = gmpy2.mpz(min_value)
        self._max_value = gmpy2.mpz(max_value)
        self._size = max_value + 1 - min_value

    def __contains__(self, value):
        return self._min_value <= value <= self._max_value

    @property
    def min_value(self):
        return self._min_value

    @property
    def max_value(self):
        return self._max_value

    def __eq__(self, value):
        if isinstance(value, Item):
            return self.equals(value)
        else:
            return self._min_value <= value <= self._max_value

    def __repr__(self):
        return "{}({}, {})".format(
            type(self).__name__,
            self._min_value,
            self._max_value)

    def as_string(self):
        return "{}..{}".format(self._srepr(self._min_value), self._srepr(self._max_value))

    def __hash__(self):
        return hash(self._min_value) + hash(self._max_value)

    def equals(self, other):
        if super().equals(other):
            return self._min_value == other._min_value and self._max_value == other._max_value
        return False

    @property
    def size(self):
        return self._size

    def iter_values(self):
        yield from range(self._min_value, self._max_value + 1)


class Set(Item):
    def __init__(self, *values):
        self._values = frozenset(gmpy2.mpz(value) for value in values)

    def __hash__(self):
        return hash(self._values)

    def __contains__(self, value):
        assert value in self._values

    def __eq__(self, value):
        if isinstance(value, Item):
            return self.equals(value)
        else:
            return value in self._values

    def __repr__(self):
        return "{}({})".format(
            type(self).__name__,
            ", ".join(self._srepr(x) for x in self._values))

    def as_string(self):
        return ",".join(self._srepr(value) for value in self._values)

    def equals(self, other):
        if super().equals(other):
            return self._values == other._values
        return False

    @property
    def size(self):
        return len(self._values)

    def iter_values(self):
        yield from self._values


def simplify_item(x):
    if isinstance(x, Item) and x.size == 1:
        return next(x.iter_values())
    else:
        return x


def make_item(x, simplify=True):
    if isinstance(x, Item):
        if simplify:
            return simplify_item(x)
        else:
            return x
    elif is_integer(x):
        if simplify:
            return int(x)
        else:
            return Value(int(x))
    elif isinstance(x, str):
        if x == '%':
            return ANY
        rw = re.compile(r'\D')
        m = rw.search(x)
        if m:
            c = m.group()
            if c.isalpha():
                value = eval(x, {
                    'ANY': ANY,
                    'Any': Any,
                    'Range': Range,
                    'Set': Set,
                    'Value': Value,
                })
                if isinstance(value, Item):
                    if simplify and value.size == 1:
                        return next(value.iter_values())
                    else:
                        return value
                elif is_integer(value):
                    return value
                else:
                    raise ValueError(x)
            elif c == ',':
                lst = []
                for t in x.split(','):
                    lst.append(int(t.strip()))
                if simplify and len(lst) == 1:
                    return lst[0]
                else:
                    return Set(*lst)
            elif '..' in x:
                lst = x.split('..', 1)
                mn = int(lst[0])
                mx = int(lst[1])
                if simplify and mn == mx:
                    return mn
                else:
                    return Range(mn, mx)
        if simplify:
            return int(x)
        else:
            return Value(int(x))
    else:
        raise TypeError("{!r}: not a valid Item".format(x))
