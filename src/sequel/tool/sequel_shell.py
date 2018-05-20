"""
Sequel shell
"""

import collections
import json
import shlex

from io import StringIO

from shells_kitchen import (
    Interpreter, argument, command, group, topic,
    filter_completion,
    QUIT, IGNORE, HISTORY,
)

from .. import VERSION
from ..config import (
    default_config,
    get_rl_history_filename,
    get_rl_init_filename,
    get_config,
    get_config_key,
    set_config,
    update_config,
    write_config,
    reset_config,
    get_config_items,
    edit_config,
)
from ..item import make_item
from ..items import make_items
from ..search import (
    create_manager,
    StopAtFirst,
    StopAtLast,
    # StopAtNum,
    StopBelowComplexity,
)
from ..sequence import compile_sequence, Sequence
from ..profiler import Profiler
from ..utils import assert_sequence_matches

from .display import Printer

__all__ = [
    'main',
]


# def type_stop_at_num(string):
#     return StopAtNum(int(string))


def type_stop_below_complexity(string):
    return StopBelowComplexity(int(string))


class declist(object):
    def __init__(self, decorators):
        self.decorators = decorators

    def __call__(self, function):
        for decorator in self.decorators:
            function = decorator(function)
        return function


def iter_selected_sequences(found_sequences, sort=False, limit=None):
    if sort:
        found_sequences = sorted(found_sequences, key=lambda x: x.complexity())
    if limit is None:
        yield from found_sequences
    else:
        for sequence, _ in zip(found_sequences, range(limit)):
            yield sequence
            

