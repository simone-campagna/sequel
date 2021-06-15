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
import operator
import weakref

from ..item import (
    Any, ANY, Interval, Set, Value,
    LowerBound, UpperBound,
)
from ..lazy import (
    gmpy2,
    sympy,
)
from .trait import Trait


__all__ = [
    'Sequence',
    'SequenceError',
    'RecursiveSequenceError',
    'SequenceUnknownValueError',
    'SequenceUnboundError',
    'RecursiveSequence',
    'BackIndexer',
    'rseq',
    'compile_sequence',
    'StashMixin',
    'EnumeratedSequence',
    'Iterator',
    'Function',
    'StashedFunction',
    'Integer',
    'Natural',
    'Const',
    'Compose',
]


_NUM_INDEXERS = 10


def idem(x):
    return x


class SequenceError(Exception):
    pass


class SequenceUnknownValueError(SequenceError):
    pass


class SequenceUnboundError(SequenceError):
    pass


class RecursiveSequenceError(SequenceError):
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
        cls.register()
        return cls


class LazyRegistry(collections.abc.Mapping):
    class LazyValue(object):
        def __init__(self, instance, factory):
            self.instance = instance
            self.factory = factory

        def get(self, name):
            if self.instance is None:
                self.instance = self.factory()
            self.instance._set_name(name)
            return self.instance

    def __init__(self):
        self._data = collections.OrderedDict()
        self._metadata = collections.defaultdict(dict)

    def register_metadata(self, name, **kwargs):
        for key, value in kwargs.items():
            self._metadata[key][name] = value

    def get_metadata(self, name, key):
        return self._metadata[key].get(name, None)

    def register_instance(self, name, instance, **metadata):
        instance = self.LazyValue(instance=instance, factory=None)
        self._data[name] = instance
        self.register_medatata(name, **metadata)

    def register_factory(self, name, factory, **metadata):
        instance = self.LazyValue(instance=None, factory=factory)
        self._data[name] = instance
        self.register_metadata(name, **metadata)

    def unregister(self, name):
        if name in self._data:
            del self._data[name]
        for key, md in self._metadata.items():
            md.pop(name, None)

    def __getitem__(self, name):
        return self._data[name].get(name)

    def __iter__(self):
        yield from self._data

    def __len__(self):
        return len(self._data)
        
        
