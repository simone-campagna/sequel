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
    parse_sequence_declaration,
    sequence_declaration, declared,
    DeclarationType,
)
from .display import Printer, iter_item_types
from .page import Navigator, Element, Paragraph, Quotation, Break
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
    def example_args(self):
        return []

    def _format_lines(self, lines):
        return '\n'.join("  " + line for line in lines)


class SimplifyMixIn(object):
    def __init__(self, *, simplify=None, **kwargs):
        self.simplify = simplify
        super().__init__(**kwargs)

    def example_args(self):
        args = super().example_args()
        if self.simplify:
            args.append("--simplify")
        return args


class DeclarationsMixIn(object):
    def __init__(self, *, declarations=None, **kwargs):
        if declarations is None:
            declarations = ()
        self._declarations = tuple(declarations)
        super().__init__(**kwargs)

    @contextlib.contextmanager
    def declare(self):
        declarations = []
        for declaration in self._declarations:
            if isinstance(declaration, DummyCatalogDeclaration):
                for decl in declaration.sources:
                    declarations.append(sequence_declaration(decl))
            else:
                declarations.append(declaration)
        with declared(*declarations):
            yield

    def example_args(self):
        args = super().example_args()
        for declaration in self._declarations:
            if isinstance(declaration, DummyCatalogDeclaration):
                args.append("--catalog={!r}".format(declaration.filename))
            elif declaration.decl_type is DeclarationType.SEQUENCE:
                sequence_declaration = parse_sequence_declaration(declaration.value)
                if sequence_declaration.name is None:
                    decl = sequence_declaration.source
                else:
                    decl = "{}:={}".format(sequence_declaration.name, sequence_declaration.source)
                args.append("--declare={!r}".format(decl))
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
    def __init__(self, printer, kind, source, simplify=False, max_lines=None):
        super().__init__(printer=printer, simplify=simplify, max_lines=max_lines)
        self.kind = kind
        self.source = source
        self.simplify = simplify

    def example_args(self):
        args = super().example_args()
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
        args = self.example_args()
        lines = []
        lines.append("$ sequel doc " + " ".join(args))
        lines.extend(self._output_lines(ios.getvalue()))
        return self._format_lines(lines)


class CompileExample(SimplifyMixIn, RaisingMixIn, Example):
    def __init__(self, printer, sources, simplify=False, expected_exception=False, max_lines=None, num_items=None):
        super().__init__(printer=printer, simplify=simplify, expected_exception=expected_exception, max_lines=max_lines)
        self.sources = sources
        self.simplify = simplify
        self.num_items = num_items

    def get_text(self):
        ios = StringIO()
        with self.printer.set_file(ios):
            with self.raising(ios):
                for source in self.sources:
                    sequence = compile_sequence(source, simplify=self.simplify)
                    self.printer.print_sequence(sequence, num_items=self.num_items)
        args = self.example_args()
        if self.sources:
            args.extend(self.sources)
        lines = []
        lines.append("$ sequel compile " + " ".join(shlex.quote(arg) for arg in args))
        lines.extend(self._output_lines(ios.getvalue()))
        return self._format_lines(lines)


class SearchExample(DeclarationsMixIn, Example):
    def __init__(self, *, printer, kind, source, sequences, max_lines=None, declarations=None):
        super().__init__(printer=printer, declarations=declarations, max_lines=max_lines)
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

    def example_args(self):
        args = super().example_args()
        if self.kind == 'items':
            args.append('-i')
            args.extend(str(i) for i in self.orig_items)
        elif self.kind == 'expression':
            args.append('-e')
            args.extend(repr(self.source))
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
        args = self.example_args()
        lines.append("$ sequel search " + " ".join(args))
        lines.extend(self._output_lines(ios.getvalue()))
        return self._format_lines(lines)


class Shellxample(Example):
    def __init__(self, printer, commands, max_lines=None):
        super().__init__(printer=printer, max_lines=max_lines)
        self.commands = list(commands)

    def get_text(self):
        ios = StringIO()
        shell = SequelShell(printer=self.printer)
        with self.printer.set_file(ios):
            with redirect(ios, ios):
                shell.run_commands(self.commands, echo=True)
        args = self.example_args()
        lines = []
        lines.append("$ sequel shell " + " ".join(args))
        lines.extend(self._output_lines(ios.getvalue()))
        return self._format_lines(lines)


