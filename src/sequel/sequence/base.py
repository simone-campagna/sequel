"""
Abstract Sequence
"""

import abc
import ast
import astor
import collections
import contextlib
import functools
import inspect
import itertools
import uuid
import weakref

import gmpy2
import sympy

from ..item import Any, ANY, Range, Set, Value
from ..utils import is_integer
from . import sympy_classes
from .trait import Trait


__all__ = [
    'Sequence',
    'compile_sequence',
    'StashMixin',
    'EnumeratedSequence',
    'Iterator',
    'Function',
    'StashedFunction',
    'Integer',
    'Natural',
    'NegInteger',
    'NegNatural',
    'Const',
    'Compose',
]



class SequenceError(Exception):
    pass


class SequenceUnknownValueError(SequenceError):
    pass


class SMeta(abc.ABCMeta):
    def __new__(mcls, class_name, class_bases, class_dict):
        params = []
        class_dict['__params__'] = params
        class_dict['__signature__'] = None
        cls = super().__new__(mcls, class_name, class_bases, class_dict)
        init_method = getattr(cls, '__init__')
        sig = inspect.signature(init_method)
        cls.__signature__ = sig
        return cls


class Sequence(metaclass=SMeta):
    __instances__ = weakref.WeakValueDictionary()
    __registry__ = collections.OrderedDict()
    __traits__ = ()
    __ignored_errors__ = (ArithmeticError, OverflowError, ValueError, IndexError, SequenceUnknownValueError)

    def __new__(cls, *args, **kwargs):
        bound_args = cls.__signature__.bind(None, *args, **kwargs)
        bound_args.apply_defaults()
        parameters = (cls,) + tuple(bound_args.arguments.items())[1:]
        if parameters in cls.__instances__:
            return cls.__instances__[parameters]
        else:
            instance = super().__new__(cls)
            instance._instance_parameters = parameters
            instance._instance_traits = frozenset(cls.__traits__)
            instance._instance_symbol = None
            instance._instance_expr = None
            cls.__instances__[parameters] = instance
            return instance

    def __init__(self):
        # WARNING: this empty __init__method is needed in order to correctly
        #          inspect default arguments in __new__
        pass

    def as_string(self):
        if self._instance_symbol is None:
            return self._str_impl()
        return self._instance_symbol

    def _str_impl(self):
        return repr(self)

    def _make_expr(self):
        if self._instance_symbol:
            return sympy.symbols(self._instance_symbol, integer=True)

    @property
    def expr(self):
        if self._instance_expr is None:
            self._instance_expr = self._make_expr()
        return self._instance_expr

    @property
    def traits(self):
        return self._instance_traits

    def register(self, name, *traits):
        for trait in traits:
            if not isinstance(trait, Trait):
                raise TypeError("{!r} is not a Trait".format(trait))
        self._instance_traits |= frozenset(traits)
        if name is not None:
            self._instance_symbol = name
            self.__registry__[name] = self
        return self

    @abc.abstractmethod
    def __iter__(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def __call__(self, i):
        raise NotImplementedError()

    def __getitem__(self, i):
        return self(i)

    def description(self):
        """Returns the sequence description"""
        return repr(self)
        lst = [self.__class__.__name__]
        doc = self.doc()
        if doc:
            lst.append(" - ")
            lst.append(doc)
        return "".join(lst)

    @classmethod
    def get_registry(cls):
        return cls.__registry__

    def has_traits(self, *traits):
        traits = set(traits)
        return traits == traits.intersection(self.traits)

    def __pos__(self):
        return self

    def __neg__(self):
        return Neg(self)

    def __pos__(self):
        return Pos(self)

    def __abs__(self):
        return Abs(self)

    def __add__(self, other):
        return Add(self, other)

    def __radd__(self, other):
        return Add(other, self)

    def __sub__(self, other):
        return Sub(self, other)

    def __rsub__(self, other):
        return Sub(other, self)

    def __mul__(self, other):
        return Mul(self, other)

    def __rmul__(self, other):
        return Mul(other, self)

    def __floordiv__(self, other):
        return Div(self, other)

    def __rfloordiv__(self, other):
        return Div(other, self)

    def __truediv__(self, other):
        return Div(self, other)

    def __rtruediv__(self, other):
        return Div(other, self)

    def __mod__(self, other):
        return Mod(self, other)

    def __rmod__(self, other):
        return Mod(other, self)

    def __pow__(self, other):
        return Pow(self, other)

    def __rpow__(self, other):
        return Pow(other, self)

    def __or__(self, other):
        return Compose(self, other)

    def __ror__(self, other):
        return Compose(other, self)

    @classmethod
    def sequence_types(cls, abstract=False):
        """Yields all the sequence types.
    
           Parameters
           ----------
           abstract: bool, optional
               if True yields also abstract sequence types
               (defaults to False)
    
           Yields
           ------
           type
               Sequence types
        """
        sequence_type_list = [cls]
        while sequence_type_list:
            new_list = []
            for sequence_type in sequence_type_list:
                if abstract or not inspect.isabstract(sequence_type):
                    yield sequence_type
                for subtype in sequence_type.__subclasses__():
                    new_list.append(subtype)
            sequence_type_list = new_list
    
    @classmethod
    def compile(cls, source, simplify=False):
        """Compile sequence from source.
    
           Parameters
           ----------
           source: str
               Sequence source
           simplify: bool, optional
               Simplify sequence (defaults to False)
    
           Returns
           -------
           Sequence
               The compiled Sequence.
        """
        g_dict = {
            "ANY": ANY,
            "Any": Any,
            "Range": Range,
            "Set": Set,
            "Value": Value,
        }
        for sequence_type in Sequence.sequence_types():
            g_dict[sequence_type.__name__] = sequence_type
        g_dict.update(Sequence.__registry__)
        sequence = eval(source, g_dict, {})
        if isinstance(sequence, int):
            sequence = Const(value=sequence)
        elif isinstance(sequence, float):
            sequence = Const(value=int(sequence))
        elif not isinstance(sequence, Sequence):
            raise TypeError("{!r} is not a Sequence".format(sequence))
        if simplify:
            sequence = sequence.simplify()
        return sequence

    def __repr__(self):
        return "{}({})".format(
            type(self).__name__,
            ", ".join("{}={!r}".format(key, val) for key, val in self._instance_parameters[1:]))

    @classmethod
    def from_expr(cls, expr):
        return cls.compile(str(expr))
        
    def simplify(self):
        expr = self.expr
        if expr is not None:
            s_expr = sympy.simplify(expr)
            try:
                return self.from_expr(s_expr)
            except NameError:
                try:
                    return self.from_expr(expr)
                except NameError:
                    return self
        else:
            return self

    def __str__(self):
        return astor.to_source(
            ast.parse(self.as_string()),
            pretty_source=lambda s: "".join(s)).strip()

    @classmethod
    def make_sequence(cls, operand):
        if isinstance(operand, Sequence):
            return operand
        elif is_integer(operand):
            return Const(value=operand)
        elif isinstance(operand, float):
            return Const(value=int(operand))
        elif isinstance(operand, str):
            return Sequence.compile(operand)
        else:
            raise TypeError("{!r} is not a Sequence".format(operand))

    def children(self):
        yield from ()

    def equals(self, other):
        if not isinstance(other, Sequence):
            return False
        s_expr = self.expr
        o_expr = other.expr
        if s_expr is not None and o_expr is not None:
            with contextlib.suppress(Exception):
                return s_expr.equals(o_expr)
        if type(self) != type(other):
            return False
        for schild, ochild in itertools.zip_longest(self.children(), other.children(), fillvalue=None):
            if schild is None or not schild.equals(ochild):
                return False
        return True

    def walk(self, include_self=True, depth=0):
        if include_self:
            yield depth, self
        for child in self.children():
            yield from child.walk(include_self=True, depth=depth + 1)

    def complexity(self):
        return len(tuple(self.walk(include_self=True)))

    def get_values(self, num, *, start=0):
        lst = []
        if start == 0:
            try:
                for value, _ in zip(self, range(num)):
                    lst.append(value)
            except self.__ignored_errors__:
                pass
        else:
            try:
                for i in range(start, start + num):
                    lst.append(self[i])
            except self.__ignored_errors__:
                pass
        return tuple(lst)


def compile_sequence(source):
    return Sequence.compile(source)


class StashMixin(object):
    __stash__ = None

    def __getitem__(self, i):
        if 0 <= i < len(self.__stash__):
            return self.__stash__[i]
        else:
            return super().__getitem__(i)

    def __iter__(self):
        yield from self.__stash__
        for i in itertools.count(start=len(self.__stash__)):
            yield self(i)


class EnumeratedSequence(StashMixin, Sequence):

    def __call__(self, i):
        raise SequenceUnknownValueError("{}[{}]".format(self, i))

    def get_values(self, num, *, start=0):
        return self.__stash__[start:start + num]


class Iterator(Sequence):
    """Iterator sequence"""

    @functools.lru_cache(maxsize=1024)
    def __call__(self, i):
        if i < 0:
            raise IndexError(i)
        it = iter(self)
        for _ in range(i):
            next(it)
        return next(it)


class Function(Sequence):
    """Function sequence"""

    def __iter__(self):
        i = 0
        while True:
            yield self[i]
            i += 1


class StashedFunction(StashMixin, Function):
    pass


class UnOp(Sequence):
    """Unary operator"""
    __operator__ = "?"

    def __init__(self, operand):
        self.operand = self.make_sequence(operand)

    @classmethod
    @abc.abstractmethod
    def _unop(cls, value):
        raise NotImplementedError()

    def _make_expr(self):
        expr = self.operand.expr
        if expr is not None:
            return self._unop(expr)

    def __call__(self, i):
        return gmpy2.mpz(self._unop(self.operand[i]))

    def __iter__(self):
        for value in self.operand:
            yield self._unop(value)

    def _str_impl(self):
        return "{}({})".format(self.__operator__, self.operand.as_string())

    def children(self):
        yield self.operand


class Neg(UnOp):
    __operator__ = "-"

    @classmethod
    def _unop(cls, value):
        return -value


class Pos(UnOp):
    __operator__ = "+"

    @classmethod
    def _unop(cls, value):
        return +value


class Abs(UnOp):
    __operator__ = "abs"

    @classmethod
    def _unop(cls, value):
        return abs(value)


class BinOp(Sequence):
    """Binary operator"""
    __operator__ = '?'

    def __init__(self, left, right):
        self.left = self.make_sequence(left)
        self.right = self.make_sequence(right)

    @classmethod
    @abc.abstractmethod
    def _binop(cls, l, r):
        raise NotImplementedError()

    def __call__(self, i):
        return gmpy2.mpz(self._binop(self.left[i], self.right[i]))

    def __iter__(self):
        for l, r in zip(self.left, self.right):
            yield self._binop(l, r)

    def _str_impl(self):
        return "({}) {} ({})".format(self.left.as_string(), self.__operator__, self.right.as_string())

    def _make_expr(self):
        l_expr = self.left.expr
        r_expr = self.right.expr
        if l_expr is not None and r_expr is not None:
            expr = self._binop(l_expr, r_expr)
            return expr

    def children(self):
        yield from (self.left, self.right)


class Add(BinOp):
    __operator__ = '+'

    @classmethod
    def _binop(cls, l, r):
        return l + r


class Sub(BinOp):
    __operator__ = '-'

    @classmethod
    def _binop(cls, l, r):
        return l - r


class Mul(BinOp):
    __operator__ = '*'

    @classmethod
    def _binop(cls, l, r):
        return l * r


class Div(BinOp):
    __operator__ = '//'

    @classmethod
    def _binop(cls, l, r):
        return l // r

    # def _make_expr(self):
    #     l_expr = self.left.expr
    #     r_expr = self.right.expr
    #     if l_expr is not None and r_expr is not None:
    #         return l_expr / r_expr

class Mod(BinOp):
    __operator__ = '%'

    @classmethod
    def _binop(cls, l, r):
        return l % r


class Pow(BinOp):
    __operator__ = '**'

    @classmethod
    def _binop(cls, l, r):
        return l ** r


class Compose(Sequence):
    def __init__(self, sequence, operand):
        self.sequence = self.make_sequence(sequence)
        self.operand = self.make_sequence(operand)

    def __call__(self, i):
        return self.sequence[self.operand[i]]

    def __iter__(self):
        for i in self.operand:
            yield self.sequence[i]

    def children(self):
        yield from (self.sequence, self.operand)

    def _str_impl(self):
        return "({}) | ({})".format(self.sequence.as_string(), self.operand.as_string())

    def simplify(self):
        sequence = self.sequence.simplify()
        operand = self.operand.simplify()
        if isinstance(sequence, Integer):
            return operand
        if isinstance(sequence, Const):
            return sequence
        elif isinstance(operand, Integer):
            return sequence
        elif isinstance(operand, Const):
            return Const(sequence[operand.value])
        else:
            return self.__class__(sequence, operand)


class Integer(Function):
    __traits__ = frozenset([Trait.POSITIVE])

    def __call__(self, i):
        return i

    def description(self):
        return """f(i) := i"""


class Natural(Function):
    __traits__ = frozenset([Trait.POSITIVE])

    def __call__(self, i):
        return i + 1

    def description(self):
        return """f(i) := i + 1"""


class NegInteger(Function):
    __traits__ = frozenset([Trait.POSITIVE])

    def __call__(self, i):
        return -i

    def description(self):
        return """f(i) := -i"""


class NegNatural(Function):
    __traits__ = frozenset([Trait.POSITIVE])

    def __call__(self, i):
        return -(i + 1)

    def description(self):
        return """f(i) := -(i + 1)"""


class Const(Function):
    def __init__(self, value):
        self.__value = value

    @property
    def value(self):
        return self.__value

    def _make_expr(self):
        return sympy.sympify(self.__value)

    def __call__(self, i):
        return self.__value

    def description(self):
        return """f(i) := {}""".format(self.__value)

    def _str_impl(self):
        return str(self.__value)

Integer().register('i', Trait.INJECTIVE, Trait.POSITIVE)
Natural().register('n', Trait.INJECTIVE, Trait.POSITIVE, Trait.NON_ZERO)
# NegInteger().register('neg_i', Trait.INJECTIVE, Trait.NEGATIVE)
# NegNatural().register('neg_n', Trait.INJECTIVE, Trait.NEGATIVE, Trait.NON_ZERO)
