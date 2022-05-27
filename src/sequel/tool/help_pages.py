"""
Help pages
"""

import collections
import contextlib
import itertools
from io import StringIO
import shlex
import sys
import traceback

from ..declaration import (
    parse_declaration,
    declared,
    DeclarationType,
)
from .display import Printer, iter_item_types
from .page import Navigator, Element, Paragraph, Quotation, Break, Title
from .quiz import QuizShell
from .shell import SequelShell
from ..sequence import compile_sequence, Sequence, RecursiveSequenceError, Trait, get_trait_description
from ..items import make_items, ANY
from ..utils import assert_sequence_matches

__all__ = [
    'create_help',
]


DummyCatalogDeclaration = collections.namedtuple(
    'DummyCatalogDeclaration', 'filename sources')
    

@contextlib.contextmanager
def redirect(stdout, stderr):
    old_stdout, old_stderr = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = stdout, stderr
        yield
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr


class OutputLines(Element):
    def __init__(self, *, printer, max_lines=None, **kwargs):
        self.printer = printer
        self.max_lines = max_lines
        super().__init__(**kwargs)

    def _output_lines(self, text):
        lines = text.split('\n')
        max_lines = self.max_lines
        if max_lines is not None:
            if isinstance(max_lines, (list, tuple)):
                max_lines, end_lines = max_lines
            else:
                max_lines, end_lines = max_lines, 0
            if len(lines) > max_lines:
                del lines[max_lines:len(lines) - end_lines]
                lines.insert(max_lines, "...")
        return lines

    def _format_lines(self, lines):
        return '\n'.join("  " + line for line in lines)


class TraitsElement(OutputLines):
    def get_text(self):
        printer = self.printer
        trait_fmt = "{name} {desc}"
        def adj(txt):
            return "{:20s}".format(txt)

        lines = [trait_fmt.format(name=printer.bold(adj("TRAIT")), desc=printer.bold("DESCRIPTION"))]
        for trait in Trait:
            lines.append(trait_fmt.format(name=printer.blue(adj(trait.name)), desc=get_trait_description(trait)))
        return "\n".join(lines)

        
class Example(OutputLines):
    def __init__(self, *, declarations=None, plugins=None, **kwargs):
        if declarations is None:
            declarations = ()
        self._declarations = tuple(declarations)
        if plugins is None:
            plugins = ()
        self._plugins = tuple(plugins)
        super().__init__(**kwargs)

    @contextlib.contextmanager
    def declare(self):
        declarations = []
        for declaration in self._declarations:
            if isinstance(declaration, DummyCatalogDeclaration):
                for decl in declaration.sources:
                    declarations.append(parse_declaration(decl))
            else:
                declarations.append(declaration)
        with declared(*declarations):
            yield

    def global_args(self):
        args = []
        for declaration in self._declarations:
            if isinstance(declaration, DummyCatalogDeclaration):
                args.append("--declarations-file={!r}".format(declaration.filename))
            elif declaration.decl_type is DeclarationType.SEQUENCE:
                if declaration.name is None:
                    decl = declaration.source
                else:
                    decl = "{}:={}".format(declaration.name, declaration.source)
                args.append("--declare={!r}".format(decl))
        return args

    def command_args(self):
        return []

    def command_line(self, command):
        #g_args = [shlex.quote(arg) for arg in self.global_args()]
        #c_args = [shlex.quote(arg) for arg in self.command_args()]
        g_args = self.global_args()
        c_args = self.command_args()
        return " ".join(["$ sequel"] + g_args + [command] + c_args)

    def _format_lines(self, lines):
        return '\n'.join("  " + line for line in lines)


class SimplifyMixIn(object):
    def __init__(self, *, simplify=None, **kwargs):
        self.simplify = simplify
        super().__init__(**kwargs)

    def command_args(self):
        args = super().command_args()
        if self.simplify:
            args.append("--simplify")
        return args


class RaisingMixIn(object):
    def __init__(self, *, expected_exception=False, **kwargs):
        self.expected_exception = None
        if isinstance(expected_exception, type) and issubclass(expected_exception, Exception):
            self.expected_exception = expected_exception
        elif isinstance(expected_exception, bool):
            if expected_exception:
                self.expected_exception = BaseException
            else:
                self.expected_exception = None
        else:
            raise TypeError(expected_exception)
        super().__init__(**kwargs)

    @contextlib.contextmanager
    def raising(self, file=sys.stderr):
        if self.expected_exception:
            try:
                yield
            except self.expected_exception:
                file.write(self.printer.red(traceback.format_exc()))
            else:
                raise RuntimeError("should raise {} but it doesn't".format(self.expected_exception))
        else:
            yield

            
class DocExample(SimplifyMixIn, Example):
    def __init__(self, printer, kind, source, simplify=False, max_lines=None, declarations=None, plugins=None):
        super().__init__(printer=printer, simplify=simplify, max_lines=max_lines, declarations=declarations, plugins=plugins)
        self.kind = kind
        self.source = source
        self.simplify = simplify

    def command_args(self):
        args = super().command_args()
        if self.kind == 'expressions':
            args.append('-e')
            args.extend(self.source)
        elif self.kind == 'traits':
            args.append('-w')
            args.extend(self.source)
        return args

    def get_text(self):
        ios = StringIO()
        if self.kind == 'all':
            sources = None
        elif self.kind == 'expressions':
            sources = self.source
        elif self.kind == 'traits':
            traits = [Trait[trait] for trait in self.source]
            sources = Sequence.get_sequences_with_traits(traits, order=True)
        with self.printer.set_file(ios):
            self.printer.print_doc(sources=sources, simplify=self.simplify)
        lines = []
        lines.append(self.command_line("doc"))
        lines.extend(self._output_lines(ios.getvalue()))
        return self._format_lines(lines)


