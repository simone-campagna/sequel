"""
Help pages
"""

from io import StringIO
import shlex

from .display import Printer
from .page import Navigator, Paragraph
from ..sequence import compile_sequence
from ..items import make_items, ANY
from ..utils import assert_sequence_matches

__all__ = [
    'create_help',
]

# def create_help(help_source_filename=None):
#     if help_source_filename is None:
#         help_source_filename = os.path.join(os.path.dirname(__file__), 'help.json')
#     with open(help_source_filename, "r") as f_in:
#         help_config = json.loads(f_in)
#         pages = collections.OrderedDict()
#         links = {}
#         for page_num, page_config = enumerate(help_config["pages"]):
#             page_name = page_config.get('name', 'page_{}'.format(page_num))
#             page = Page(name=page_name, text=page_config['text'])
#             page_links = page_config.get('links', [])
#             links[page] = page_links
#         for page, link_names in links.items():
#             for link_name in link_names:
#                 if not link_name in pages:
#                     raise ValueError("page {} links missing page {}".format(page.name, link_name))
#                 page.add_link_page(link_name, pages[link_name])
#         home_page_name = help_config.get('home', None)
#         if home_page_name is None and pages:
#             home_page_name = tuple(pages)[0]
#         if home_page_name is None:
#             raise ValueError("no home page")
#         if home_page_name not in pages:
#             raise ValueError("home page {!r} not defined".format(home_page_name))
#         home_page = pages[home_page_name]
#         for page in pages.values():
#             page.set_home(home_page)
#         return home_page

class Example(Paragraph):
    def __init__(self, printer, max_lines=None):
        self.printer = printer
        self.max_lines = max_lines

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


class DocExample(Example):
    def __init__(self, printer, sources, simplify=False, max_lines=None):
        super().__init__(printer, max_lines=max_lines)
        self.sources = sources
        self.simplify = simplify

    def get_text(self):
        ios = StringIO()
        with self.printer.set_file(ios):
            self.printer.print_doc(sources=self.sources, simplify=self.simplify)
        args = []
        if self.simplify:
            args.append("--simplify")
        if self.sources:
            args.extend(self.sources)
        lines = []
        lines.append("$ sequel doc " + " ".join(args))
        lines.extend(self._output_lines(ios.getvalue()))
        return self._format_lines(lines)


class CompileExample(Example):
    def __init__(self, printer, sources, simplify=False, max_lines=None):
        super().__init__(printer, max_lines=max_lines)
        self.sources = sources
        self.simplify = simplify

    def get_text(self):
        ios = StringIO()
        with self.printer.set_file(ios):
            for source in self.sources:
                sequence = compile_sequence(source, simplify=self.simplify)
                self.printer.print_sequence(sequence)
        args = []
        if self.simplify:
            args.append("--simplify")
        if self.sources:
            args.extend(self.sources)
        lines = []
        lines.append("$ sequel compile " + " ".join(shlex.quote(arg) for arg in args))
        lines.extend(self._output_lines(ios.getvalue()))
        return self._format_lines(lines)


class SearchExample(Example):
    def __init__(self, printer, items, sequences, max_lines=None):
        super().__init__(printer, max_lines=max_lines)
        self.orig_items = tuple(items)
        self.items = make_items(items)
        self.sequences = tuple(sequences)
        for sequence in sequences:
            assert_sequence_matches(sequence, self.items)

    def get_text(self):
        ios = StringIO()
        with self.printer.set_file(ios):
            self.printer.print_sequences(self.sequences, num_known=len(self.items))
        lines = []
        lines.append("$ sequel search " + " ".join(str(item) for item in self.orig_items))
        lines.extend(self._output_lines(ios.getvalue()))
        return self._format_lines(lines)


class TestExample(Example):
    def __init__(self, printer, source, sequences, simplify=False, max_lines=None):
        super().__init__(printer, max_lines=max_lines)
        self.source = source
        self.sequences = sequences
        self.simplify = simplify

    def get_text(self):
        ios = StringIO()
        with self.printer.set_file(ios):
            sequence = compile_sequence(self.source, simplify=self.simplify)
            items = sequence.get_values(self.printer.num_items)
            sequences = self.sequences
            if sequences is None:
                sequences = [sequence]
            self.printer.print_test(self.source, sequence, items, sequences)
        args = []
        if self.simplify:
            args.append("--simplify")
        args.extend(shlex.quote(self.source))
        lines = []
        lines.append("$ sequel test " + " ".join(args))
        lines.extend(self._output_lines(ios.getvalue()))
        return self._format_lines(lines)