class Sequence(metaclass=SMeta):
    __metadata__ = {'description', 'oeis'}
    __instances__ = weakref.WeakValueDictionary()
    __registry__ = LazyRegistry()
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
            instance._instance_name = None
            instance._instance_hash = None
            instance._instance_expr = None
            instance._instance_doc = None
            cls.__instances__[parameters] = instance
            return instance

    def __init__(self):
        # WARNING: this empty __init__method is needed in order to correctly
        #          inspect default arguments in __new__
        pass

    def _is_bound(self):
        return True

    def is_bound(self):
        if not self._is_bound():
            return False
        for child in self.children():
            if not child.is_bound():
                return False
        return True

    def as_string(self):
        if self._instance_name is None:
            return self._str_impl()
        return self._instance_name

    def _str_impl(self):
        return repr(self)

    def _make_expr(self):
        if self._instance_name:
            return sympy.symbols(self._instance_name, integer=True)

    def _make_simplify_expr(self, vdict):
        expr = self.expr
        if expr is not None:
            return expr
        else:
            symbol = "tmp_{}".format(len(vdict))
            vdict[symbol] = self
            return sympy.symbols(symbol, integer=True)

    @property
    def expr(self):
        if self._instance_expr is None:
            self._instance_expr = self._make_expr()
        return self._instance_expr

    @property
    def traits(self):
        return self._instance_traits

    def set_traits(self, *traits):
        for trait in traits:
            if not isinstance(trait, Trait):
                raise TypeError("{!r} is not a Trait".format(trait))
        self._instance_traits |= frozenset(traits)
        return self

    def set_doc(self, doc):
        self._instance_doc = doc
        return self

    @classmethod
    def _check_metadata(cls, metadata):
        for key in metadata:
            if key not in cls.__metadata__:
                raise ValueError("unknown metadata key: {}".format(key))

    @classmethod
    def register_factory(cls, name, factory, **metadata):
        cls._check_metadata(metadata)
        cls.__registry__.register_factory(name, factory, **metadata)

    @classmethod
    def register_instance(cls, name, sequence, **metadata):
        cls._check_metadata(metadata)
        cls.__registry__.register_instance(name, sequence, **metadata)

    @classmethod
    def unregister(cls, name):
        cls.__registry__.unregister(name)

    def forget(self):
        self.__class__.__instances__.pop(self._instance_parameters)
        self.__class__.unregister(self._instance_name)

    @classmethod
    def register(cls):
        pass

    def _set_name(self, name):
        self._instance_name = name

    @abc.abstractmethod
    def __iter__(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def __call__(self, i):
        raise NotImplementedError()

    def __getitem__(self, i):
        return self(i)

    def doc(self):
        """Returns the documentation"""
        if self._instance_doc:
            return self._instance_doc

    @property
    def name(self):
        return getattr(self, '_instance_name', None)

    @abc.abstractmethod
    def __iter__(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def __call__(self, i):
        raise NotImplementedError()

    def __getitem__(self, i):
        return self(i)

    def doc(self):
        """Returns the documentation"""
        if self._instance_doc:
            return self._instance_doc
        else:
            return self.description()

    def description(self):
        """Returns the sequence description"""
        value = self.__registry__.get_metadata(self.name, 'description')
        if value is None:
            value = repr(self)
        return value

    def oeis(self):
        """Returns the sequence OEIS id"""
        return self.__registry__.get_metadata(self.name, 'oeis')

    @classmethod
    def get_registry(cls):
        return cls.__registry__

    def has_trait(self, trait):
        return trait in self.traits

    def has_traits(self, traits):
        return self.traits >= frozenset(traits)

    @classmethod
    def iter_sequences_with_traits(cls, traits):
        for seq in cls.get_registry().values():
            if seq.has_traits(traits):
                yield seq

    @classmethod
    def get_sequences_with_traits(cls, traits, order=False):
        sequences = list(cls.iter_sequences_with_traits(traits))
        if order:
            sequences.sort(key=str)
        return sequences
        
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

    def __le__(self, other):
        return Le(self, other)

    def __lt__(self, other):
        return Lt(self, other)

    def __ge__(self, other):
        return Ge(self, other)

    def __gt__(self, other):
        return Gt(self, other)

    def __eq__(self, other):
        return Eq(self, other)

    def __ne__(self, other):
        return Ne(self, other)

    def __hash__(self):
        if self._instance_hash is None:
            self._instance_hash = hash(self.as_string())
        return self._instance_hash

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
    def get_locals(cls):
        locals = {
            "ANY": ANY,
            "Any": Any,
            "Interval": Interval,
            "LowerBound": LowerBound,
            "UpperBound": UpperBound,
            "Set": Set,
            "Value": Value,
            "rseq": rseq,
            "floor": idem,  # sympy: a / b -> floor(a/b)
        }
        for sequence_type in Sequence.sequence_types():
            locals[sequence_type.__name__] = sequence_type
        locals.update(Sequence.__registry__)
        locals.update(BackIndexer.__registry__)
        return locals

    @classmethod
    def compile(cls, source, simplify=False, locals=None, check_type=True):
        """Compile sequence from source.
    
           Parameters
           ----------
           source: str
               Sequence source
           simplify: bool, optional
               Simplify sequence (defaults to False)
           locals dict, optional
               locals dictionary (defaults to None)
           check_type: bool, optional
               check if the output is a Sequence (defaults to True)
    
           Returns
           -------
           Sequence
               The compiled Sequence.
        """
        globals = cls.get_locals()
        if locals is None:
            locals = {}
        sequence = eval(source, globals, locals)
        if check_type:
            if gmpy2.is_integer(sequence):
                sequence = Const(value=sequence)
            elif isinstance(sequence, float):
                sequence = Const(value=int(sequence))
            elif not isinstance(sequence, Sequence):
                raise TypeError("{!r} is not a Sequence".format(sequence))
        if isinstance(sequence, Sequence) and simplify:
            sequence = sequence.simplify()
        return sequence

    def __repr__(self):
        plist = []
        parameters = self.__signature__.parameters
        def mkrepr(obj):
            if isinstance(obj, Sequence):
                return str(obj)
            else:
                return repr(obj)
        for key, val in self._instance_parameters[1:]:
            par = parameters[key]
            if par.kind == par.VAR_POSITIONAL:
                for x in val:
                    plist.append(mkrepr(x))
            elif par.kind == par.KEYWORD_ONLY:
                plist.append("{}={}".format(key, mkrepr(val)))
            else:
                plist.append(mkrepr(val))
        return "{}({})".format(
            type(self).__name__,
            ", ".join(plist))

    @classmethod
    def from_expr(cls, expr, locals=None):
        return cls.compile(str(expr), locals=locals)
        
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
            return self._simplify_backup()

    def _simplify_backup(self):
        return self

    def __str__(self):
        return astor.to_source(
            ast.parse(self.as_string()),
            pretty_source=lambda s: "".join(s)).strip()

    @classmethod
    def make_sequence(cls, operand):
        if isinstance(operand, Sequence):
            return operand
        elif gmpy2.is_integer(operand):
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


def compile_sequence(source, simplify=False):
    return Sequence.compile(source, simplify=simplify)


class StashMixin(object):
    __stash__ = None

    @classmethod
    def get_stash(cls):
        if cls.__stash__ is None:
            cls.__stash__ = cls._create_stash()
        return cls.__stash__

    @classmethod
    @abc.abstractmethod
    def _create_stash(cls):
        raise NotImplementedError()

    def __getitem__(self, i):
        stash = self.get_stash()
        if 0 <= i < len(stash):
            return stash[i]
        else:
            return super().__getitem__(i)

    def __iter__(self):
        stash = self.get_stash()
        yield from stash
        for i in itertools.count(start=len(stash)):
            yield self(i)


class EnumeratedSequence(StashMixin, Sequence):

    def __call__(self, i):
        stash = self.get_stash()
        if i >= len(stash):
            raise SequenceUnknownValueError("{}[{}]".format(self, i))
        return stash[i]

    def get_values(self, num, *, start=0):
        return self.get_stash()[start:start + num]


class Iterator(Sequence):
    """Iterator sequence"""

    @functools.lru_cache(maxsize=1024)
    def __call__(self, i):
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

    def _simplify_backup(self):
        o = self.operand.simplify()
        return self._unop(
            self.operand.simplify()
        )

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

    def _simplify_backup(self):
        vdict = {}
        left = self.left.expr
        if left is None:
            left = self.left.simplify()._make_simplify_expr(vdict)
        right = self.right.expr
        if right is None:
            right = self.right.simplify()._make_simplify_expr(vdict)
        expr = self._binop(left, right)
        return self.from_expr(str(expr), locals=vdict)


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


class Le(BinOp):
    __operator__ = '<='

    @classmethod
    def _binop(cls, l, r):
        return int(l <= r)


class Lt(BinOp):
    __operator__ = '<'

    @classmethod
    def _binop(cls, l, r):
        return int(l < r)


class Ge(BinOp):
    __operator__ = '>='

    @classmethod
    def _binop(cls, l, r):
        return int(l >= r)


class Gt(BinOp):
    __operator__ = '>'

    @classmethod
    def _binop(cls, l, r):
        return int(l > r)


class Eq(BinOp):
    __operator__ = '=='

    @classmethod
    def _binop(cls, l, r):
        return int(l == r)


class Ne(BinOp):
    __operator__ = '!='

    @classmethod
    def _binop(cls, l, r):
        return int(l != r)


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
    __traits__ = frozenset([Trait.INJECTIVE, Trait.POSITIVE, Trait.INCREASING])

    def __call__(self, i):
        return i

    @classmethod
    def register(cls):
        cls.register_factory('i', cls,
            oeis='A001477',
            description='f(i) := i',
        )


class Natural(Function):
    __traits__ = frozenset([Trait.INJECTIVE, Trait.POSITIVE, Trait.NON_ZERO, Trait.INCREASING])

    def __call__(self, i):
        return i + 1

    @classmethod
    def register(cls):
        cls.register_factory('n', cls,
            oeis='A000027',
            description='f(i) := i + 1',
        )


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


class BackIndexer(Sequence):
    __registry__ = LazyRegistry()
    __recursive_sequence__ = None

    def __init__(self, offset):
        if not isinstance(offset, int):
            raise TypeError("{!r} is not a valid offset".format(offset))
        if offset < 0:
            raise ValueError("{!r} is not a valid offset".format(offset))
        self._offset = offset
        super().__init__()

    @property
    def offset(self):
        return self._offset

    @classmethod
    @contextlib.contextmanager
    def bind(cls, recursive_sequence):
        if not (recursive_sequence is None or isinstance(recursive_sequence, RecursiveSequence)):
            raise TypeError(recursive_sequence)
        old_recursive_sequence = cls.__recursive_sequence__
        try:
            cls.__recursive_sequence__ = recursive_sequence
            yield
        finally:
            cls.__recursive_sequence__ = old_recursive_sequence

    def _is_bound(self):
        return self.__recursive_sequence__ is not None

    def _check_bound(self):
        if self.__recursive_sequence__ is None:
            raise SequenceUnboundError(self)

    def __call__(self, i):
        self._check_bound()
        return self.__recursive_sequence__.get_item(i - self._offset)

    def __iter__(self):
        self._check_bound()
        offset = self._offset
        for i in itertools.count(start=0):
            yield self(i + offset)

    def __getitem__(self, i):
        return self(i)

    @classmethod
    def register(cls):
        def make_factory(index):
            return lambda: cls(index)
        for i in range(_NUM_INDEXERS):
            cls.register_factory('I{}'.format(i), make_factory(i))

    def __repr__(self):
        if self._offset < _NUM_INDEXERS:
            return "I{}".format(self._offset)
        else:
            return "rseq[{}]".format(self._offset)


class RecursiveSequence(Sequence):
    __maxlen__ = 100000

    def __init__(self, known_items, generating_sequence):
        self._known_items = tuple(gmpy2.mpz(x) for x in known_items)
        if isinstance(generating_sequence, str):
            generating_sequence = compile_sequence(generating_sequence)
        generating_sequence = self.make_sequence(generating_sequence)
        # if isinstance(generating_sequence, SequenceBuilder):
        #     generating_sequence = generating_sequence({'recursive_sequence': self})
        self._generating_sequence = generating_sequence
        offsets = set()
        set_maxlen = True
        for depth, seq in self.walk():
            if isinstance(seq, BackIndexer):
                offset = seq.offset
                offsets.add(seq.offset)
        if offsets:
            max_offset = max(offsets)
            if len(self._known_items) < max_offset:
                raise ValueError("sequence {}: too few known items: {} < {}".format(self, len(self._known_items), max_offset))
        else:
            max_offset = 0
        self.__items = []
        self.__items.extend(self._known_items)
        super().__init__()

    def simplify(self):
        o = type(self)(self._known_items, self._generating_sequence.simplify())
        return o

    @property
    def known_items(self):
        return self._known_items

    @property
    def generating_sequence(self):
        return self._generating_sequence

    def children(self):
        yield self._generating_sequence

    def get_item(self, i):
        items = self.__items
        if i < 0 or i >= len(items):
            raise RecursiveSequenceError("request for item {} in recursive sequence with {} items".format(i, len(items)))
        return items[i]

    def __getitem__(self, i):
        return self(i)

    def __call__(self, i):
        with BackIndexer.bind(self):
            items = self.__items
            if i > self.__maxlen__:
                raise SequenceUnknwonError("request for item {} > maxlen {}".format(i, self.__maxlen__))
            if i < len(items):
                return items[i]
            generating_sequence = self._generating_sequence
            for j in range(len(items), i + 1):
                item = generating_sequence(j)
                items.append(item)
            return items[-1]

    def __iter__(self):
        with BackIndexer.bind(self):
            items = self.__items
            yield from items
            generating_sequence = self._generating_sequence
            for j in range(len(items), self.__maxlen__ + 1):
                item = generating_sequence(j)
                yield item
                items.append(item)
            raise SequenceUnknwonError("iteration over maxlen {}".format(self.__maxlen__))

    def __repr__(self):
        lst = [str(x) for x in self._known_items]
        lst.append(str(self._generating_sequence))
        return "rseq({})".format(', '.join(lst))


class RecursiveSequenceMaker(object):
    def __call__(self, arg0, *args):
        if args:
            known_items = (arg0,) + args[:-1]
            generating_sequence = args[-1]
        else:
            known_items = ()
            generating_sequence = arg0
        return RecursiveSequence(
            known_items=known_items,
            generating_sequence=generating_sequence,
        )
        
    def __getitem__(self, index):
        return BackIndexer(index)


rseq = RecursiveSequenceMaker()