class SequelShell(Interpreter):
    __example_line_prefix__ = "  "
    __simplify_argument__ = argument('-s', '--simplify', action='store_true', default=False, help='simplify expressions')
    __profile_argument__ = argument('-p', '--profile', action='store_true', default=False, help='show profiling stats')
    __sort_argument__ = argument('-t', '--sort', action='store_true', default=False, help='sort sequences')
    __base_argument__ = argument('-b', '--base', type=int, default=None, help='output base')
    __limit_argument__ = argument('-l', '--limit', type=int, metavar='L', default=None, help='max number of displayed results')
    __num_items_argument__ = argument('-n', '--num-items', type=int, metavar='N', default=None, help='number of displayed items')
    __search_arguments__ = declist([
        __profile_argument__,
        __sort_argument__,
        __base_argument__,
        __num_items_argument__,
        __limit_argument__,
        argument('-f', '--first', dest='handler', action="store_const", const=StopAtFirst(), default=None,
                 mutually_exclusive_group='stop', help="stop search at first matches"),
        argument('-a', '--all', dest='handler', action="store_const", const=StopAtLast(), default=None,
                 mutually_exclusive_group='stop', help="search all sequences"),
        # argument('-l', '--limit', dest='handler', metavar='L', type=type_stop_at_num, default=None,
        #          mutually_exclusive_group='stop', help="search at most L sequences"),
        argument('-c', '--complexity', dest='handler', metavar="C", type=type_stop_below_complexity, default=None,
                 mutually_exclusive_group='stop', help="stop below complexity C"),
    ])

    def __init__(self, printer=None):
        if printer is None:
            printer = Printer()
        config = get_config()
        colored = config['display']['colored']
        self.line_prefix = "    "
        super().__init__(
            color=colored,
            history_filename=get_rl_history_filename(),
            init_filename=get_rl_init_filename(),
            default=IGNORE,
            content={
                'quit': QUIT,
                'history': HISTORY,
            },
        )
        self.banner = self.__class__._show_banner
        self.doc = self.__class__._show_documentation
        self.prompt = self.colored('SEQUEL> ', style='bold')
        self.printer = printer

        config = get_config()
        def _yield_keys(prefix, dct):
            for key, val in dct.items():
                fq_key = prefix + key
                if isinstance(val, collections.Mapping):
                    yield from _yield_keys(fq_key + ".", val)
                else:
                    yield fq_key
        self._config_keys = list(_yield_keys("", config))
        self._core_sequences = [str(sequence) for sequence in Sequence.get_registry().values()]

    ### config:
    _config_group = group(name="config", default="show", doc="""\
Show/write/reset sequel config""")

    def get_banner_text(self):
        return "Sequel " + self.colored("v{version}".format(version=VERSION), style="bold") + " - integer sequence finder\n"

    def _show_banner(self):
        self.output(self.get_banner_text())

    def _make_link(self, text):
        return self.colored(text, "blue", style="underline")

    def _item_list(self, item, description):
        self.output(''.join([
            " ○  ",
            self.colored(item, style="bold"),
            ": ",
            description]))

    def _title(self, text):
        self.output("")
        self.output(self.colored(text, style="reverse"))
        self.output("")

    def _show_documentation(self):
        self._show_banner()
        self.output("""\
Sequel is a tool to search integer sequences.

The main sequel subcommands are:
 * {c_search}: search a sequence matching the given values
 * {c_compile}: compile a sequence expression and show its first values
 * {c_doc}: print documentation about core sequences
 * {c_help}: show help about commands

Sequel can be used as a command shell or as a command line tool; see
{help_usage} for information.
""".format(
    c_search=self._make_link("search"),
    c_compile=self._make_link("compile"),
    c_doc=self._make_link("doc"),
    c_help=self._make_link("help"),
    help_usage=self._make_link("help usage")))

    @topic(name='usage')
    def _topic_usage(self):
        self.output("""\
The sequel program can be used as a command shell or as a CLI (command line
interface) tool. In the first case the program is run without arguments; an
interactive shell accepting sequel commands is open. In the second case a single
command is passed as argument.""")
        self._title("Interactive shell")
        self.output(self._search_example(
            items=[2, 3, 5, 7],
            sequences=[compile_sequence('p'), compile_sequence('m_exp')],
            shell=True,
        ))
        self._title("Command line interface")
        self.output(self._search_example(
            items=[2, 3, 5, 7],
            sequences=[compile_sequence('p'), compile_sequence('m_exp')],
            shell=False,
        ))

    @topic(name='core')
    def _topic_core(self):
        self.output("""\
Sequel known many core sequences. The {doc} command shows information about the core
sequences:
""".format(doc=self._make_link("doc")))
        self.output(self._doc_example(sources=None, max_lines=7))
        self.output("""
Sequel known also sequence families (or parametric sequences); for instance the
Geometric sequences depend on the sequence 'Geometric(8)' is the geometric sequence
with base 8:
""")
        self.output(self._doc_example(sources=['Geometric(8)']))
        self.output("""
The most common family members are registered as core sequences; for instance, the
geometric sequence with base 3 is the core sequence 'power_of_3':
""")
        self.output(self._doc_example(sources=['Geometric(3)']))
        self.output("\nOther sequence families are:\n")
        self._item_list("Geometric(base)", "the geometric sequences 'base ** i'")
        self._item_list("Arithmetic(start, step)", "the arithmetic sequences 'start + i * step'")
        self._item_list("Polygolan(sides)", "the polygonal numbers with 'sides' sides")
        self._item_list("Power(power)", "the power sequences 'i ** power'")
        self._item_list("Fib(first, second)", "the generalized Fibonacci sequences")
        self.output("""
Sequel has algorithms to find matches for all these sequences.

Other sequences can be created; see {help_expressions}.""".format(
        help_expressions=self._make_link("help expressions")))

    @topic(name='expressions')
    def _topic_expressions(self):
        self.output("""\
Core sequences can be combined to create new sequence expressions; the
{c_compile} command can be used to compile a sequence expression and to
show its first values. For instance:
""".format(
            c_compile=self._make_link("compile"),
        ))
        self.output(self._compile_example(
            sources=['p * n']
        ))
        self.output("\nThe arithmetic operators are available:\n")
        self._item_list("+", "addition, for instance 'p + n'")
        self._item_list("-", "subtraction, for instance 'p - n'")
        self._item_list("*", "multiplication, for instance 'p * n'")
        self._item_list("/", "division, for instance 'p / n'")
        self._item_list("%", "modulo, for instance 'p % n'")
        self._item_list("**", "power, for instance 'p ** n'")
        self.output("""
The {o} operator can be used to compose sequences; for instance, {p_o_zero_one} is
the sequence 'p' computed on the values of 'zero_one':
""".format(
        o=self.colored("|", style="bold"),
        p_o_zero_one=self.colored("p | zero_one", style="bold")))
        self.output(self._compile_example(
            sources=['p', 'zero_one', 'p | zero_one']
        ))
        self.output("""
Some functions can be used to create new sequences; for instance:
""")
        self._item_list("derivative(sequence)", "the derivative of the 'sequence'")
        self._item_list("integral(sequence, start)", "the integral of the 'sequence'")
        self._item_list("summation(sequence)", "the cumulative sum of the 'sequence'")
        self._item_list("product(sequence)", "the cumulative product of the 'sequence'")
        self._item_list("roundrobin(s0, s1, ...)", "the values 's0[0], s1[0], ... s0[1], ...'")

    @argument('keys', nargs='*', metavar='K', help="key")
    @_config_group.command(name="show")
    def _config_show_command(self, keys):
        config = get_config()
        for key, value in sorted(get_config_items(config, keys=keys), key=lambda x: x[0]):
            self.output("{} = {}".format(
                key,
                self.colored(repr(value), style="bold")))

    @_config_show_command.document
    def _config_show_doc(self):
        self.output("Show the entire configuration file or selected keys")

    @argument('-o', '--output-config-filename', metavar='F', default=None, help="output config filename")
    @argument('-r', '--reset', action='store_true', default=False, help="reset config")
    @_config_group.command(name="write")
    def _config_write_command(self, output_config_filename, reset):
        if reset:
            config = default_config()
        else:
            config = get_config()
        write_config(config, output_config_filename)
        set_config(config)
        self.printer = Printer()

    @_config_write_command.document
    def _config_write_doc(self):
        self.output("Write the configuration file")

    @argument('-o', '--output-config-filename', metavar='F', default=None, help="output config filename")
    @argument('-r', '--reset', action='store_true', default=False, help="reset config")
    @_config_group.command(name="edit")
    def _config_edit_command(self, output_config_filename, reset):
        if reset:
            config = default_config()
        else:
            config = get_config()
        config = edit_config(config)
        write_config(config, output_config_filename)
        set_config(config)
        self.printer = Printer()

    @_config_edit_command.document
    def _config_edit_doc(self):
        self.output("Edit the configuration file")

    @_config_group.command(name="reset")
    def _config_reset_command(self):
        config = reset_config()
        set_config(config)
        self.printer = Printer()

    @_config_reset_command.document
    def _config_reset_doc(self):
        self.output("Reset the configuration file")

    @argument('value', metavar='V', help="value")
    @argument('key', metavar='K', help="key")
    @_config_group.command(name="update")
    def _config_update_command(self, key, value):
        config = get_config()
        value = eval(value)
        update_config(config, key, value)
        set_config(config)
        self.printer = Printer()

    @_config_show_command.completer
    @_config_update_command.completer
    def _config_update_completer(self, text, line, begidx, endidx):
        return filter_completion(text, self._config_keys)

    ### search:
    @argument('items', type=make_item, nargs='+', help="sequence items")
    @__search_arguments__
    @command(name='search')
    def _search_command(self, items, handler, profile, base, sort, limit, num_items):
        """Search a sequence matching the given items"""
        printer = self.printer
        if profile:
            profiler = Profiler()
        else:
            profiler = None
        config = get_config()
        size = len(items)
        manager = create_manager(size, config=config)
        found_sequences = manager.search(items, handler=handler, profiler=profiler)
        sequences = iter_selected_sequences(found_sequences, sort=sort, limit=limit)
        with printer.overwrite(base=base, num_items=num_items):
            printer.print_sequences(sequences, num_known=len(items))
            if profile:
                printer.print_stats(profiler)

    @_search_command.document
    def _search_help(self):
        self.output("Search a sequence matching the given values; for instance:\n")
        text = self._search_example(
            items=[2, 3, 5, 7],
            sequences=[compile_sequence('p'), compile_sequence('m_exp')])
        self.output(text)
        self.output("""
Search applies many algorithms to find a matching sequence; see
{help_search_algorithms} for more details.

Search command accepts patterns; see {help_search_patterns}.
""".format(
            help_search_patterns=self._make_link("help search patterns"),
            help_search_algorithms=self._make_link("help search algorithms"),
            ))

    @_search_command.topic(name="algorithms")
    def _search_algorithms(self):
        self.output("""\
Search command applies many different algorithms to search a matching sequence.
It first tries to find a matching core sequence; if none can be found, a more
complex sequence is searched.

For instance:\n""")
        self.output(self._search_example(
            items=[10, 15, 25, 35, 71, 97, 101, 191],
            sequences=[compile_sequence('-3 * p + 8 * m_exp')],
            end=False))
        self.output(self._search_example(
            items=[3, 6, 9, 15, 24],
            sequences=[compile_sequence('3 * Fib(first=1, second=2)')],
            end=False))
        self.output(self._search_example(
            items=[1, 36, 316, 2556, 20476, 163836],
            sequences=[compile_sequence('-4 + 5 * Geometric(base=8)')],
            end=False))
        self.output(self._search_example(
            items=[2, 101, 3, 107, 5, 149, 7, 443],
            sequences=[compile_sequence('roundrobin(p, 100 + Geometric(base=7))'),
                       compile_sequence('roundrobin(m_exp, 100 + Geometric(base=7))')],
            end=True))

    @_search_command.topic(name="patterns")
    def _search_patterns(self):
        self.output("""\
Search values can be patterns. For instance:
 * {c_any} means any integer value
 * {c_lower_10} means any integer value not lower than 10
 * {c_upper_10} means any integer value not greater than 10
 * {c_interval_3_10} means any integer value int the closed interval [3, 10]

For instance:
""".format(
            c_any=self.colored("..", style="bold"),
            c_lower_10=self.colored("..10", style="bold"),
            c_upper_10=self.colored("10..", style="bold"),
            c_interval_3_10=self.colored("3..10", style="bold"),
        ))
        self.output(self._search_example(
            items=[2, 3, 5, '..', 13],
            sequences=[compile_sequence('m_exp')],
            end=False))
        self.output(self._search_example(
            items=[2, 3, 5, 7, '..12'],
            sequences=[compile_sequence('p')],
            end=False))
        self.output(self._search_example(
            items=[2, 3, 5, 7, '10..20'],
            sequences=[compile_sequence('p'), compile_sequence('m_exp')],
            end=True))
        self.output("""
Notice that when using patterns some of the available search algorithms could
be disabled.""")

    ### doc:
    @__simplify_argument__
    @argument('sources', type=str, nargs='*', help="sequence sources")
    @argument('--full', action='store_true', default=False, help="show full documentation")
    @__base_argument__
    @__num_items_argument__
    @command(name='doc')
    def _doc_command(self, sources, simplify, num_items, base, full):
        if not sources:
            sources = None
        printer = self.printer
        with printer.overwrite(num_items=num_items, base=base):
            printer.print_doc(sources=sources, simplify=simplify, full=full)

    @_doc_command.completer
    def _doc_completer(self, text, line, begidx, endidx):
        return filter_completion(text, self._core_sequences)

    @_doc_command.document
    def _doc_help(self):
        self.output("Show documentation about sequences; for instance:\n")
        text = self._doc_example(sources=['m_exp', 'p'])
        self.output(text)
        self.output("Without arguments all core sequences are shown:\n")
        text = self._doc_example(sources=None, max_lines=7)
        self.output(text)

    ### compile:
    @__simplify_argument__
    @argument('-t', '--tree', action='store_true', default=False, help="show sequence tree")
    @__base_argument__
    @__num_items_argument__
    @argument('sources', type=str, nargs='+', help="sequence sources")
    @command(name='compile')
    def _compile_command(self, sources, simplify, tree, base, num_items):
        printer = self.printer
        with printer.overwrite(base=base, num_items=num_items):
            if tree:
                print_function = printer.print_tree
            else:
                print_function = printer.print_sequence
            for source in sources:
                sequence = compile_sequence(source, simplify=simplify)
                print_function(sequence)

    @_compile_command.document
    def _compile_help(self):
        self.output("Compile a sequence expression and shows the first items; for instance:\n")
        text = self._compile_example(
            sources=['p * zero_one'])
        self.output(text)

    ### test:
    @__simplify_argument__
    @__search_arguments__
    @argument('sources', type=str, nargs='+', help="sequence sources")
    @command(name='test')
    def _test_command(self, sources, simplify, handler, profile, base, sort, limit, num_items):
        printer = self.printer
        config = get_config()
        with printer.overwrite(base=base, num_items=num_items):
            size = printer.num_items
            manager = create_manager(size, config=config)
            if profile:
                profiler = Profiler()
            else:
                profiler = None
            for source in sources:
                sequence = compile_sequence(source, simplify=simplify)
                items = sequence.get_values(printer.num_items)
                found_sequences = manager.search(items, handler=handler, profiler=profiler)
                sequences = iter_selected_sequences(found_sequences, sort=sort, limit=limit)
                printer.print_test(source, sequence, items, sequences)
            if profile:
                printer.print_stats(profiler)
            
    @_test_command.document
    def _test_help(self):
        self.output("Compile a sequence expression and searches its first items; for instance:\n")
        text = self._test_example( source='p * zero_one', sequences=None)
        self.output(text)

    ### utils:
    def _text_lines(self, text, max_lines=None):
        lines = text.split('\n')
        if max_lines is not None:
            if len(lines) > max_lines:
                del lines[max_lines:]
                lines.append("...")
        return lines
    
    def _make_text(self, lines):
        return '\n'.join(self.line_prefix + line for line in lines)

    def _add_end_line(self, lines, shell):
        if shell:
            lines.append(self.prompt)
        else:
            lines.append("$")

    def _add_begin_line(self, lines, cmd, shell):
        if shell:
            lines.append("$ sequel ")
            lines.append(self.get_banner_text())
            lines.append(self.prompt + cmd)
        else:
            lines.append("$ sequel " + cmd)

    def _search_example(self, items, sequences, max_lines=None, shell=False, end=True):
        printer = self.printer
        orig_items = tuple(items)
        items = make_items(items)
        sequences = tuple(sequences)
        for sequence in sequences:
            assert_sequence_matches(sequence, items)
        ios = StringIO()
        with printer.set_file(ios):
            printer.print_sequences(sequences, num_known=len(items))
        lines = []
        self._add_begin_line(lines, "search " + " ".join(str(item) for item in orig_items), shell=shell)
        lines.extend(self._text_lines(ios.getvalue().rstrip(), max_lines=max_lines))
        if end:
            self._add_end_line(lines, shell=shell)
        return self._make_text(lines)

    def _compile_example(self, sources, simplify=False, max_lines=None, shell=False, end=True):
        printer = self.printer
        ios = StringIO()
        with printer.set_file(ios):
            for source in sources:
                sequence = compile_sequence(source, simplify=simplify)
                printer.print_sequence(sequence)
        args = []
        if simplify:
            args.append("--simplify")
        if sources:
            args.extend(sources)
        lines = []
        self._add_begin_line(lines, "compile " + " ".join(shlex.quote(arg) for arg in args), shell=shell)
        lines.extend(self._text_lines(ios.getvalue().rstrip(), max_lines=max_lines))
        if end:
            self._add_end_line(lines, shell=shell)
        return self._make_text(lines)

    def _test_example(self, source, sequences, simplify=False, max_lines=None, shell=False, end=True):
        printer = self.printer
        ios = StringIO()
        with printer.set_file(ios):
            sequence = compile_sequence(source, simplify=simplify)
            items = sequence.get_values(printer.num_items)
            sequences = sequences
            if sequences is None:
                sequences = [sequence]
            printer.print_test(source, sequence, items, sequences)
        args = []
        if simplify:
            args.append("--simplify")
        args.extend(shlex.quote(source))
        lines = []
        self._add_begin_line(lines, "test " + " ".join(args), shell=shell)
        lines.extend(self._text_lines(ios.getvalue().rstrip(), max_lines=max_lines))
        if end:
            self._add_end_line(lines, shell=shell)
        return self._make_text(lines)

    def _doc_example(self, sources, simplify=False, max_lines=None, shell=False, end=True):
        printer = self.printer
        ios = StringIO()
        with printer.set_file(ios):
            printer.print_doc(sources=sources, simplify=simplify)
        args = []
        if simplify:
            args.append("--simplify")
        if sources:
            args.extend(sources)
        lines = []
        self._add_begin_line(lines, "doc " + " ".join(args), shell=shell)
        lines.extend(self._text_lines(ios.getvalue().rstrip(), max_lines=max_lines))
        if end:
            self._add_end_line(lines, shell=shell)
        return self._make_text(lines)