class ShowExample(SimplifyMixIn, RaisingMixIn, Example):
    def __init__(self, printer, kind, source, simplify=False, expected_exception=False, max_lines=None, num_items=None, declarations=None, plugins=None):
        super().__init__(printer=printer, simplify=simplify, expected_exception=expected_exception, max_lines=max_lines, declarations=declarations, plugins=plugins)
        self.kind = kind
        self.source = source
        self.simplify = simplify
        self.num_items = num_items

    def command_args(self):
        args = super().command_args()
        if self.kind == 'expression':
            args.append('-e')
            args.append(repr(str(self.source)))
        if self.kind == 'random':
            args.append('-r')
        return args

    def get_text(self):
        ios = StringIO()
        with self.printer.set_file(ios):
            with self.raising(ios):
                with self.declare():
                    sequence = compile_sequence(self.source, simplify=self.simplify)
                self.printer.print_sequence(sequence, num_items=self.num_items)
        lines = []
        lines.append(self.command_line("show"))
        lines.extend(self._output_lines(ios.getvalue()))
        return self._format_lines(lines)


class SearchExample(Example):
    def __init__(self, *, printer, kind, source, sequences, max_lines=None, declarations=None, plugins=None):
        super().__init__(printer=printer, max_lines=max_lines, declarations=declarations, plugins=plugins)
        self.kind = kind
        self.source = source
        self.target_sequence = None
        if kind == 'items':
            items = source
            assert sequences is not None
        else:
            self.target_sequence = Sequence.make_sequence(source)
            items = self.target_sequence.get_values(printer.num_items)
            if sequences is None:
                sequences = [self.target_sequence]
        self.orig_items = tuple(items)
        self.items = make_items(items)
        seqs = []
        with self.declare():
            for seq in sequences:
                if isinstance(seq, str):
                    seq = compile_sequence(seq)
                seqs.append(seq)
        self.sequences = tuple(seqs)
        for sequence in self.sequences:
            assert_sequence_matches(sequence, self.items)

    def command_args(self):
        args = super().command_args()
        if self.kind == 'items':
            args.append('-i')
            args.extend(str(i) for i in self.orig_items)
        elif self.kind == 'expression':
            args.append('-e')
            args.append(repr(self.source))
        elif self.kind == 'random':
            args.append('-r')
        return args

    def get_text(self):
        ios = StringIO()
        printer = self.printer
        with printer.set_file(ios):
            kwargs = {'target_sequence': self.target_sequence}
            if self.kind == 'expression':
                printer.print_evaluate_expression_header(self.source)
            elif self.kind == 'random':
                printer.print_generate_sequence_header()
            else:
                kwargs['item_types'] = iter_item_types(self.items)
            printer.print_search_header(self.items)
            printer.print_search_result(self.sequences, **kwargs)
        lines = []
        lines.append(self.command_line("search"))
        lines.extend(self._output_lines(ios.getvalue()))
        return self._format_lines(lines)


class Shellxample(Example):
    def __init__(self, printer, commands, max_lines=None, declarations=None, plugins=None):
        super().__init__(printer=printer, max_lines=max_lines, declarations=declarations, plugins=plugins)
        self.commands = list(commands)

    def get_text(self):
        ios = StringIO()
        shell = SequelShell(printer=self.printer)
        with self.printer.set_file(ios):
            with redirect(ios, ios):
                shell.run_commands(self.commands, echo=True)
        lines = []
        lines.append(self.command_line("shell"))
        lines.extend(self._output_lines(ios.getvalue()))
        return self._format_lines(lines)


class PlayExample(Example):
    def __init__(self, printer, sequences, commands, num_items=5, max_lines=None, banner=None, max_games=1, declarations=None, plugins=None):
        super().__init__(printer=printer, max_lines=max_lines, declarations=declarations, plugins=plugins)
        self.sequences = [Sequence.make_sequence(x) for x in sequences]
        self.commands = list(commands)
        self.num_items = num_items
        self.banner = banner
        self.max_games = max_games

    def command_args(self):
        return super().command_args() + ['--num-items={}'.format(self.num_items)]

    def get_text(self):
        ios = StringIO()
        with self.printer.set_file(ios):
            with redirect(ios, ios):
                quiz_shell = QuizShell(printer=self.printer, sequence_iterator=itertools.cycle(self.sequences),
                                       num_known_items=self.num_items, max_games=self.max_games)
                quiz_shell.run_commands(self.commands, echo=True, banner=self.banner)
        lines = []
        lines.append(self.command_line("play"))
        lines.extend(self._output_lines(ios.getvalue()))
        return self._format_lines(lines)