def create_help():
    printer = Printer()
    wip_text = printer.red("Work in progress")

    navigator = Navigator()
    ### HOME
    navigator.new_page(
        name="introduction",
        elements=[
            """\
Sequel is a command line tool to find integer sequences:
""",
            SearchExample(printer=printer,
                          items=[2, 3, 5, 7, 11],
                          sequences=[compile_sequence('p')]),
            SearchExample(printer=printer,
                          items=[2, 3, 5, 7, 13, 17],
                          sequences=[compile_sequence('m_exp')]),
            """\
The SEARCH subcommand accepts an arbitrary number of integer values and returns a list of matching sequences;
it may also return multiple matches:
""",
            SearchExample(printer=printer,
                          items=[2, 3, 5, 7],
                          sequences=[compile_sequence('p'), compile_sequence('m_exp')]),
            """\
Sequel knows many CORE-SEQUENCES; the DOC subcommand can be used to get information about one or more sequences:
""",
            DocExample(printer=printer,
                       sources=['m_exp', 'p']),
            """\
If no sequence name is specified, the doc subcommand shows all the known sequences:
""",
            DocExample(printer=printer,
                       sources=None, max_lines=(5, 3)),
            """\
The COMPILE subcommand can be used to compile sequence EXPRESSIONS:
""",
            CompileExample(printer=printer,
                           sources=['p * zero_one']),
            """\
The TEST subcommand can be used to test the search algorithm: it gets a sequence definition, compiles it,
and searches its values. It is a shortcut for running a compile subcommand and then a search subcommand.
""",
            TestExample(printer=printer,
                        source='p * zero_one', sequences=None),
        ]
    )

    ### SEQUENCES
    navigator.new_page(
        name="sequences",
        elements=[
            """\
Sequel understands many SEQUENCES. There are many CORE-SEQUENCES; for instance 'p' is the prime numbers sequence [2, 3, 5, 7, ...].

Other sequences can be created using sequence EXPRESSIONS; for instance, 'p + 10' is the sequence of the prime numbers plus ten [12, 13, 15, 17, ...].
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
                       sources=None),
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
Additionally, a generic RECURSIVE-SEQUENCE can be defined.
""",
        ],
    )

    ### RECURSIVE-SEQUENCE_EXPRESSIONS
    navigator.new_page(
        name="recursive sequence",
        parent="expressions",
        elements=[
            """\
Generic recursive sequences can be defined using the "rseq" function: it takes a list of known values and a generating sequence. The generating sequence is a special sequence that, given the last generated items, generates the next one; it can access the last item as _0, the second to last item as _1, and so on. 
For instance, 'rseq(0, 1, _0 + _1)' defines a new sequence starting with 0 and 1, and producing new items as the sum of the last item ('_0') and the second to last item ('_1'); this is clearly the same as the fib01 sequence:
""",
            CompileExample(printer=printer,
                           sources=['rseq(0, 1, _0 + _1)']),
            """\
More complex recursive functions can be created, for instance this is defined as the squared last item minus the second to last item:
""",
            CompileExample(printer=printer,
                           sources=['rseq(0, 1, _0 ** 2 - _1)']),
            """\
When defining the generating sequence, the last ten produced items can be accessed by using the _0, _1, ..., _9 indices. In general, 'rseq[n]' can be used to access the n-th to last generated item.
""",
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
                       sources=None, max_lines=(5, 3)),
            """\
When one or more arguments are passed, the arguments are compiled and the documentation about the resulting sequence is shown:
""",

            DocExample(printer=printer,
                       sources=['m_exp', 'p', 'm_exp * (p - 2)']),
        ],
    )
    ### TEST
    navigator.new_page(
        name="test",
        elements=[wip_text],
    )
    ### COMPILE
    navigator.new_page(
        name="compile",
        elements=[wip_text],
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
                          items=[2, 3, 5, 7],
                          sequences=[compile_sequence('p'), compile_sequence('m_exp')]),
            """\
If no known sequence matches the given values, sequel applies some ALGORITHMS to detect a matching sequence. It can so find generic SEQUENCES. For instance:
""",
            SearchExample(printer=printer,
                          items=[10, 15, 25, 35, 71, 97, 101, 191],
                          sequences=[compile_sequence('-3 * p + 8 * m_exp')]),
            SearchExample(printer=printer,
                          items=[3, 6, 9, 15, 24],
                          sequences=[compile_sequence('3 * Fib(first=1, second=2)')]),
            SearchExample(printer=printer,
                          items=[1, 36, 316, 2556, 20476, 163836],
                          sequences=[compile_sequence('-4 + 5 * Geometric(base=8)')]),
            SearchExample(printer=printer,
                          items=[2, 101, 3, 107, 5, 149, 7, 443],
                          sequences=[compile_sequence('roundrobin(p, 100 + Geometric(base=7))'),
                                     compile_sequence('roundrobin(m_exp, 100 + Geometric(base=7))')]),
            """\
Search accepts patterns instead of integer values. For instance, ANY matches with any value:
""",
            SearchExample(printer=printer,
                          items=[2, 3, ANY, 7, 11],
                          sequences=[compile_sequence('p')]),
            """\
A range of suitable values can be passed as 'first..last': any integer value with first <= value <= last is then matched:
""",
            SearchExample(printer=printer,
                          items=[2, 3, ANY, 7, '10..20'],
                          sequences=[compile_sequence('p'), compile_sequence('m_exp')]),
            """\
A set of values can be passed as 'v0,v1,v2', for instance:
""",
            SearchExample(printer=printer,
                          items=[2, 3, ANY, 7, '10,13'],
                          sequences=[compile_sequence('m_exp')]),
            """\
Notice that using patterns can inhibit some search algorithms.
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
""",
        ],
        parent="search",
    )

    return navigator