class PlayExample(Example):
    def __init__(self, printer, sequences, commands, num_items=5, max_lines=None, banner=None, max_games=1):
        super().__init__(printer=printer, max_lines=max_lines)
        self.sequences = [Sequence.make_sequence(x) for x in sequences]
        self.commands = list(commands)
        self.num_items = num_items
        self.banner = banner
        self.max_games = max_games

    def example_args(self):
        return super().example_args() + ['--num-items={}'.format(self.num_items)]

    def get_text(self):
        ios = StringIO()
        with self.printer.set_file(ios):
            with redirect(ios, ios):
                quiz_shell = QuizShell(printer=self.printer, sequence_iterator=itertools.cycle(self.sequences),
                                       num_known_items=self.num_items, max_games=self.max_games)
                quiz_shell.run_commands(self.commands, echo=True, banner=self.banner)
        args = self.example_args()
        lines = []
        lines.append("$ sequel play " + " ".join(args))
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
                       kind='expressions', source=['m_exp', 'p']),
            """\
If no sequence name is specified, the doc subcommand shows all the known sequences:
""",
            DocExample(printer=printer,
                       kind='all', source=None, max_lines=(5, 3)),
            """\
The COMPILE subcommand can be used to compile sequence EXPRESSIONS:
""",
            CompileExample(printer=printer,
                           sources=['p * zero_one']),
            """\
The SHELL subcommand opens an interactive python shell to play with sequel sequences:
""",
            Shellxample(printer=printer,
                                 commands=['print_sequence(p * zero_one)']),
            """\
The PLAY subcommand generates an hidden random sequence and let you guess what sequence it is.
""",
            PlayExample(printer=printer,
                                 sequences=['p * zero_one'], commands=['q.guess(p * zero_one)']),
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
            CompileExample(printer=printer,
                           sources=['3']),
            """\
The usual arithmetic operators can be used to obtain new sequences; for instance:
""",
            CompileExample(printer=printer,
                           sources=['3 * p + m_exp - m_primes', 'm_exp % p', 'p ** n']),
            """\
Since sequel only supports integer sequences, the division operator always truncates the result:
""",
            CompileExample(printer=printer,
                           sources=['m_exp // p']),
            """\
Powers are also available: the sequence 'Power(3)' is the sequence i**3':
""",
            CompileExample(printer=printer,
                           sources=['Power(3)', 'Power(7)']),
            """\
Sequences can be composed with the '|' operator. The sequence 'p | n' is the sequence primes 'p' computed on the values of the natural numers sequence 'n':
""",
            CompileExample(printer=printer,
                           sources=['p', 'n', 'p | n', 'p | (2 * n)']),
            """\
The 'roundrobin' function creates a new sequence by taking values from other sequences:
""",
            CompileExample(printer=printer,
                           sources=['roundrobin(p, 0, 7 * n - 10)']),
            """\
Other available functions are 'integral', 'derivative', 'summation', 'product':
""",
            CompileExample(printer=printer,
                           sources=['integral(p)', 'derivative(p)', 'summation(p)', 'product(p)']),
            """\
The 'ifelse' function creates a new function according to a condition. For instance, the following sequence is '1000 + fib01' for the indices where catalan is even, and p for the indices where catalan is odd:
""",
            CompileExample(printer=printer,
                           sources=['ifelse(catalan % 2 == 0, 1000 + fib01, p)']),
            """\
Moreover, some parametric sequences are available. For instance, the geometric, arithmetic sequences:
""",
            CompileExample(printer=printer,
                           sources=['Geometric(base=8)', 'Arithmetic(start=2, step=7)']),
            """\
Fibonacci sequences are also available; 'Fib' is the generic Fibonacci sequence with parametric 'first' and 'second' values. Three specialized sequences are available:
'fib01', 'fib11' and 'lucas':
are defined as 
""",
            CompileExample(printer=printer,
                           sources=['Fib(first=2, second=4)', 'fib01', 'fib11', 'lucas']),
            """\
The polygonal numbers are also available:
""",
            CompileExample(printer=printer,
                           sources=['triangular', 'square', 'pentagonal', 'hexagonal', 'Polygonal(8)']),
            """\
Additionally, a generic RECURSIVE-SEQUENCE can be defined; the following sequence is the recursive definition of the factorial function:
""",
            CompileExample(printer=printer,
                           sources=['rseq(1, I1 * i)']),
        ],
    )

    ### RECURSIVE-SEQUENCE_EXPRESSIONS
    navigator.new_page(
        name="recursive sequence",
        parent="expressions",
        elements=[
            """\
Generic recursive sequences can be defined using the "rseq" function: it takes a list of known values and a generating sequence. The generating sequence is a special sequence that, given the last generated items, produces the next one. The form of a recursive sequence definition is
""",
            Quotation("""\
  rseq(K0, K1, ..., KN, GS)

where:

  K0, K1, ..., KN are the first N known values (N can be 0)
  GS is a generatong sequence
"""),
            """\
The generating sequence is used to produce the items for i >= N; for instance, in 'rseq(4, 8, p)', the generating sequence is 'p', and it is used to produce the items with index 2, 3, ...:
""",
            CompileExample(printer=printer,
                           sources=['rseq(4, 8, 0)']),
            """
The generating sequence can be a generic sequence; nevertheless it may contain references to the recursive sequence itself:
""",
            Quotation("""\
  I0      is the recursive sequence itself
  I1      is equivalent to I0 | i - 1
  I2      is equivalent to I0 | i - 2 (or I1 | i - 1)
  ...
  I9      is equivalent to I0 | i - 9
  rseq[n] is equivalent to I0 | i - n
"""),
            """\
For instance, 'rseq(1, I1 * i)' defines a new sequence starting with 1 and producing new items as the product of the last item ('I1') with the value of the sequence 'i' ([0, 1, 2, 3, ...]). The values are:
""",
            Quotation("""\
  rseq(1, I1 * i):
    [0] ->                                   1  (the initial value)
    [1] -> I1 * i(1) == [0] * 1 == 1 * 1 ==  1
    [2] -> I1 * i(2) == [1] * 2 == 1 * 2 ==  2
    [3] -> I1 * i(3) == [2] * 3 == 2 * 3 ==  6
    [4] -> I1 * i(4) == [3] * 4 == 6 * 4 == 24
    ...

This is the same as the factorial sequence.
"""),
            CompileExample(printer=printer,
                           sources=['rseq(1, I1 * i)']),
            """\
As a second example, consider 'rseq(0, 1, I1 + I2)'; in this case the known items are two (0 and 1) and the next items are generated as the sum of the last two values (I1 and I2):
""",

            Quotation("""\
  rseq(0, 1, I1 + I2):
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
            CompileExample(printer=printer,
                           sources=['rseq(0, 1, I1 + I2)']),
            """\
A recursive sequence definition must contain at least N known elements, where N is the max used index in the generating expression; so, if the generating expression is 'I1 + 3 * I3',
the recursive sequence definition must contain at least 3 values. Anyway, it is accepted to define more than N+1 known values, for instance:
""",
            CompileExample(printer=printer,
                           sources=['rseq(3, 2, 1, 0, I1 + 1)']),
            """\
Another constraint on the generating sequence is obviously that it cannot be used to generate items with index N >= the index of the last generated item.
For instance, 'I0', wich is a reference to the recursive sequence itself, is not a valid generating sequence:
""",
            CompileExample(printer=printer,
                           sources=['rseq(0, I0)'], expected_exception=RecursiveSequenceError),
            """\
In the definition above the item 1 of the recursive sequence is defined as the item 1 of the recursive sequence itself; this is an error.
Anyway, I0 can be used in a generating sequence definition; for instance 'rseq(1, summation(I0) | i - 1)' is defined as follow:
""",
            Quotation("""\
  rseq(1, summation(I0) | i - 1):
    [0] ->                                         1  (the first known item)
    [1] -> summation(I0)[0] == sum(1)              1
    [2] -> summation(I0)[1] == sum(1, 1) ==        2
    [3] -> summation(I0)[2] == sum(1, 1, 2) ==     4
    [4] -> summation(I0)[3] == sum(1, 1, 2, 4) ==  8
    ...
"""),
            CompileExample(printer=printer,
                           sources=['rseq(0, 1, summation(I0) | i - 1)']),
            """\
The following sequence computes the items of the Collatz sequence starting with n=19:
""",
            CompileExample(printer=printer,
                           sources=['rseq(19, ifelse(I1 % 2 == 0, I1 // 2, 3 * I1 + 1))'], num_items=24),
            """\
Be aware that I0, I1, ... are "limited" sequences: they cannot be used outside a rseq(...) definition. Moreover, as stated above, I<N> cannot be used to generate items with index n >= N.
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
                       kind='all', source=['m_exp', 'p', 'catalan']),
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
                        sequences=['rseq(2, 3, I1 * I2 - 1)'], commands=[]),
            """\
The 'q' instance can be used to play the game; run the 'q' command to have an help:
""",
            PlayExample(printer=printer,
                        sequences=['rseq(2, 3, I1 * I2 - 1)'], commands=['q']),
            """\
In order to win the game you have to guess a sequence matching the shown items. 
""",
            PlayExample(printer=printer,
                        sequences=['rseq(2, 3, I1 * I2 - 1)'], commands=['q.show()', 'q.guess(p)', 'x = rseq(2, 3, I1 * I2 - 1)', 'print_sequence(x)', 'q.guess(x)']),
            """\
You can also try to guess the next item of the sequence:
""",
            PlayExample(printer=printer,
                        sequences=['rseq(2, 3, I1 * I2 - 1)'], commands=['q.show()', 'q.guess(100)']),
            """\
If the guess is correct, the item is added to the list:
""",
            PlayExample(printer=printer,
                        sequences=['rseq(2, 3, I1 * I2 - 1)'], commands=['q.show()', 'q.guess(965)']),
            """\
If you guess 3 items you win the game:
""",
            PlayExample(printer=printer,
                        sequences=['rseq(2, 3, I1 * I2 - 1)'], num_items=3, commands=['q.show()', 'q.guess(14)', 'q.guess(69)', 'q.guess(965)']),
            """\
You can ask for new items:
""",
            PlayExample(printer=printer,
                        sequences=['rseq(2, 3, I1 * I2 - 1)'], num_items=3, commands=['q.new_item()', 'q.new_item()']),
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
    ### COMPILE
    navigator.new_page(
        name="compile",
        elements=[
            """\
The COMPILE command compiles a sequence and shows its first items:
For instance:
""",
            CompileExample(printer=printer,
                        sources=['p * zero_one']),
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
                                 kind='random', source='rseq(1, 2, 2 * I2**2 - I1)', sequences=None),
    ])

    ### DECLARATION
    navigator.new_page(
        name="declaration",
        title="Sequence declaration",
        parent="SEARCH",
        elements=[
            """\
Many of the search algorithms are based on the catalog of known sequences.
It is possible to declare new non-core sequences in order to increase the efficiency and velocity of the search algorithm.

For instance consider the items 5 10 27 54 135 211 421 790 1959 5703; the SEARCH algorithm can find the sequence
that has been used to generate these values, but it is very slow.

If you have reasons to guess that the p ** 2 sequence is probably part of the solution, the algorithm can be considerably faster:
""",
            SearchExample(printer=printer,
                          kind="items", source=[5, 10, 27, 54, 135, 211, 421, 790, 1959, 5703],
                          sequences=['catalan + p ** 2'],
                          declarations=[sequence_declaration('p ** 2')]),
            """\
It is possible to give a name to the declared sequence, for instance:
""",
            SearchExample(printer=printer,
                          kind="items", source=[5, 10, 27, 54, 135, 211, 421, 790, 1959, 5703],
                          sequences=['catalan + p2'],
                          declarations=[sequence_declaration('p2:=p ** 2')]),
            """\
It is possible to register more than one sequence:
""",
            SearchExample(printer=printer,
                          kind="items", source=[3, 7, 22, 47, 122, 194, 402, 759, 1898, 5614],
                          sequences=['c + p2'],
                          declarations=[sequence_declaration('p2:=p ** 2'), sequence_declaration('c:=catalan - m_exp')]),
            """\
Sequence declarations can be collected in files; for instance, suppose the file 'catalog.txt' contains the two declarations 'p2:=p ** 2' and 'c:=catalan - m_exp':
""",
            SearchExample(printer=printer,
                          kind="items", source=[3, 7, 22, 47, 122, 194, 402, 759, 1898, 5614],
                          sequences=['c + p2'],
                          declarations=[DummyCatalogDeclaration('catalog.txt', ['p2:=p ** 2', 'c:=catalan - m_exp'])]),
            """\
Be aware that adding too many sequence declaration can slow down some catalog-based search algorithms.
""",
        ]
    )
    ### ALGORITHMS
    navigator.new_page(
        name="algorithms",
        elements=[
            """\
Sequel implements many algorithms to discover which sequences generate the given values.

The first algorithm tries to find a core sequence matching the result: for instance when searching "2 3 5 7 11" the
'p' sequence is immediately found.

Then sequel tries to find an affine trasformation of a core sequence matching the values: for instance "1 4 10 16 28 34" is found as '3 * p - 5'.

Sequel tries then to see if the values match any arithmetic or geometric sequence, or a power sequence such as 'i ** 3', or a fibonacci-like
sequence, or a polynomial sequence such as '2 + i - i**3', or a repunit sequence, or finally a linear combination of known sequences.

If no sequence is found, sequel applies some recursive algorithms: for instance it tries to subtract the core sequence 'p' to the given values, and to find the
sequence 's' matching the resulting values; the sequence 'p + s' is then a solution.

For instance:
""",
            SearchExample(printer=printer,
                          kind="items", source=[4, 3, 20, 0, 77, -52, 238, -285, 736, -1276],
                          sequences=[compile_sequence('rseq(2, 1, I2 - I1 + 3) * p')]),

        ],
        parent="search",
    )

    return navigator