def create_help():
    printer = Printer()
    # wip_text = printer.red("Work in progress")

    navigator = Navigator()
    ### HOME
    navigator.new_page(
        name="introduction",
        elements=[
            """\
Sequel is a command line tool to find integer sequences:
""",
            SearchExample(printer=printer,
                          kind="items", source=[2, 3, 5, 7, 11],
                          sequences=[compile_sequence('p')]),
            SearchExample(printer=printer,
                          kind="items", source=[2, 3, 5, 7, 13, 17],
                          sequences=[compile_sequence('m_exp')]),
            """\
The SEARCH subcommand accepts an arbitrary number of integer values and returns a list of matching sequences;
it may also return multiple matches:
""",
            SearchExample(printer=printer,
                          kind="items", source=[2, 3, 5, 7],
                          sequences=[compile_sequence('p'), compile_sequence('m_exp')]),
            """\
Sequel knows many CORE-SEQUENCES; the DOC subcommand can be used to get information about one or more sequences:
""",
            DocExample(printer=printer,
                       kind='all', source=None, max_lines=(5, 3)),
            """\
The SHOW subcommand can be used to show information about a sequence:
""",
            ShowExample(printer=printer,
                        kind='expression', source='p * zero_one'),
            """\
The SHELL subcommand opens an interactive python shell to play with sequel sequences:
""",
#             Shellxample(printer=printer,
#                                  commands=['print_sequence(p * zero_one)']),
            """\
The PLAY subcommand generates an hidden random sequence and let you guess what sequence it is.
""",
#             PlayExample(printer=printer,
#                                  sequences=['p * zero_one'], commands=['q.guess(p * zero_one)']),
        ]
    )

    ### SEQUENCES
    navigator.new_page(
        name="sequences",
        elements=[
            """\
Sequel understands many SEQUENCES. There are many CORE-SEQUENCES; for instance 'p' is the prime numbers sequence [2, 3, 5, 7, ...].

Other sequences can be created using sequence EXPRESSIONS; for instance, 'p + 10' is the sequence of the prime numbers plus ten [12, 13, 15, 17, ...].

Sequences can be classified by TRAITS.
""",
        ],
    )

    ### CORE
    navigator.new_page(
        name="core sequences",
        parent="sequences",
        elements=[
            """\
Sequel knows many sequences; the DOC subcommand without arguments shows information about all CORE-SEQUENCES:
""",
            DocExample(printer=printer,
                       kind='all', source=None),
        ],
    )

    ### SEQUENCE_EXPRESSIONS
    navigator.new_page(
        name="expressions",
        parent="sequences",
        elements=[
            """\
New sequences can be created by composing CORE-SEQUENCES and integer constants with many operators.

An integer constant is considered as a const sequence; for instance, the sequence '3' always repeats the integer value '3':
""",
            ShowExample(printer=printer,
                        kind='expression', source='3'),
            """\
The usual arithmetic operators (+, -, *, /, //, %, **) can be used to obtain new sequences; for instance:
""",
            ShowExample(printer=printer,
                        kind='expression', source='3 * p ** 2 - m_exp'),
            """\
Since sequel only supports integer sequences, the division operator always truncates the result:
""",
            ShowExample(printer=printer,
                        kind='expression', source='m_exp // p'),
            """\
Powers are also available: the sequence 'Power(3)' is the sequence i**3':
""",
            ShowExample(printer=printer,
                        kind='expression', source='Power(3)'),
            ShowExample(printer=printer,
                        kind='expression', source='Power(7)'),
            """\
The python slicing syntax allows to create SLICES, both finite and infinite: for instance:
""",
            Quotation("""\
 * 'p[:3]' is a finite sequence producing the values [2, 3, 5]
 * 'p[1:]' is an infinite sequence producing the values [3, 5, 7, 11, 13, ...]
 * 'p[1:6]' is a finite sequence producing the values [3, 5, 7, 11, 13]
 * 'p[1::2]' is an infinite sequence producing the values [3, 7, 13, 19, ...]
 * 'p[1:10:2]' is a finite sequence producing the values [3, 7, 13, 19, 29]
"""),
            ShowExample(printer=printer,
                        kind='expression', source='p[1:10:2]'),
            """\
Sequences can be composed with the '|' operator. The sequence 'p | n' is the sequence primes 'p' computed on the values of the natural numers sequence 'n':
""",
            ShowExample(printer=printer,
                        kind='expression', source='p | n'),
            """\
Sequences can also be created by enumerating a (limited) set of values:
""",
            ShowExample(printer=printer,
                        kind='expression', source='Values(1, 5, 0, 10)'),
            ShowExample(printer=printer,
                        kind='expression', source='Values(1, 5, 0, 10) * n'),
            """\
The 'roundrobin' function creates a new sequence by taking values from other sequences:
""",
            ShowExample(printer=printer,
                        kind='expression', source='roundrobin(p, 0, 7 * n - 10)'),
            """\
It is possible to CHAIN multiple sequences or lists of items; for instance:
""",
            ShowExample(printer=printer,
                        kind='expression', source='chain(-p[:3], p[3:6], i)'),
            ShowExample(printer=printer,
                        kind='expression', source='chain(-p[:3], [102, 101, 100], i)'),
            """\
Other available functions are 'integral', 'derivative', 'summation', 'product':
""",
            ShowExample(printer=printer,
                        kind='expression', source='integral(p)'),
            ShowExample(printer=printer,
                        kind='expression', source='derivative(p)'),
            ShowExample(printer=printer,
                        kind='expression', source='product(p)'),
            """\
The 'moessner' functional applies the MOESSNER-ALGORITHM;
the input sequence defines the selected indices (starting from 1).
""",
            ShowExample(printer=printer,
                        kind='expression', source='moessner(n * 2)'),
            ShowExample(printer=printer,
                        kind='expression', source='moessner(n * 3)'),
            ShowExample(printer=printer,
                        kind='expression', source='moessner(triangular[1:])'),
            """\
Notice that moessner(i) returns the factorials of the natural numbers:
""",
            ShowExample(printer=printer,
                        kind='expression', source='moessner(i)'),
            """\
The 'ifelse' function creates a new function according to a condition. For instance, the following sequence is '1000 + fib01' for the indices where catalan is even, and p for the indices where catalan is odd:
""",
            ShowExample(printer=printer,
                        kind='expression', source='ifelse(catalan % 2 == 0, 1000 + fib01, p)'),
            """\
The 'where(condition, sequence)' function is the list of values of sequence for the indices where the condition is True.
""",
            ShowExample(printer=printer,
                        kind='expression', source='where((p + 1) % 4 == 0, p)'),
            """\
This is the list of values p where p + 1 can be divided by 4.
By default the sequence is 'i', so where(condition) is the list of indices where condition is True:
""",
            ShowExample(printer=printer,
                        kind='expression', source='where((p + 1) % 4 == 0)'),
            """\
Moreover, some parametric sequences are available. For instance, the geometric, arithmetic sequences:
""",
            ShowExample(printer=printer,
                        kind='expression', source='Geometric(base=8)'),
            ShowExample(printer=printer,
                        kind='expression', source='Arithmetic(start=2, step=7)'),
            """\
Fibonacci sequences are also available; 'Fib' is the generic Fibonacci sequence with parametric 'first' and 'second' values. Three specialized sequences are available:
'fib01', 'fib11' and 'lucas':
are defined as 
""",
            ShowExample(printer=printer,
                        kind='expression', source='fib01'),
            ShowExample(printer=printer,
                        kind='expression', source='Fib(first=2, second=4)'),
            """\
The polygonal numbers are also available:
""",
            ShowExample(printer=printer,
                        kind='expression', source='triangular'),
            ShowExample(printer=printer,
                        kind='expression', source='pentagonal'),
            ShowExample(printer=printer,
                        kind='expression', source='Polygonal(8)'),
            """\
Additionally, a generic RECURSIVE-SEQUENCE can be defined; the following sequence is the recursive definition of the factorial function:
""",
            ShowExample(printer=printer,
                        kind='expression', source='rec(1, I1 * i)'),
        ],
    )

    ### SLICES
    navigator.new_page(
        name="slices",
        parent="expressions",
        elements=[
            """\
The slicing syntax can be used to create a new sequence from an existing one by selecting only a subset of elements. For instance:
""",
            ShowExample(printer=printer,
                        kind='expression', source='p[:3]'),
            ShowExample(printer=printer,
                        kind='expression', source='p[1:]'),
            ShowExample(printer=printer,
                        kind='expression', source='p[1:6]'),
            ShowExample(printer=printer,
                        kind='expression', source='p[1::2]'),
            ShowExample(printer=printer,
                        kind='expression', source='p[1:10:2]'),
        ],
    )

    ### CHAIN
    navigator.new_page(
        name="chain",
        parent="expressions",
        elements=[
            """\
The 'chain' function chains items from multiple sequences or lists of values; for instance, 'chain([1, 3, 1], p)'
is an infinite sequence producing the values [1, 3, 1, 2, 3, 5, 7, 11, ...]:
""",
            ShowExample(printer=printer,
                        kind='expression', source='chain([1, 3, 1], p)'),
            """\
Notice that all the arguments but the last one should be finite sequences (for instance limited SLICES) or lists,
otherwise the next sequences are pointless. For instance, the following expression will produce only items from
the infinite sequence 'p[1:]', while the 'm_exp' sequence is not used.
""",
            ShowExample(printer=printer,
                        kind='expression', source='chain(p[1:], m_exp)'),
        ],
    )

    ### MOESSNER-ALGORITHM
    navigator.new_page(
        name="moessner algorithm",
        parent="expressions",
        elements=[
            """\
The Moessner algorithm creates a new sequence from a sequence of indices starting with 1.
See https://thatsmaths.com/2017/09/14/moessners-magical-method/ or https://www.youtube.com/watch?v=rGlpyFHfMgI.
""",
            Quotation("""\
Consider the list of positive integers:

    1    2    3    4    5    6    7    8    9

The consider a non-negative, non-decreasing, non-null sequence of highlighted indices
starting with 1; for instance, the sequence [3, 6, 9, ...]:

    1    2   (3)   4    5   (6)   7    8   (9)

For each of the blocks [1, 2, 3], [4, 5, 6], [7, 8, 9], ... the Moessner
algorithm is implemented as follows:

    1    2   (3)   4    5   (6)   7    8   (9)
    1   (3)        7  (12)       19  (27)
   (1)            (8)           (27)

In each line, each block has one element less than the block above; the values are
the sum of the values on the left and above. For instance, on the second block, 12 is the sum
of 7 (left) and 5 (above); 8 is the sum of 1 (left) and 7 (above).

These are the cubes of the highlighted indices.
"""),
            """\
Some interesting index sequences:
""",
            ShowExample(printer=printer,
                        kind='expression', source='moessner(n * 2)'),
            ShowExample(printer=printer,
                        kind='expression', source='moessner(n * 3)'),
            ShowExample(printer=printer,
                        kind='expression', source='moessner(triangular[1:])'),
            """\
An interesting property of the Moessner algorithm is that it seems to transform sums into products and
products into powers.
""",
            Quotation("""\
Consider an arbitraty non-decreasing non-null sequence of items

    S := [a, b, c, d, ...]

Then consider the following sequence:
    I == moessner_ext_index(S) := [
        (1 * a),
        (2 * a) + (1 * b),
        (3 * a) + (2 * b) + (1 * c),
        (4 * a) + (3 * b) + (2 * c) + (1 * d),
        ...
    ]

The Moessner algorithm applied to the sequence I produces:

    moessner(I) := [
        (1 ** a),
        (2 ** a) * (1 ** b),
        (3 ** a) * (2 ** b) * (1 ** c),
        (4 ** a) * (3 ** b) * (2 ** c) * (1 ** d),
        ...
    ]

For instance, if a is 2 and b, c, d, ... are all equal to 0 (i.e. S := 'chain([2], 0)'), then
"""),
            ShowExample(printer=printer,
                        kind='expression', source='moessner_ext_index(chain([2], 0))'),
            ShowExample(printer=printer,
                        kind='expression', source='moessner(moessner_ext_index(chain([2], 0)))'),
            """\
This is the same as 'moessner(n ** 2)'. Or:
""",
            ShowExample(printer=printer,
                        kind='expression', source='moessner_ext_index(1)'),
            ShowExample(printer=printer,
                        kind='expression', source='moessner(moessner_ext_index(1))'),
            """\
This is the same as 'moessner(triangular[1:])'.

The 'moessner_ext' function is a fast implementation of the Moessner algorithm based on the property above, to obtain directly
moessner(I) from S:
""",
            ShowExample(printer=printer,
                        kind='expression', source='moessner_ext(chain([2], 0))'),
            ShowExample(printer=printer,
                        kind='expression', source='moessner_ext(1)'),
        ]
    )

    ### RECURSIVE-SEQUENCE_EXPRESSIONS
    navigator.new_page(
        name="recursive sequence",
        parent="expressions",
        elements=[
            """\
Generic recursive sequences can be defined using the "rec" function: it takes a list of known values and a generating sequence. The generating sequence is a special sequence that, given the last generated items, produces the next one. The form of a recursive sequence definition is
""",
            Quotation("""\
  rec(K0, K1, ..., KN, GS)

where:

  K0, K1, ..., KN are the first N known values (N can be 0)
  GS is a generatong sequence
"""),
            """\
The generating sequence is used to produce the items for i >= N; for instance, in 'rec(4, 8, p)', the generating sequence is 'p', and it is used to produce the items with index 2, 3, ...:
""",
            ShowExample(printer=printer,
                        kind='expression', source='rec(4, 8, 0)'),
            """
The generating sequence can be a generic sequence; nevertheless it may contain references to the recursive sequence itself:
""",
            Quotation("""\
  I0     is the recursive sequence itself
  I1     is equivalent to I0 | i - 1
  I2     is equivalent to I0 | i - 2 (or I1 | i - 1)
  ...
  I9     is equivalent to I0 | i - 9
  rec[n] is equivalent to I0 | i - n
"""),
            """\
For instance, 'rec(1, I1 * i)' defines a new sequence starting with 1 and producing new items as the product of the last item ('I1') with the value of the sequence 'i' ([0, 1, 2, 3, ...]). The values are:
""",
            Quotation("""\
  rec(1, I1 * i):
    [0] ->                                   1  (the initial value)
    [1] -> I1 * i(1) == [0] * 1 == 1 * 1 ==  1
    [2] -> I1 * i(2) == [1] * 2 == 1 * 2 ==  2
    [3] -> I1 * i(3) == [2] * 3 == 2 * 3 ==  6
    [4] -> I1 * i(4) == [3] * 4 == 6 * 4 == 24
    ...

This is the same as the factorial sequence.
"""),
            ShowExample(printer=printer,
                        kind='expression', source='rec(1, I1 * i)'),
            """\
As a second example, consider 'rec(0, 1, I1 + I2)'; in this case the known items are two (0 and 1) and the next items are generated as the sum of the last two values (I1 and I2):
""",

            Quotation("""\
  rec(0, 1, I1 + I2):
    [0] ->                                   0  (the first known item)
    [1] ->                                   1  (the second known item)
    [2] -> I1 + I2 == [1] + [0] == 0 + 0 ==  1
    [3] -> I1 + I2 == [2] + [1] == 1 + 1 ==  2
    [4] -> I1 + I2 == [3] + [2] == 2 + 1 ==  3
    [5] -> I1 + I2 == [4] + [3] == 3 + 2 ==  5
    [6] -> I1 + I2 == [5] + [4] == 5 + 3 ==  8
    ...

This is the same as the fib01 sequence.
"""),
            ShowExample(printer=printer,
                        kind='expression', source='rec(0, 1, I1 + I2)'),
            """\
A recursive sequence definition must contain at least N known elements, where N is the max used index in the generating expression; so, if the generating expression is 'I1 + 3 * I3',
the recursive sequence definition must contain at least 3 values. Anyway, it is accepted to define more than N+1 known values, for instance:
""",
            ShowExample(printer=printer,
                        kind='expression', source='rec(3, 2, 1, 0, I1 + 1)'),
            """\
Another constraint on the generating sequence is obviously that it cannot be used to generate items with index N >= the index of the last generated item.
For instance, 'I0', wich is a reference to the recursive sequence itself, is not a valid generating sequence:
""",
            ShowExample(printer=printer,
                        kind='expression', source='rec(0, I0)', expected_exception=RecursiveSequenceError),
            """\
In the definition above the item 1 of the recursive sequence is defined as the item 1 of the recursive sequence itself; this is an error.
Anyway, I0 can be used in a generating sequence definition; for instance 'rec(1, summation(I0) | i - 1)' is defined as follow:
""",
            Quotation("""\
  rec(1, summation(I0) | i - 1):
    [0] ->                                         1  (the first known item)
    [1] -> summation(I0)[0] == sum(1)              1
    [2] -> summation(I0)[1] == sum(1, 1) ==        2
    [3] -> summation(I0)[2] == sum(1, 1, 2) ==     4
    [4] -> summation(I0)[3] == sum(1, 1, 2, 4) ==  8
    ...
"""),
            ShowExample(printer=printer,
                        kind='expression', source='rec(0, 1, summation(I0) | i - 1)'),
            """\
The following sequence computes the items of the Collatz sequence starting with n=19:
""",
            ShowExample(printer=printer,
                        kind='expression', source='rec(19, ifelse(I1 % 2 == 0, I1 // 2, 3 * I1 + 1))', num_items=24),
            """\
Be aware that I0, I1, ... are "limited" sequences: they cannot be used outside a rec(...) definition. Moreover, as stated above, I<N> cannot be used to generate items with index n >= N.
"""
        ],
    )

    ### DOC
    navigator.new_page(
        name="doc",
        elements=[
            """\
Without arguments the DOC command shows the available core sequences.
""",
            DocExample(printer=printer,
                       kind='all', source=None, max_lines=(5, 3)),
            """\
The DOC command can be used to show documentation about selected sequences:
""",
            DocExample(printer=printer,
                       kind='expressions', source=['catalan', 'm_exp', 'p']),
            """\
It is also possible to select sequences by given TRAITS:
""",
            DocExample(printer=printer,
                       kind='traits', source=['INJECTIVE', 'NON_ZERO'], max_lines=(5, 3)),
        ],
    )

    ### TRAITS
    navigator.new_page(
        name="traits",
        parent="sequences",
        elements=[
            """\
Sequence traits are:

""",
        TraitsElement(printer=printer),
    ])

    ### PLAY
    navigator.new_page(
        name="play",
        elements=[
            """\
The PLAY command generates an hidden random sequence and asks you to guess that sequence:
""",
            PlayExample(printer=printer,
                        sequences=['rec(2, 3, I1 * I2 - 1)'], commands=[]),
            """\
The 'q' instance can be used to play the game; run the 'q' command to have an help:
""",
            PlayExample(printer=printer,
                        sequences=['rec(2, 3, I1 * I2 - 1)'], commands=['q']),
            """\
In order to win the game you have to guess a sequence matching the shown items. 
""",
            PlayExample(printer=printer,
                        sequences=['rec(2, 3, I1 * I2 - 1)'], commands=['q.show()', 'q.guess(p)', 'x = rec(2, 3, I1 * I2 - 1)', 'print_sequence(x)', 'q.guess(x)']),
            """\
You can also try to guess the next item of the sequence:
""",
            PlayExample(printer=printer,
                        sequences=['rec(2, 3, I1 * I2 - 1)'], commands=['q.show()', 'q.guess(100)']),
            """\
If the guess is correct, the item is added to the list:
""",
            PlayExample(printer=printer,
                        sequences=['rec(2, 3, I1 * I2 - 1)'], commands=['q.show()', 'q.guess(965)']),
            """\
If you guess 3 items you win the game:
""",
            PlayExample(printer=printer,
                        sequences=['rec(2, 3, I1 * I2 - 1)'], num_items=3, commands=['q.show()', 'q.guess(14)', 'q.guess(69)', 'q.guess(965)']),
            """\
You can ask for new items:
""",
            PlayExample(printer=printer,
                        sequences=['rec(2, 3, I1 * I2 - 1)'], num_items=3, commands=['q.new_item()', 'q.new_item()']),
            """\
If the current game is too difficult for you, the 'new_game' command will start a new one:
""",
            PlayExample(printer=printer,
                        sequences=['(fib01 + catalan) ** m_exp', 'p'], num_items=3, commands=['q.new_game()']),
    ])
    ### SHELL
    navigator.new_page(
        name="shell",
        elements=[
            """\
The SHELL subcommand opens an interactive python shell to play with sequel sequences:
""",
            Shellxample(printer=printer,
                                 commands=['print_sequence(p * zero_one)']),
    ])
    ### SHOW
    navigator.new_page(
        name="show",
        elements=[
            """\
The SHOW command shows information about sequence EXPRESSIONS, for instance:
""",
            ShowExample(printer=printer,
                        kind='expression', source='p * zero_one'),
            ShowExample(printer=printer,
                        kind='expression', source='rec(0, 1, 1 - I1 ** 2 + I2 ** 2)'),
            """\
The SHOW command can also generate random sequences:
""",
            ShowExample(printer=printer,
                        kind='random', source='rec(0, 0, I1 ** 2 - 2 * I2 + 1)'),
            ShowExample(printer=printer,
                        kind='random', source='product(lucas)'),
        ],
    )

    ### SEARCH
    navigator.new_page(
        name="search",
        elements=[
            """\
The search subcommand tries to find a sequence matching the given integer values. An arbitrary number of values can be provided, neverheless some search algorithms will not work if too few known values are provided.

Sequel tries first to search for CORE-SEQUENCES:
""",
            SearchExample(printer=printer,
                          kind="items", source=[2, 3, 5, 7],
                          sequences=[compile_sequence('p'), compile_sequence('m_exp')]),
            """\
If no known sequence matches the given values, sequel applies some ALGORITHMS to detect a matching sequence. It can so find generic SEQUENCES. For instance:
""",
            SearchExample(printer=printer,
                          kind="items", source=[10, 15, 25, 35, 71, 97, 101, 191],
                          sequences=[compile_sequence('-3 * p + 8 * m_exp')]),
            SearchExample(printer=printer,
                          kind="items", source=[3, 6, 9, 15, 24],
                          sequences=[compile_sequence('3 * Fib(first=1, second=2)')]),
            SearchExample(printer=printer,
                          kind="items", source=[1, 36, 316, 2556, 20476, 163836],
                          sequences=[compile_sequence('-4 + 5 * Geometric(base=8)')]),
            SearchExample(printer=printer,
                          kind="items", source=[2, 101, 3, 107, 5, 149, 7, 443],
                          sequences=[compile_sequence('roundrobin(p, 100 + Geometric(base=7))'),
                                     compile_sequence('roundrobin(m_exp, 100 + Geometric(base=7))')]),
            """\
Search accepts patterns instead of integer values. For instance, ANY matches with any value:
""",
            SearchExample(printer=printer,
                          kind="items", source=[2, 3, ANY, 7, 11],
                          sequences=[compile_sequence('p')]),
            """\
A range of suitable values can be passed as 'first..last': any integer value with first <= value <= last is then matched:
""",
            SearchExample(printer=printer,
                          kind="items", source=[2, 3, ANY, 7, '10..20'],
                          sequences=[compile_sequence('p'), compile_sequence('m_exp')]),
            """\
A set of values can be passed as 'v0,v1,v2', for instance:
""",
            SearchExample(printer=printer,
                          kind="items", source=[2, 3, ANY, 7, '10,13'],
                          sequences=[compile_sequence('m_exp')]),
            """\
Notice that using patterns can inhibit some search algorithms.

The SEARCH algorithm can be more efficient in case you know or guess that some non-core sequence can be part of the solution. In this case you can add a sequence DECLARATION.
""",
            """\
The SEARCH command can also be used to test the search algorithm by performing a reverse search of a known sequence.
The input sequence can be an expression or a randomly generated sequence.
For instance:
""",
            SearchExample(printer=printer,
                                 kind='expression', source='p * zero_one', sequences=None),
            SearchExample(printer=printer,
                                 kind='random', source='rec(1, 2, 2 * I2**2 - I1)', sequences=None),
    ])

    ### DECLARATION
    navigator.new_page(
        name="declaration",
        title="Sequence declaration",
        parent="SEARCH",
        elements=[
            """\
Sequel has a catalog of known sequences; this catalog can be extended to include custom sequences.
Notice that declaring new sequences can enhance the search algorithm: indeed many search algorithm are based on the catalog of known sequences.
For instance consider the items 5 10 27 54 135 211 421 790 1959 5703; the SEARCH algorithm can find the sequence
that has been used to generate these values, but it is very slow.
If you have reasons to guess that the p ** 2 sequence is probably part of the solution, the algorithm can be considerably faster.
Anyway, be aware that adding too many sequence declaration can slow down some catalog-based search algorithms.

The sequel catalog of known sequences can be extended with custom declarations in the following three ways:
 * through the `--load plugin.py` global command line option
 * through the `--declare ...` global command line option
 * through the `--declarations-file ...` global command line option

""",
           Title('--load plugin.py', level=1),
           """\
A sequel plugin is a generic python source file; it can be used to declare new sequences. For instance,
consider the file `myplugin.py` with the following content:
""",
           Quotation("""\
from sequel.sequence import *

seq = p ** 2
seq.register('p_squared')

for k in range(4, 8):
    seq = rec(*[1 for _ in range(k)], sum(rec[i] * rec[k-i] for i in range(1, 1 + k//2)) / rec[k])
    seq.register(f'somos_{k}')
"""),
           """\
This loads five new sequences:
  * p_squared
  * somos_4
  * somos_5
  * somos_6
  * somos_7

""",
           Title('--declare [name:=]<sequence>', level=1),
           """\
The --declare ... argument allows to add new sequences to the catalog; for instance:
""",
            SearchExample(printer=printer,
                          kind="items", source=[5, 10, 27, 54, 135, 211, 421, 790, 1959, 5703],
                          sequences=['catalan + p ** 2'],
                          declarations=[parse_declaration('p ** 2')]),
            """\
It is possible to give a name to the declared sequence, for instance:
""",
            SearchExample(printer=printer,
                          kind="items", source=[5, 10, 27, 54, 135, 211, 421, 790, 1959, 5703],
                          sequences=['catalan + p2'],
                          declarations=[parse_declaration('p2:=p ** 2')]),
            """\
It is possible to declare more than one sequence:
""",
            SearchExample(printer=printer,
                          kind="items", source=[3, 7, 22, 47, 122, 194, 402, 759, 1898, 5614],
                          sequences=['c + p2'],
                          declarations=[parse_declaration('p2:=p ** 2'), parse_declaration('c:=catalan - m_exp')]),
           Title('--declarations-file decl.txt', level=1),
            """\
Sequence declarations can be collected in files; for instance, suppose the file 'catalog.txt' contains the two declarations 'p2:=p ** 2' and 'c:=catalan - m_exp':
""",
            SearchExample(printer=printer,
                          kind="items", source=[3, 7, 22, 47, 122, 194, 402, 759, 1898, 5614],
                          sequences=['c + p2'],
                          declarations=[DummyCatalogDeclaration('catalog.txt', ['p2:=p ** 2', 'c:=catalan - m_exp'])]),
            """\
In the following example, 'somos.txt' contains a const declaration 'N::5' and a sequence declaration 'somos_5:=rec(*[1 for i in range(N)], sum(rec[i]*rec[N-i] for i in range(1, 1+N//2))/rec[N])':
""",
            ShowExample(printer=printer,
                          kind="items", source='somos_5',
                          #sequences=['somos_5'],
                          declarations=[DummyCatalogDeclaration('somos.txt', [
                              'N::5', 'somos_5:=rec(*[1 for i in range(N)], sum(rec[i]*rec[N-i] for i in range(1, 1+N//2))/rec[N])'
                          ])]),
        ]
    )
    ### ALGORITHMS
    navigator.new_page(
        name="algorithms",
        elements=[
            """\
Sequel implements many algorithms to discover which sequences generate the given values.

The first algorithm tries to find a core sequence matching the result: for instance when searching "2 3 5 7 11" the
'p' sequence is immediately found:
""",
            SearchExample(printer=printer,
                          kind="items", source=[2, 3, 5, 7, 11],
                          sequences=[compile_sequence('p')]),
            """\
The next algorithm tries to see if the sequence is a const sequence:
""",
            SearchExample(printer=printer,
                          kind="items", source=[4, 4, 4, 4, 4, 4],
                          sequences=[compile_sequence('4')]),
            """\
The next algorithm tries to see if the sequence is an Arithmetic sequence:
""",
            SearchExample(printer=printer,
                          kind="items", source=[2, 9, 16, 23, 30, 37],
                          sequences=[compile_sequence('Arithmetic(2, 7)')]),
            """\
The next algorithm tries to see if the sequence is a Geometric sequence:
""",
            SearchExample(printer=printer,
                          kind="items", source=[1, 7, 49, 343, 2401, 16807],
                          sequences=[compile_sequence('Geometric(7)')]),
            """\
The next algorithm tries to see if the sequence is a Power sequence (Power(n) := i ** n):
""",
            SearchExample(printer=printer,
                          kind="items", source=[0, 1, 32, 243, 1024, 3125],
                          sequences=[compile_sequence('Power(5)')]),
            """\
The next algorithm tries to see if the sequence is a Fibonacci-like sequence (Fib(first, second, scale) := scale * Fib[n-1] + Fib[n-2], Fib[0] := first, Fib[1] := second):
""",
            SearchExample(printer=printer,
                          kind="items", source=[5, -1, 1, 3, 13, 55, 233, 987],
                          sequences=[compile_sequence('Fib(5, -1, 4)')]),
            """\
The next algorithm tries to see if the sequence is a Tribonacci sequence:
""",
            SearchExample(printer=printer,
                          kind="items", source=[5, 6, -3, 8, 11, 16, 35],
                          sequences=[compile_sequence('Trib(5, 6, -3)')]),
            """\
The next algorithm tries to see if the sequence is a polynomial:
""",
            SearchExample(printer=printer,
                          kind="items", source=[5, 11, 45, 113, 197, 255, 221],
                          sequences=[compile_sequence('5 + 7 * i**3 - i**4')]),
            """\
The next algorithm tries to see if the sequence is a Repunit sequence:
""",
            SearchExample(printer=printer,
                          kind="items", source=[6, 9, 18, 45, 126, 369, 1098, 3285],
                          sequences=[compile_sequence('5 + Repunit(3)')]),
            """\
The next algorithm tries to see if the sequence is a RECURSIVE-SEQUENCE:
""",
            SearchExample(printer=printer,
                          kind="items", source=[0, 1, 0, 2, -3, -4, -6, -19, -324, -104614],
                          sequences=[compile_sequence('rec(0, 1, 1 - I1 ** 2 + I2 ** 2)')]),
            """\
The next algorithm tries to see if the sequence is a linear combination of known sequences:
""",
            SearchExample(printer=printer,
                          kind="items", source=[1, -2, -1, 14, 59, 243, 867, 2910],
                          sequences=[compile_sequence('7 * catalan - 3 * m_exp')]),
            """\
The following algorithms try to invert some kind of binary operator. These algorithms recursively call the search algorithms for a subsequence,
so they can be considerably slow.

The next algorithm tries to find a sequence S and a power C so that S ** C matches the given items:
""",
            SearchExample(printer=printer,
                          kind="items", source=[16, 16, 25, 64, 289, 2025, 18225],
                          sequences=[compile_sequence('(3 + catalan) ** 2')]),
            """\
In this case, the algorithm finds that the sequence items '16 16 25 64 289 2025 18225' are the square of the items '4 4 5 8 17 45 135'. It then tries to search a sequence
S matching the items '4 4 5 8 17 45 135', and the solution will be S ** 2. The sequence S is found as '3 + catalan' with one of the previous algorithms.
""",
            """\
The next algorithm tries to find two sequences L and R so that L + R, L - R, L * R, L / R or L ** r matches the given items:
""",
            SearchExample(printer=printer,
                          kind="items", source=[5, 6, 11, 16, 28, 41, 58, 94],
                          sequences=[compile_sequence('3 * fib11 + m_exp')]),
            SearchExample(printer=printer,
                          kind="items", source=[1, 0, 1, 2, 2, 7, 20, 32, 41],
                          sequences=[compile_sequence('3 * fib11 - m_exp')]),
            SearchExample(printer=printer,
                          kind="items", source=[8, 12, 25, 42, 88, 143, 272, 456],
                          sequences=[compile_sequence('(3 + fib11) * p')]),
            """\
The next algorithms try to find sequences such as 'S1 | S2', 'summation(S)', 'product(S)', 'integral(S)', 'derivative(S)', 'roundrobin(S1, S2)'.
""",
        ],
        parent="search",
    )

    return navigator


